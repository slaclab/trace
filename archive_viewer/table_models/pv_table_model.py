from PyQt5.QtCore import (QModelIndex, Qt) # QMimeData
from qtpy.QtGui import QColor
from qtpy.QtCore import (QModelIndex, Qt, Slot, QAbstractTableModel, QUrl)
from qtpy.QtWidgets import (QWidget, QComboBox, QSlider, QCheckBox)
from qtpy.QtNetwork import (QNetworkAccessManager, QNetworkReply, QNetworkRequest)
from widgets import ColorButton
from config import archiver_urls, logger


class PVTableModel(QAbstractTableModel):
    def __init__(self, parent: QWidget, column_widgets: dict):
        super().__init__(parent)
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.archive_validation)

        self.headers = list(column_widgets.keys())
        self.widgets = list(column_widgets.values())

        self._data = []
        self._error = []
        self.init_data()

    def rowCount(self, index: QModelIndex = QModelIndex()):
        """Return the number of rows in the model."""
        return len(self._data)

    def columnCount(self, index: QModelIndex = QModelIndex()):
        """Return the number of columns in the model."""
        return len(self.headers)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):
        """Return the index's data."""
        if not index.isValid():
            return
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            return str(self._data[index.row()][index.column()])
        elif role == Qt.UserRole:
            return self._data[index.row()][index.column()]
        elif role == Qt.ForegroundRole:
            if self._error[index.row()]:
                return QColor(Qt.red)
            return QColor(Qt.black)

    def setData(self, index: QModelIndex, value, role: Qt.ItemDataRole):
        """Set the index's data on edit."""
        if not index.isValid() or role != Qt.EditRole:
            return False

        logger.debug(f"Setting table data for index {(index.row(), index.column())}")
        if index.column() == 1:
            # TODO: Account for cases where multiple URLs are accessed
            #   and have differences in PV validity (race condition)

            for url in archiver_urls.values():
                url_str = f"{url}/retrieval/bpl/getMatchingPVs?pv={value}"

                reply = self.network_manager.get(QNetworkRequest(QUrl(url_str)))
                reply.setProperty("index", index)
                reply.setProperty("pv_name", value)
                logger.debug(f"Archiver validation request: {reply.url()}")
        self._data[index.row()][index.column()] = value
        self.dataChanged.emit(index, index)
        return True

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: Qt.ItemDataRole):
        """Set the horizontal or vertical header's text."""
        if role != Qt.DisplayRole:
            return

        if orientation == Qt.Horizontal:
            return self.headers[section]
        elif orientation == Qt.Vertical:
            return self._data[section][0]

    def flags(self, index: QModelIndex):
        fl = super().flags(index)
        fl |= (Qt.ItemIsSelectable | Qt.ItemIsEnabled
               | Qt.ItemIsEditable | Qt.ItemIsDropEnabled)
        return fl

    def supportedDropActions(self):
        return Qt.MoveAction | Qt.CopyAction

    def removeRows(self, row: int, count:int,  parent=QModelIndex()):
        if count < 1 or (row + count) > len(self._data):
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        del self._data[row:(row + count)]
        self.endRemoveRows()

        if (row + count) == (len(self._data) + 1):
            self.add_empty_row()

        return True

    def next_header(self):
        if not self._data:
            return 'A'

        old_header = self._data[-1][0]
        new_header = ""

        if old_header == 'Z' * len(old_header):
            return 'A' * (len(old_header) + 1)

        inc = 1
        for i in range(len(old_header) - 1, -1, -1):
            old_val = ord(old_header[i]) - ord('A') + inc
            new_val = chr(old_val % 26 + ord('A'))
            new_header = new_val + new_header
            inc = 1 if old_header[i] == 'Z' else 0

        return new_header

    def init_data(self, csv_filename=""):
        if csv_filename:
            self.import_csv(csv_filename)

        self.add_empty_row()

    def add_empty_row(self):
        new_row = []

        for wid in self.widgets:
            if wid is str:
                new_row.append(self.next_header())
            elif wid is None:
                new_row.append("")
            elif wid is QComboBox or wid is QSlider:
                new_row.append(0)
            elif wid is QCheckBox:
                new_row.append(True)
            elif wid is ColorButton:
                color = ColorButton.index_color(self.rowCount())
                new_row.append(color.name())
            else:
                new_row.append(None)

        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append(new_row)
        self._error.append(False)
        self.endInsertRows()

    def import_csv(self, filename=""):
        if not filename:
            return
        # TODO: the rest

    @Slot(QNetworkReply)
    def archive_validation(self, reply: QNetworkReply):
        # Test PV: VPIO:IN20:111:VRAW

        index = reply.property("index")
        pv_name = reply.property("pv_name")

        if reply.error() != QNetworkReply.NoError or not index:
            logger.error("Invalid Network Reply recieved")
            reply.deleteLater()
            return

        bytes_str = reply.readAll()
        valid_list = str(bytes_str, "utf-8")
        logger.debug(f"Archiver valid_pv_list: {valid_list}")

        is_valid = pv_name and pv_name in valid_list
        self._error[index.row()] = not is_valid
        self._data[index.row()][index.column()] = pv_name
        self.dataChanged.emit(index, index)

        if is_valid and index.row() == (len(self._data) - 1):
            self.add_empty_row()

        reply.deleteLater()

    # TODO: Unable to drag from search widget to table.
    #   This was my attempt to fix it:
    # def mimeTypes(self):
    #     return ["application/vnd.text.list"]

    # def canDropMimeData(self, data: QMimeData, action: Qt.DropAction,
    #                     row: int, column: int, parent: QModelIndex):
    #     # return super().canDropMimeData(data, action, row, column, parent)
    #     if column != 1:
    #         return False
    #     return True

    # def dropMimeData(self, data: QMimeData, action: Qt.DropAction,
    #                  row: int, column: int, parent: QModelIndex):
    #     # return super().dropMimeData(data, action, row, column, parent)
    #     logger.info("attempting drop")

    #     if not self.canDropMimeData(data, action, row, column, parent):
    #         return False

    #     if action == Qt.IgnoreAction:
    #         return True

    #     ind = self.index(len(self._data), 1, QModelIndex())
    #     ret_status = self.setData(ind, data.text(), Qt.EditRole)
    #     logger.info(ret_status)
    #     return ret_status
