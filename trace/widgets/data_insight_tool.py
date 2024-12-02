import os
import re
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from scipy.io import savemat
from qtpy.QtCore import (
    Qt,
    QUrl,
    Signal,
    QObject,
    QModelIndex,
    QStringListModel,
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
    QApplication,
)

# from widgets import FrozenTableView
from frozen_table_view import FrozenTableView

SEVERITY_MAP = {0: "NO_ALARM", 1: "MINOR", 2: "MAJOR", 3: "INVALID"}

logger = logging.getLogger("")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)-8s] - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel("DEBUG")
    handler.setLevel("DEBUG")


class ArchiveDataModel(QAbstractTableModel):
    reply_recieved = Signal()

    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self.df = pd.DataFrame(columns=["Datetime", "Value", "Severity", "Unit", "Source"])

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

    def request_archive_data(self, pv_name: str, from_dt: datetime, to_dt: datetime):
        from_date_str = from_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        to_date_str = to_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        base_url = os.getenv("PYDM_ARCHIVER_URL")
        if base_url is None:
            logger.error(
                "Environment variable: PYDM_ARCHIVER_URL must be defined to use the archiver plugin, for "
                "example: http://lcls-archapp.slac.stanford.edu"
            )
            return

        url_string = f"{base_url}/retrieval/data/getData.json?pv={pv_name}&from={from_date_str}&to={to_date_str}"

        request = QNetworkRequest(QUrl(url_string))
        self.network_manager.get(request)

    def recieve_archive_reply(self, reply: QNetworkReply):
        self.reply_recieved.emit()
        if reply.error() == QNetworkReply.NoError:
            bytes_str = reply.readAll()
            data_dict = json.loads(str(bytes_str, "utf-8"))
            self.set_all_data(data_dict)
        else:
            logger.debug(
                f"Request for data from archiver failed, request url: {reply.url()} retrieved header: "
                f"{reply.header(QNetworkRequest.ContentTypeHeader)} error: {reply.error()}"
            )
        reply.deleteLater()

    def set_all_data(self, data_dict: dict):
        convert_data = {"Datetime": [], "Value": [], "Severity": []}
        for point in data_dict[0]["data"]:
            ts = point["secs"] + (point["nanos"] * 1e-9)
            convert_data["Datetime"].append(datetime.fromtimestamp(ts))
            convert_data["Value"].append(point["val"])
            convert_data["Severity"].append(SEVERITY_MAP[point["severity"]])
        try:
            convert_data["Unit"] = [data_dict[0]["meta"]["EGU"]] * len(data_dict[0]["data"])
        except KeyError:
            logger.debug("Requested data has no unit.")
        convert_data["Source"] = ["Archive"] * len(data_dict[0]["data"])

        self.beginResetModel()
        self.df = pd.DataFrame(data=convert_data)
        self.endResetModel()
        self.layoutChanged.emit()

    def export_data(self, file_name: Path, extension: str):
        if self.df.empty:
            raise ValueError("No data to export. Request data first.")
        if file_name.is_dir():
            raise IsADirectoryError("The selected path is a directory. Select a file to export to.")
        if extension not in [".csv", ".mat", ".json"]:
            raise ValueError("Unrecognized file format requested. Skipping export.")

        backup = self.df["Datetime"]
        self.df["Datetime"] = self.df["Datetime"].astype("int64") / 1e9

        if extension == ".csv":
            self.df.to_csv(file_name, index=False)
        elif extension == ".mat":
            df_dict = {name: col.values for name, col in self.df.items()}
            savemat(file_name, df_dict)
        elif extension == ".json":
            self.df.to_json(file_name, orient="records", indent=2)

        self.df["Datetime"] = backup


class DataInsightTool(QWidget):
    # def __init__(self, curve_model: QAbstractTableModel, parent: QObject = None) -> None:
    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent=parent)
        self.setWindowFlag(Qt.Window)
        self.resize(600, 600)
        self.setWindowTitle("Data Insight Tool")

        if parent:
            # Get curves model and plot
            pass
        else:
            # Only for testing. Make dummy curves model and plot
            self.curves_model = QStringListModel(
                ["KLYS:LI22:31:KVAC", "SBST:LI29:1:AMPL", "LASR:IN20:196:PWR", "TPG:SYS0:1:MANUAL_PATH"]
            )

            def getXRange():
                return [datetime(2024, 11, 17), datetime(2024, 11, 20)]

            self.get_time_range = getXRange

        self.init()

        self.archive_data_model.reply_recieved.connect(self.loading_label.hide)
        self.request_button.clicked.connect(self.get_data)
        self.export_button.clicked.connect(self.export_data_to_file)

    def init(self):
        self.main_layout = QVBoxLayout()

        # Populate the PV selection and request layout at the top of the widget
        self.request_layout = QHBoxLayout()
        self.pv_select_box = QComboBox()
        self.pv_select_box.setModel(self.curves_model)
        self.request_layout.addWidget(self.pv_select_box, alignment=Qt.AlignLeft)

        self.loading_label = QLabel("Loading...")
        self.loading_label.hide()
        self.request_layout.addWidget(self.loading_label, alignment=Qt.AlignCenter)

        self.request_button = QPushButton("Request Data")
        self.request_layout.addWidget(self.request_button, alignment=Qt.AlignRight)
        self.main_layout.addLayout(self.request_layout)

        # Set up the main data table in the center of the widget
        self.archive_data_model = ArchiveDataModel()
        self.data_table = FrozenTableView(self.archive_data_model)
        self.main_layout.addWidget(self.data_table)

        # Set up the export data layout at the bottom of the widget
        self.export_layout = QHBoxLayout()
        self.export_button = QPushButton("Export to File")
        self.export_layout.addWidget(self.export_button, alignment=Qt.AlignRight)
        self.main_layout.addLayout(self.export_layout)

        self.setLayout(self.main_layout)

    def get_data(self):
        pv_name = self.pv_select_box.currentText()
        time_range = self.get_time_range()

        self.archive_data_model.request_archive_data(pv_name, *time_range)
        self.loading_label.show()

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
            self.archive_data_model.export_data(file_name, extension)
        except (ValueError, IsADirectoryError) as e:
            logger.error(str(e))
            QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dit = DataInsightTool()
    dit.show()

    app.exec_()
