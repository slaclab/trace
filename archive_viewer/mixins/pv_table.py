from qtpy.QtCore import (Qt, Slot, QPoint, QModelIndex)
from qtpy.QtWidgets import (QComboBox, QCheckBox, QSlider, QHeaderView, QMenu,
                            QStyledItemDelegate, QAction, QTableView, QDialog,
                            QVBoxLayout, QGridLayout, QLineEdit, QPushButton)
from config import logger
from widgets import (ColorButton, PVTableDelegate, ArchiveSearchWidget)
from table_models import PVTableModel


class PVTableMixin:
    def pv_table_init(self):
        self.col_wids = {"ROW_HEADER_HIDDEN": str,
                         "PV NAME": None,
                         "RANGE AXIS": QComboBox,
                         "VISIBLE": QCheckBox,
                         "RAW": QCheckBox,
                         "COLOR": ColorButton,
                         "TYPE": QComboBox,
                         "WIDTH": QSlider}

        self.pv_table_model = PVTableModel(self, self.col_wids)

        self.ui.traces_tbl.setModel(self.pv_table_model)

        self.ui.traces_tbl.hideColumn(0)
        # self.ui.traces_tbl.setDragDropOverwriteMode(False)
        # self.ui.traces_tbl.setAcceptDrops(True)
        # self.ui.traces_tbl.setDropIndicatorShown(True)

        my_delegate = PVTableDelegate(self.ui.traces_tbl, self.col_wids)
        self.ui.traces_tbl.setItemDelegate(my_delegate)
        self.ui.traces_tbl.setItemDelegateForColumn(0, QStyledItemDelegate())
        self.ui.traces_tbl.setItemDelegateForColumn(1, QStyledItemDelegate())

        hdr = self.ui.traces_tbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        for i in range(3, 6):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.menu = PVContextMenu(self)
        self.ui.traces_tbl.customContextMenuRequested.connect(
            self.custom_context_menu)

    @Slot(QPoint)
    def custom_context_menu(self, pos: QPoint):
        table = self.ui.traces_tbl
        if not table or not isinstance(table, QTableView):
            logger.error(f"Internal error: {type(table)} is not QTableView")
            return

        index = table.indexAt(pos)
        is_color = "COLOR" == table.model().headerData(index.column(),
                                                       Qt.Horizontal,
                                                       Qt.DisplayRole)
        logger.debug(f"ColorButton solumn selected: {is_color}")

        if index.isValid() and not is_color:
            self.menu.selected_index = index
            self.menu.popup(table.viewport().mapToGlobal(pos))


class PVContextMenu(QMenu):
    # TODO: Change this QMenu so functions that change data stay in table object
    #   - Move functions to table widget
    #   - Init parameters: dict("ACTION_NAME": function)
    #   - Init: Loop through dict values:
    #       - Create action w/ name
    #       - action.triggered.connect(function)
    #       - self.addAction(action)

    # data_changed_signal = Signal(int)

    # TODO: Archived PVs are no longer draggable from the search tool. Find out why

    def __init__(self, parent=None):
        super().__init__(parent)
        # self.logger = getLogger(__name__)
        self._selected_index = None
        self.archive_search = ArchiveSearchWidget()
        self._formula_dialog = FormulaDialog(self)

        # Add "SEARCH PV" option
        search_pv_action = QAction("SEARCH PV", self)
        search_pv_action.triggered.connect(self.archive_search.show)
        self.addAction(search_pv_action)

        # Add "FORMULA" option
        formula_action = QAction("FORMULA", self)
        formula_action.triggered.connect(self._formula_dialog.exec_)
        self.addAction(formula_action)

        # Add "DELETE PV" option
        delete_pv_action = QAction("DELETE PV", self)
        delete_pv_action.triggered.connect(self.delete_pv)
        self.addAction(delete_pv_action)

        import_action = QAction("IMPORT CSV", self)
        import_action.triggered.connect(self.import_csv)
        self.addAction(import_action)

    @property
    def selected_index(self):
        return self._selected_index
    
    @selected_index.setter
    def selected_index(self, ind: QModelIndex):
        self._selected_index = ind

    # @Slot()
    # def search_pv(self):
    #     self.archive_search.show()

    @Slot()
    def delete_pv(self):
        if not self.selected_index or not self.selected_index.isValid():
            logger.error("PV invalid, unable to delete row")
            return
        self.selected_index.model().removeRow(self.selected_index.row())
        logger.debug(f"Deleted row: {self.selected_index.row()}")

    @Slot()
    def import_csv(self):
        pass


class FormulaDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        # self.logger = getLogger(__name__)
        self.setWindowTitle("Formula Input")

        # Create the layout for the dialog
        layout = QVBoxLayout(self)

        # Create the QLineEdit for formula input
        self.field = QLineEdit(self)
        layout.addWidget(self.field)

        # Define the list of calculator buttons
        buttons = ["7", "8", "9", "+",
                   "4", "5", "6", "-",
                   "1", "2", "3", "*",
                   "0", "(", ")", "/",
                   ".", "PV", "Clear", "="]

        # Create the calculator buttons and connect them to the input field
        grid_layout = QGridLayout()
        for i, button_text in enumerate(buttons):
            button = QPushButton(button_text, self)
            row = i // 4
            col = i % 4
            grid_layout.addWidget(button, row, col)

            # Connect the button clicked signal to the appropriate action
            if button_text == "PV":
                button.clicked.connect(lambda _: self.field.insert("PV"))
            elif button_text == "Clear":
                button.clicked.connect(lambda _: self.field.clear())
            elif button_text == "=":
                button.clicked.connect(self.evaluate_formula)
            else:
                button.clicked.connect(lambda _, text=button_text: self.field.insert(text))

        layout.addLayout(grid_layout)

        # Add an input field for PV name
        self.pv_name_input = QLineEdit(self)
        self.pv_name_input.setPlaceholderText("Enter PV name")
        layout.addWidget(self.pv_name_input)

        # Add an "OK" button to accept the formula and close the dialog
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.accept_formula)
        layout.addWidget(ok_button)

    def evaluate_formula(self, **kwargs):
        # Evaluate the formula expression and update the formula input field
        # TODO: Check if PVs used are in Table Model
        #   if yes, replace with row header; if no, add to TableModel and replace with row header
        formula = self.field.text()
        try:
            result = eval(formula)
            self.field.setText(str(result))
        except (SyntaxError, TypeError):
            self.field.setText("Error")
            logger.error("Invalid formula evaluated.")

    def accept_formula(self, **kwargs):
        # Retrieve the formula and PV name and perform desired actions
        # TODO: Evaluate the formula before accepting, prompt user if invalid(?)
        formula = self.field.text()
        pv_name = self.pv_name_input.text()

        print("Formula:", formula)
        print("PV Name:", pv_name)

        self.accept()
