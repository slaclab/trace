import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

import epics
import numpy as np
import pandas as pd
from scipy.io import savemat
from qtpy.QtCore import (
    Qt,
    QUrl,
    Slot,
    Signal,
    QObject,
    QThread,
    QModelIndex,
    QAbstractTableModel,
)
from qtpy.QtNetwork import QNetworkReply, QNetworkRequest, QNetworkAccessManager
from qtpy.QtWidgets import (
    QLabel,
    QWidget,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from pydm.widgets.archiver_time_plot import (
    TimePlotCurveItem,
    ArchivePlotCurveItem,
    PyDMArchiverTimePlot,
)

from widgets import FrozenTableView

TZ = datetime.now().astimezone().tzinfo
SEVERITY_MAP = {0: "NO_ALARM", 1: "MINOR", 2: "MAJOR", 3: "INVALID"}

logger = logging.getLogger("")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)-8s] - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel("DEBUG")
    handler.setLevel("DEBUG")


class CAGetThread(QThread):
    """Thread for making a CA get request to the given address. This is used
    to get the description of the curve.
    """

    result_ready = Signal(object)

    def __init__(self, parent: QObject = None, address: str = "") -> None:
        super().__init__(parent=parent)
        self.address = address
        self.stop_flag = False

    def run(self) -> None:
        """Get the value for the given address. Interruptable via the
        stop_flag. Does not attempt to emit the PV Value if interrupted.
        """
        pv = epics.PV(self.address)

        if self.stop_flag:
            return

        try:
            self.result_ready.emit(pv.value)
        except epics.ca.ChannelAccessException as e:
            logger.warning(f"Channel Access error: {e}")

    def stop(self) -> None:
        """Set the stop flag"""
        self.stop_flag = True


