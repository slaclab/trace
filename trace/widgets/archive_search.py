import logging
from os import getenv
from typing import Any

from qtpy.QtGui import QDrag, QKeyEvent
from qtpy.QtCore import (
    Qt,
    QUrl,
    Signal,
    QObject,
    QMimeData,
    QModelIndex,
    QAbstractTableModel,
)
from qtpy.QtNetwork import QNetworkReply, QNetworkRequest, QNetworkAccessManager
from qtpy.QtWidgets import (
    QLabel,
    QWidget,
    QLineEdit,
    QTableView,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QVBoxLayout,
    QAbstractItemView,
)

logger = logging.getLogger("")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)-8s] - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel("INFO")
    handler.setLevel("INFO")


class ArchiveResultsTableModel(QAbstractTableModel):
    """This table model holds the results of an archiver appliance PV search. This search is for names matching
    the input search words, and the results are a list of PV names that match that search.

    Parameters
    ----------
    parent : QObject, optional
        The parent item of this table
    """

    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent=parent)
        self.results_list = []
        self.column_names = ("PV",)

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        """Return the row count of the table"""
        if index is not None and index.isValid():
            return 0
        return len(self.results_list)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        """Return the column count of the table"""
        if index is not None and index.isValid():
            return 0
        return len(self.column_names)

    def data(self, index: QModelIndex, role: int) -> Any:
        """Return the data for the associated role. Currently only supporting DisplayRole."""
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        return self.results_list[index.row()]

    def headerData(self, section, orientation, role=Qt.DisplayRole) -> Any:
        """Return data associated with the header"""
        if role != Qt.DisplayRole:
            return super().headerData(section, orientation, role)

        return str(self.column_names[section])

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Return flags that determine how users can interact with the items in the table"""
        if index.isValid():
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled

    def append(self, pv: str) -> None:
        """Appends a row to this table given the PV name as input"""
        self.beginInsertRows(QModelIndex(), len(self.results_list), len(self.results_list))
        self.results_list.append(pv)
        self.endInsertRows()
        self.layoutChanged.emit()

    def replace_rows(self, pvs: list[str]) -> None:
        """Overwrites any existing rows in the table with the input list of PV names"""
        self.beginInsertRows(QModelIndex(), 0, len(pvs) - 1)
        self.results_list = pvs
        self.endInsertRows()
        self.layoutChanged.emit()

    def clear(self) -> None:
        """Clear out all data stored in this table"""
        self.beginRemoveRows(QModelIndex(), 0, len(self.results_list))
        self.results_list = []
        self.endRemoveRows()
        self.layoutChanged.emit()

    def sort(self, col: int, order=Qt.AscendingOrder) -> None:
        """Sort the table by PV name"""
        self.results_list.sort(reverse=order == Qt.DescendingOrder)
        self.layoutChanged.emit()


class ArchiveSearchWidget(QWidget):
    """Widget for searching and selecting PVs from the EPICS archiver appliance.

    This widget provides a search interface for finding PVs by name patterns
    using the archiver appliance. Users can search for PVs and add them to
    the plot by selecting them from the results table.

    Parameters
    ----------
    parent : QObject, optional
        The parent item of this widget
    """

    append_PVs_requested = Signal(list)

    def __init__(self, parent: QObject = None):
        """Initialize the archive search widget.

        Parameters
        ----------
        parent : QObject, optional
            The parent object
        """
        super().__init__(parent=parent)

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.populate_results_list)

        self.resize(400, 800)
        self.main_layout = QVBoxLayout()

        self.archive_url_layout = QHBoxLayout()
        self.archive_title_label = QLabel("Archive URL:")
        self.archive_url_layout.addWidget(self.archive_title_label)
        self.archive_url_textedit = QLineEdit(getenv("PYDM_ARCHIVER_URL"))
        self.archive_url_textedit.setFixedWidth(250)
        self.archive_url_textedit.setFixedHeight(25)
        self.archive_url_layout.addWidget(self.archive_url_textedit)
        self.main_layout.addLayout(self.archive_url_layout)

        self.search_layout = QHBoxLayout()
        self.search_label = QLabel("Pattern:")
        self.search_layout.addWidget(self.search_label)
        self.search_box = QLineEdit()
        self.search_layout.addWidget(self.search_box)
        self.search_button = QPushButton("Search")
        self.search_button.setDefault(True)
        self.search_button.clicked.connect(self.request_archiver_info)
        self.search_layout.addWidget(self.search_button)
        self.main_layout.addLayout(self.search_layout)

        self.loading_label = QLabel("Loading...")
        self.loading_label.hide()
        self.main_layout.addWidget(self.loading_label)

        self.results_table_model = ArchiveResultsTableModel()
        self.results_view = QTableView(self)
        self.results_view.setModel(self.results_table_model)
        # self.results_view.setProperty("showDropIndicator", False)
        # self.results_view.setDragDropOverwriteMode(False)
        # self.results_view.setDragEnabled(True)  # Removing drag & drop for now
        self.results_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.results_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        # self.results_view.setDropIndicatorShown(True)
        self.results_view.setCornerButtonEnabled(False)
        self.results_view.setSortingEnabled(True)
        self.results_view.verticalHeader().setVisible(False)
        self.results_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.results_view.startDrag = self.startDragAction
        self.results_view.doubleClicked.connect(lambda: self.append_PVs_requested.emit(self.selectedPVs()))
        self.main_layout.addWidget(self.results_view)

        self.insert_button = QPushButton("Add PVs")
        self.insert_button.clicked.connect(lambda: self.append_PVs_requested.emit(self.selectedPVs()))
        self.main_layout.addWidget(self.insert_button)

        self.setLayout(self.main_layout)

    def selectedPVs(self) -> list[str]:
        """Get the list of selected PVs from the results table.

        Returns
        -------
        list[str]
            List of selected PV names
        """
        indices = self.results_view.selectedIndexes()
        pv_list = []
        for index in indices:
            pv_list.append(self.results_table_model.results_list[index.row()])
        return pv_list

    def startDragAction(self, supported_actions) -> None:
        """Handle drag action for PV names.

        This method is called when a user initiates a drag action for one of
        the results in the table. It allows dragging PV names onto a plot to
        automatically start drawing data for that PV.

        Parameters
        ----------
        supported_actions : Qt.DropActions
            The supported drop actions, unused
        """
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.selectedPVs())
        drag.setMimeData(mime_data)
        drag.exec_()

    def keyPressEvent(self, e: QKeyEvent) -> None:
        """Handle key press events for search submission.

        Parameters
        ----------
        e : QKeyEvent
            The key press event
        """
        if e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter:
            self.request_archiver_info()
        return super().keyPressEvent(e)

    def request_archiver_info(self) -> None:
        """Send a search request to the archiver appliance.

        Converts the search text to a regex pattern and queries the archiver
        appliance for matching PV names.
        """
        search_text = self.search_box.text()
        search_text = search_text.replace("?", ".")
        search_text = search_text.replace("*", ".*")
        search_text = search_text.replace("%", ".*")
        url_string = f"{self.archive_url_textedit.text()}/retrieval/bpl/searchForPVsRegex?regex=.*{search_text}.*"
        request = QNetworkRequest(QUrl(url_string))
        self.network_manager.get(request)
        self.loading_label.show()

    def populate_results_list(self, reply: QNetworkReply) -> None:
        """Handle the response from the archiver appliance search.

        Parameters
        ----------
        reply : QNetworkReply
            The network reply containing search results
        """
        self.loading_label.hide()
        if reply.error() == QNetworkReply.NoError:
            self.results_table_model.clear()
            bytes_str = reply.readAll()
            pv_list = str(bytes_str, "utf-8").split()
            self.results_table_model.replace_rows(pv_list)
        else:
            logger.error(f"Could not retrieve archiver results due to: {reply.error()}")
        reply.deleteLater()
