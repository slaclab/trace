import os
import re
import json
import logging
from typing import Iterable
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import tzlocal
from epics import caget
from scipy.io import savemat
from qtpy.QtCore import (
    Qt,
    QUrl,
    Slot,
    Signal,
    QObject,
    QModelIndex,
    QAbstractTableModel,
    QSortFilterProxyModel,
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

TZ = tzlocal.get_localzone()
SEVERITY_MAP = {0: "NO_ALARM", 1: "MINOR", 2: "MAJOR", 3: "INVALID"}

logger = logging.getLogger("")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)-8s] - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel("DEBUG")
    handler.setLevel("DEBUG")


class DataVisualizationModel(QAbstractTableModel):
    reply_recieved = Signal()

    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self.df = pd.DataFrame(columns=["Datetime", "Value", "Severity", "Source"])

        self.address = None
        self.unit = None
        self.description = None

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.recieve_archive_reply)

    def rowCount(self, index: QModelIndex = QModelIndex()):
        return self.df.shape[0]

    def columnCount(self, index: QModelIndex = QModelIndex()):
        return self.df.shape[1]

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole):
        if not index.isValid():
            return None
        elif role == Qt.DisplayRole:
            val = self.df.iat[index.row(), index.column()]
            return str(val)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.df.columns[section]

    def set_all_data(self, curve_item: TimePlotCurveItem, x_range: Iterable[int]):
        self.address = curve_item.address
        self.unit = curve_item.units
        self.description = caget(curve_item.address + ".DESC")

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

    def set_live_data(self, curve_item: TimePlotCurveItem, x_range: Iterable[int]):
        """Set the live data for the given curve in the given time range. Appends
        rows within the time range to the end of the model's dataframe.

        Parameters
        ----------
        curve_item : TimePlotCurveItem
            The curve for the model to collect and store data on
        x_range : Iterable[int]
            The time range to collect and store data between
        """
        data_n = curve_item.getBufferSize()
        data = curve_item.data_buffer[:, :data_n]
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

    def request_archive_data(self, pv_name: str, x_range: Iterable[int]):
        """Request data from the Archiver Appliance for the given PV and time range.
        Only gets raw data, never optimized. Ends early if there is no environment
        variable PYDM_ARCHIVER_URL, which would contain the url for the Archiver
        Appliance.

        Parameters
        ----------
        pv_name : str
            The PV address to request data for
        x_range : Iterable[int]
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

    def recieve_archive_reply(self, reply: QNetworkReply):
        self.reply_recieved.emit()
        if reply.error() == QNetworkReply.NoError:
            bytes_str = reply.readAll()
            data_dict = json.loads(str(bytes_str, "utf-8"))
            self.set_archive_data(data_dict)
        else:
            logger.debug(
                f"Request for data from archiver failed, request url: {reply.url()} retrieved header: "
                f"{reply.header(QNetworkRequest.ContentTypeHeader)} error: {reply.error()}"
            )
        reply.deleteLater()

    def set_archive_data(self, data_dict: dict):
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

    def export_data(self, file_path: Path, extension: str):
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


class CurveFilterModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        curve = self.sourceModel().curve_at_index(source_row)
        return isinstance(curve, ArchivePlotCurveItem) and bool(curve.address)


class DataInsightTool(QWidget):
    def __init__(self, parent: QObject, curves_model: QAbstractTableModel, plot: PyDMArchiverTimePlot) -> None:
        super().__init__(parent=parent)
        self.setWindowFlag(Qt.Window)
        self.resize(600, 600)
        self.setWindowTitle("Data Insight Tool")

        # Get curves model and function for getting plot x-range
        self.curves_model = curves_model
        self.curve_filter_model = CurveFilterModel()
        self.curve_filter_model.setSourceModel(self.curves_model)
        self.plot = plot

        self.layout_init()

        self.data_vis_model.reply_recieved.connect(self.loading_label.hide)
        self.export_button.clicked.connect(self.export_data_to_file)
        self.pv_select_box.currentIndexChanged.connect(self.get_data)
        self.refresh_button.clicked.connect(self.get_data)

        self.get_data(0)

    def layout_init(self):
        self.main_layout = QVBoxLayout()

        # Populate the PV selection and request layout at the top of the widget
        self.request_layout = QHBoxLayout()
        self.pv_select_box = QComboBox()
        self.pv_select_box.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.pv_select_box.setModel(self.curve_filter_model)
        self.request_layout.addWidget(self.pv_select_box, alignment=Qt.AlignLeft)

        self.loading_label = QLabel("Loading...")
        self.loading_label.hide()
        self.request_layout.addWidget(self.loading_label, alignment=Qt.AlignCenter)

        self.export_button = QPushButton("Export to File")
        self.request_layout.addWidget(self.export_button, alignment=Qt.AlignRight)
        self.main_layout.addLayout(self.request_layout)

        # Create the metadata label and refresh button
        self.metadata_layout = QHBoxLayout()
        self.metadata_label = QLabel()
        self.metadata_layout.addWidget(self.metadata_label, alignment=Qt.AlignLeft)

        self.refresh_button = QPushButton("Refresh Data")
        self.metadata_layout.addWidget(self.refresh_button, alignment=Qt.AlignRight)
        self.main_layout.addLayout(self.metadata_layout)

        # Set up the main data table in the center of the widget
        self.data_vis_model = DataVisualizationModel()
        self.data_table = FrozenTableView(self.data_vis_model)
        self.main_layout.addWidget(self.data_table)

        self.setLayout(self.main_layout)

    def export_data_to_file(self):
        file_name, extension_filter = QFileDialog.getSaveFileName(
            self,
            "Export Archive Data",
            Path(".").name,
            "Comma-Separated Values File (*.csv);;MAT-File (*.mat);;JSON File (*.json)",
        )
        extension = re.search(r"\*(.*?)\)", extension_filter).group(1)
        file_name = Path(file_name).with_suffix(extension)

        try:
            self.data_vis_model.export_data(file_name, extension)
        except (ValueError, IsADirectoryError) as e:
            logger.error(str(e))
            QMessageBox.critical(self, "Error", str(e))

    def set_metadata(self):
        meta_str = ""
        if self.data_vis_model.unit:
            meta_str = self.data_vis_model.unit + ", "
        meta_str += self.data_vis_model.description
        self.metadata_label.setText(meta_str)

    @Slot()
    @Slot(int)
    def get_data(self, curve_index: int = -1):
        if curve_index < 0:
            curve_index = self.pv_select_box.currentIndex()
        curve_item = self.curves_model.curve_at_index(curve_index)
        x_range = self.plot.getXAxis().range

        self.data_vis_model.set_all_data(curve_item, x_range)
        self.set_metadata()
        self.loading_label.show()