class DataVisualizationModel(QAbstractTableModel):
    """Table Model for fetching and storing the data for a given curve on the
    model. Gathers live data directly from the curve, but makes an HTTP request
    to the Archiver Appliance
    """

    reply_recieved = Signal()
    description_changed = Signal()

    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self.df = pd.DataFrame(columns=["Datetime", "Value", "Severity", "Source"])

        self.address = None
        self.unit = None
        self.description = None
        self.caget_thread = None

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.recieve_archive_reply)

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        """Return the row count of the table"""
        if index is not None and index.isValid():
            return 0
        return self.df.shape[0]

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        """Return the column count of the table"""
        if index is not None and index.isValid():
            return 0
        return self.df.shape[1]

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole) -> str:
        """Return the data for the associated role. Currently only supporting DisplayRole."""
        if not index.isValid():
            return None
        elif role == Qt.DisplayRole:
            val = self.df.iat[index.row(), index.column()]
            return str(val)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.DisplayRole) -> str:
        """Return data associated with the header"""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.df.columns[section]

    def set_description(self, description: str) -> None:
        """Set the description of the curve. This is called when the CAGetThread
        emits a result_ready signal.

        Parameters
        ----------
        description : str
            The description of the curve
        """
        self.description = description
        self.description_changed.emit()

    def set_all_data(self, curve_item: TimePlotCurveItem, x_range: list[int] | tuple[int, int]) -> None:
        """Set the model's data for the given curve and the given time range.
        This function determines what kind of data should be saved and prompts
        the methods for setting live or archived data as necessary. This also
        saves the meta data.

        Parameters
        ----------
        curve_item : TimePlotCurveItem
            The curve for the model to collect and store data on
        x_range : list[int] | tuple[int, int]
            The time range to collect and store data between
        """
        self.address = curve_item.address if curve_item.address else ""
        self.unit = curve_item.units

        # Set the meta data label of the DataInsightTool
        self.set_description("Loading...")

        # Create a new CAGetThread to get the description of the curve
        if isinstance(self.caget_thread, CAGetThread) and self.caget_thread.isRunning():
            self.caget_thread.stop()
        self.caget_thread = CAGetThread(self, self.address + ".DESC")
        self.caget_thread.result_ready.connect(self.set_description)
        self.caget_thread.start()

        curve_range = (curve_item.min_x(), curve_item.max_x())
        left_ts = max(x_range[0], curve_range[0])
        right_ts = min(x_range[1], curve_range[1])

        # Populate the model with live data if it is shown on the plot
        if (curve_range[0] <= x_range[1]) and (x_range[0] <= curve_range[1]):
            self.set_live_data(curve_item, (left_ts, right_ts))

        # Populate the model with archive data if it is shown on the plot
        if x_range[0] <= curve_range[0]:
            self.request_archive_data(curve_item.address, (x_range[0], left_ts))
        else:
            # Emulate network reply being recieved for parent widget
            self.reply_recieved.emit()

    def set_live_data(self, curve_item: TimePlotCurveItem, x_range: list[int] | tuple[int, int]) -> None:
        """Set the live data for the given curve in the given time range. Appends
        rows within the time range to the end of the model's dataframe.

        Parameters
        ----------
        curve_item : TimePlotCurveItem
            The curve for the model to collect and store data on
        x_range : list[int] | tuple[int, int]
            The time range to collect and store data between
        """
        data_n = curve_item.points_accumulated
        if data_n == 0:
            return

        data = curve_item.data_buffer[:, -data_n:]
        indices = np.where((x_range[0] <= data[0]) & (data[0] <= x_range[1]))[0]

        convert_data = {"Datetime": [], "Value": [], "Severity": []}
        convert_data["Datetime"] = data[0, indices]
        convert_data["Value"] = data[1, indices]
        convert_data["Severity"] = ["NaN"] * indices.size
        convert_data["Source"] = ["Live"] * indices.size

        live_df = pd.DataFrame(convert_data)
        live_df["Datetime"] = live_df["Datetime"].apply(datetime.fromtimestamp)

        self.beginResetModel()
        self.df = live_df
        self.endResetModel()

    def request_archive_data(self, pv_name: str, x_range: list[int] | tuple[int, int]) -> None:
        """Request data from the Archiver Appliance for the given PV and time range.
        Only gets raw data, never optimized. Ends early if there is no environment
        variable PYDM_ARCHIVER_URL, which would contain the url for the Archiver
        Appliance.

        Parameters
        ----------
        pv_name : str
            The PV address to request data for
        x_range : list[int] | tuple[int, int]
            The time range to collect and store data between
        """
        # Check the $PYDM_ARCHIVER_URL is populated
        base_url = os.getenv("PYDM_ARCHIVER_URL")
        if base_url is None:
            logger.error(
                "Environment variable: PYDM_ARCHIVER_URL must be defined to use the archiver plugin, for "
                "example: http://lcls-archapp.slac.stanford.edu"
            )
            return

        # Correctly format the timestamps for the Archiver Appliance
        from_dt = datetime.fromtimestamp(x_range[0], tz=timezone.utc)
        from_date_str = from_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        to_dt = datetime.fromtimestamp(x_range[1], tz=timezone.utc)
        to_date_str = to_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # Construct the request url and make the request
        url_string = f"{base_url}/retrieval/data/getData.json?pv={pv_name}&from={from_date_str}&to={to_date_str}"
        request = QNetworkRequest(QUrl(url_string))
        self.network_manager.get(request)

    def recieve_archive_reply(self, reply: QNetworkReply) -> None:
        """Process the recieved reply to the request made in request_archive_data.
        Unpack the data and call set_archive_data. Mostly checks if the reply
        contains an error.

        Parameters
        ----------
        reply : QNetworkReply
            Reply to the network request made in request_archive_data
        """
        self.reply_recieved.emit()
        if reply.error() == QNetworkReply.NoError:
            bytes_str = reply.readAll()
            try:
                data_dict = json.loads(str(bytes_str, "utf-8"))
                self.set_archive_data(data_dict)
            except json.JSONDecodeError:
                logger.warning("Data Insight Tool: No data received from archiver")
        else:
            logger.debug(
                f"Request for data from archiver failed, request url: {reply.url()} retrieved header: "
                f"{reply.header(QNetworkRequest.ContentTypeHeader)} error: {reply.error()}"
            )
        reply.deleteLater()

    def set_archive_data(self, data_dict: dict) -> None:
        """Set the live data for the given curve in the given time range. Appends
        rows within the time range to the end of the model's dataframe.

        Parameters
        ----------
        data_dict : dict
            Dictionary containing all data to be added to the model's dataframe
        """
        convert_data = {"Datetime": [], "Value": [], "Severity": []}
        for point in data_dict[0]["data"]:
            ts = point["secs"] + (point["nanos"] * 1e-9)
            convert_data["Datetime"].append(datetime.fromtimestamp(ts))
            convert_data["Value"].append(point["val"])
            convert_data["Severity"].append(SEVERITY_MAP[point["severity"]])
        convert_data["Source"] = ["Archive"] * len(data_dict[0]["data"])
        archive_df = pd.DataFrame(convert_data)

        if self.df.empty:
            self.beginResetModel()
            self.df = archive_df
            self.endResetModel()
        else:
            self.beginInsertRows(QModelIndex(), 0, archive_df.shape[0] - 1)
            self.df = pd.concat([archive_df, self.df])
            self.endInsertRows()
        self.layoutChanged.emit()

    def export_data(self, file_path: Path, extension: str) -> None:
        """Export the model's data to the given file. Adds metadata to the top of
        the exported file with the curve's address, unit (if any), and description.

        Parameters
        ----------
        file_path : Path
            The path of the file to be (over)written with the exported data
        extension : str
            The extension of the file to be (over)written

        Raises
        ------
        ValueError
            Raised when export is requested without data in the model, or when an
            invalid file format is requested for export
        IsADirectoryError
            Raised when the provided filepath is a directory
        """
        if self.df.empty:
            raise ValueError("No data to export. Request data first.")
        if file_path.is_dir():
            raise IsADirectoryError("The selected path is a directory. Select a file to export to.")
        if extension not in [".csv", ".mat", ".json"]:
            raise ValueError("Unrecognized file format requested. Skipping export.")

        header_dict = {"Address": self.address, "Unit": self.unit, "Description": self.description}

        export_df = self.df.copy()
        export_df["Datetime"] = export_df["Datetime"].astype("int64") / 1e9

        if extension == ".csv":
            file_header = "".join([f"{k}: {v}\n" for k, v in header_dict.items()])
            with file_path.open("w") as file:
                file.write(file_header)
                export_df.to_csv(file, index=False, mode="a")
        elif extension == ".mat":
            header_dict.update({name: col.values for name, col in export_df.items()})
            savemat(file_path, header_dict)
        elif extension == ".json":
            if export_df["Value"].dtype == object:
                export_df["Value"] = export_df["Value"].astype("str")
            data_dict = export_df.to_dict(orient="records")
            export_dict = {"meta": header_dict, "data": data_dict}
            with file_path.open("w") as file:
                json.dump(export_dict, file, indent=2)


class DataInsightTool(QWidget):
    """The Data Insight Tool is a standalone widget that allows users to display
    all archive and live data on the plot for any given curve. Users are also able
    to export the raw data from this tool.
    """

    def __init__(self, parent: QObject, plot: PyDMArchiverTimePlot = None) -> None:
        super().__init__(parent=parent)
        self.setWindowFlag(Qt.Window)
        self.resize(600, 600)
        self.setWindowTitle("Data Insight Tool")

        self.layout_init()

        self.data_vis_model.reply_recieved.connect(self.loading_label.hide)
        self.data_vis_model.description_changed.connect(self.set_meta_data)
        self.export_button.clicked.connect(self.export_data_to_file)
        self.pv_select_box.currentIndexChanged.connect(self.get_data)
        self.refresh_button.clicked.connect(self.get_data)

        if isinstance(plot, PyDMArchiverTimePlot):
            self.plot = plot

    @property
    def plot(self) -> PyDMArchiverTimePlot:
        """Return the plot associated with this widget"""
        return self._plot

    @plot.setter
    def plot(self, plot: PyDMArchiverTimePlot) -> None:
        """Set the plot associated with this widget"""
        self._plot = plot
        self.update_pv_select_box()
        if self.pv_select_box.count() > 0:
            self.get_data(0)

    def layout_init(self) -> None:
        """Initialize the layout of the Data Insight Tool widget."""
        self.main_layout = QVBoxLayout()

        # Populate the PV selection and request layout at the top of the widget
        self.request_layout = QHBoxLayout()
        self.pv_select_box = QComboBox()
        self.pv_select_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.request_layout.addWidget(self.pv_select_box, alignment=Qt.AlignLeft)

        self.loading_label = QLabel("Loading...")
        self.loading_label.hide()
        self.request_layout.addWidget(self.loading_label, alignment=Qt.AlignCenter)

        self.export_button = QPushButton("Export to File")
        self.request_layout.addWidget(self.export_button, alignment=Qt.AlignRight)
        self.main_layout.addLayout(self.request_layout)

        # Create the metadata label and refresh button
        self.metadata_layout = QHBoxLayout()
        self.meta_data_label = QLabel()
        self.metadata_layout.addWidget(self.meta_data_label, alignment=Qt.AlignLeft)

        self.refresh_button = QPushButton("Refresh Data")
        self.metadata_layout.addWidget(self.refresh_button, alignment=Qt.AlignRight)
        self.main_layout.addLayout(self.metadata_layout)

        # Set up the main data table in the center of the widget
        self.data_vis_model = DataVisualizationModel()
        self.data_table = FrozenTableView(self.data_vis_model)
        self.main_layout.addWidget(self.data_table)

        self.setLayout(self.main_layout)

    def set_meta_data(self) -> None:
        """Populate the meta_data_label with the curve's unit (if any) and description."""
        meta_labels = []
        if self.data_vis_model.unit:
            meta_labels.append(str(self.data_vis_model.unit))
        if self.data_vis_model.description:
            meta_labels.append(str(self.data_vis_model.description))
        self.meta_data_label.setText(", ".join(meta_labels))

    def combobox_to_curve(self, combobox_ind: int) -> ArchivePlotCurveItem:
        """Convert an index for the pv_select_box combobox to the corresponding
        curve item from the curves model.

        Parameters
        ----------
        combobox_ind : int
            The index for pv_select_box

        Returns
        -------
        ArchivePlotCurveItem
            The curve item that corresponds to the PV chosen on the combobox
        """
        if combobox_ind < 0 or self.pv_select_box.count() <= combobox_ind:
            combobox_ind = self.pv_select_box.currentIndex()
        return self.plot.curveAtIndex(combobox_ind)

    @Slot()
    def update_pv_select_box(self) -> None:
        """Populate the pv_select_box with all curves in the plot. This is called
        when the plot is updated.
        """
        self.pv_select_box.blockSignals(True)
        self.pv_select_box.clear()
        self.pv_select_box.blockSignals(False)
        curve_names = [c.address for c in self.plot._curves if isinstance(c, ArchivePlotCurveItem)]
        self.pv_select_box.addItems(curve_names)

    @Slot()
    def export_data_to_file(self) -> None:
        """Prompt the user to select a file to export data to then prompt the
        DataVisualizationModel to export its data to the selected file.
        """
        file_name, extension_filter = QFileDialog.getSaveFileName(
            self,
            "Export Archive Data",
            Path(".").name,
            "Comma-Separated Values File (*.csv);;MAT-File (*.mat);;JSON File (*.json)",
        )
        if not extension_filter:
            return
        extension = re.search(r"\*(.*?)\)", extension_filter).group(1)
        file_name = Path(file_name).with_suffix(extension)

        try:
            self.data_vis_model.export_data(file_name, extension)
        except (ValueError, IsADirectoryError) as e:
            logger.error(str(e))
            QMessageBox.critical(self, "Error", str(e))

    @Slot()
    @Slot(int)
    def get_data(self, combobox_index: int = -1) -> None:
        """Prompt the DataVisualizationModel to fetch and save the data for the
        curve chosen by the user for the time range on the associated plot.

        Parameters
        ----------
        combobox_index : int, optional
            The index in the pv_select_box for the user selected curve, by default -1
        """
        if self.pv_select_box.count() < 1:
            logger.warning("Curves must be added to the main display before data can be requested.")
            return

        curve_item = self.combobox_to_curve(combobox_index)
        x_range = self.plot.getXAxis().range

        self.data_vis_model.set_all_data(curve_item, x_range)
        self.set_meta_data()
        self.loading_label.show()
