import re

from qtpy.QtGui import QKeyEvent, QDropEvent, QDragMoveEvent, QDragEnterEvent
from qtpy.QtCore import Qt, Slot, QPoint, QObject, QModelIndex
from qtpy.QtWidgets import (
    QMenu,
    QAction,
    QDialog,
    QLineEdit,
    QTableView,
    QGridLayout,
    QHeaderView,
    QPushButton,
    QVBoxLayout,
    QAbstractItemView,
)

from pydm.widgets.baseplot import BasePlotCurveItem
from pydm.widgets.archiver_time_plot import FormulaCurveItem

from config import logger
from widgets import (
    ComboBoxDelegate,
    InsertPVDelegate,
    DeleteRowDelegate,
    ArchiveSearchWidget,
    ColorButtonDelegate,
)
from table_models import ArchiverCurveModel


class TracesTableMixin:
    """Mixins class for the Traces tab of the settings section."""

    def traces_table_init(self) -> None:
        """Initialize the Traces table model and section."""
        self.curves_model = ArchiverCurveModel(self, self.ui.main_plot, self.axis_table_model)
        self.curves_model.invalid_index_signal.connect(self.update_index)

        self.ui.traces_tbl.setModel(self.curves_model)

        self.menu = PVContextMenu(self)
        self.ui.traces_tbl.customContextMenuRequested.connect(self.custom_context_menu)

        hdr = self.ui.traces_tbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        for col_name in ("Channel", "Label", ""):
            channel_col = self.curves_model.getColumnIndex(col_name)
            hdr.setSectionResizeMode(channel_col, QHeaderView.ResizeToContents)
        self.setAcceptDrops(True)
        self.menu.archive_search.append_PVs_requested.connect(self.insertPVs)
        self.curves_model.multiplePVInsert.connect(self.insertPVs)

    def curve_delegates_init(self) -> None:
        """Set column delegates for the Traces table to display widgets."""
        axis_col = self.curves_model.getColumnIndex("Y-Axis Name")
        axis_combo_del = ComboBoxDelegate(self.ui.traces_tbl, self.axis_table_model)
        self.ui.traces_tbl.setItemDelegateForColumn(axis_col, axis_combo_del)

        color_col = self.curves_model.getColumnIndex("Color")
        color_button_del = ColorButtonDelegate(self.ui.traces_tbl)
        self.ui.traces_tbl.setItemDelegateForColumn(color_col, color_button_del)

        style_col = self.curves_model.getColumnIndex("Style")
        style_combo_del = ComboBoxDelegate(self.ui.traces_tbl, {"Direct": None, "Step": "right"})
        self.ui.traces_tbl.setItemDelegateForColumn(style_col, style_combo_del)

        styles = BasePlotCurveItem.lines
        line_style_col = self.curves_model.getColumnIndex("Line Style")
        line_style_del = ComboBoxDelegate(self.ui.traces_tbl, styles)
        self.ui.traces_tbl.setItemDelegateForColumn(line_style_col, line_style_del)

        size_data = {f"{i}px": i for i in range(1, 6)}
        line_width_col = self.curves_model.getColumnIndex("Line Width")
        line_width_del = ComboBoxDelegate(self.ui.traces_tbl, size_data)
        self.ui.traces_tbl.setItemDelegateForColumn(line_width_col, line_width_del)

        symbols = BasePlotCurveItem.symbols
        symbol_col = self.curves_model.getColumnIndex("Symbol")
        symbol_del = ComboBoxDelegate(self.ui.traces_tbl, symbols)
        self.ui.traces_tbl.setItemDelegateForColumn(symbol_col, symbol_del)

        size_data = {f"{i}px": i for i in range(5, 26, 5)}
        symbol_size_col = self.curves_model.getColumnIndex("Symbol Size")
        symbol_size_del = ComboBoxDelegate(self.ui.traces_tbl, size_data)
        self.ui.traces_tbl.setItemDelegateForColumn(symbol_size_col, symbol_size_del)

        delete_col = self.curves_model.getColumnIndex("")
        delete_row_del = DeleteRowDelegate(self.ui.traces_tbl)
        self.ui.traces_tbl.setItemDelegateForColumn(delete_col, delete_row_del)

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        """Handle something (like PV names) being dragged into the table"""
        e.acceptProposedAction()

    def dragMoveEvent(self, e: QDragMoveEvent) -> None:
        """Handle something (like PV names) being dragged through the table"""
        e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent) -> None:
        """Handle something (like PV names) being dropped into the table"""
        data = e.mimeData().text()
        self.insertPVs(data)

    def insertPVs(self, data: str) -> None:
        """Parse the incoming PV name data
        One by one, add them to the end of the curves model
        Resize the table to match the longest PV name/label

        Parameters
        ---------------
        data: str
            The list of pvs in string format with any white space or comma separation"""
        logger.info("Accepting PVs " + data)
        channels = re.split(r"[\n\r,]+", data)
        for channel in channels:
            index = -1
            curve = self.curves_model.curve_at_index(index)
            self.curves_model.set_data(column_name="Channel", curve=curve, value=channel)
        self.ui.traces_tbl.update()

    @Slot(QModelIndex)
    def update_index(self, index: QModelIndex) -> None:
        """Update the given index in the model and clear the selection model.

        Parameters
        ----------
        index : QModelIndex
            The index in the table view to update
        """
        self.ui.traces_tbl.clearSelection()
        self.ui.traces_tbl.update(index)

    @Slot(QPoint)
    def custom_context_menu(self, pos: QPoint) -> None:
        """Open a custom context menu for the Traces table where the
        user right-clicks. If the ColorButton is right-clicked, then do
        not open a context menu.

        Parameters
        ----------
        pos : QPoint
            The position where the context menu should appear
        """
        table = self.ui.traces_tbl
        if not table or not isinstance(table, QTableView):
            logger.error(f"Internal error: {type(table)} is not QTableView")
            return

        index = table.indexAt(pos)
        is_color = index.column() == self.curves_model.getColumnIndex("Color")
        logger.debug(f"ColorButton column selected: {is_color}")

        if index.isValid() and not is_color:
            logger.debug(f"Opening context menu at index {index}")
            self.menu.selected_index = index
            self.menu.popup(table.viewport().mapToGlobal(pos))


class PVContextMenu(QMenu):
    """Right clicking on the curves table opens 3 options - to open a PV search tool,
    Open a formula dialogue, or import a csv. Importing a csv seems to have not yet been
    implemented, but Formulae and PV search are."""

    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)

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

        import_action = QAction("IMPORT CSV", self)
        import_action.triggered.connect(self.import_csv)
        self.addAction(import_action)

    @property
    def selected_index(self) -> QModelIndex:
        """Get the table's selected index."""
        return self._selected_index

    @selected_index.setter
    def selected_index(self, ind: QModelIndex) -> None:
        """Set the table's selected index."""
        self._selected_index = ind

    @Slot()
    def import_csv(self) -> None:
        # TODO: Add action to import csv
        pass


class FormulaDialog(QDialog):
    """Formula Dialog - when a user right clicks on a row in the list of
    curves, they have the option to input a formula. They could opt to type it
    instead, but this opens a box that is a nicer UI for inputting a formula.
    """

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.setWindowTitle("Formula Input")

        # Create the layout for the dialog
        layout = QVBoxLayout(self)

        # Create the QLineEdit for formula input
        self.field = QLineEdit(self)

        # Display list of channels from curve model as table
        self.curveModel = self.parent().parent().curves_model
        self.pv_list = QTableView(self)
        self.pv_list.setModel(self.curveModel)
        self.pv_list.setEditTriggers(QAbstractItemView.EditTriggers(0))
        self.pv_list.setMaximumWidth(1000)
        self.pv_list.setMaximumHeight(1000)

        # Hide all columns unused. Leave one to add a button to
        header = self.pv_list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, self.curveModel.columnCount() - 1):
            self.pv_list.setColumnHidden(i, True)

        insertButton = InsertPVDelegate(self.pv_list)
        insertButton.button_clicked.connect(self.field.insert)
        self.pv_list.setItemDelegateForColumn(self.curveModel.columnCount() - 1, insertButton)

        layout.addWidget(self.pv_list)
        layout.addWidget(self.field)

        self.index = self.parent().selected_index

        # Define the list of calculator buttons.
        # It's a bunch of preset buttons, but users can type other functions under math.
        # fmt: off
        buttons = [
            "7",   "8",      "9",      "+",       "(",      ")",
            "4",   "5",      "6",      "-",       "^2",     "sqrt()",
            "1",   "2",      "3",      "*",       "^-1",    "ln()",
            "0",   "e",      "pi",     "/",       "sin()",  "asin()",
            ".",   "abs()",  "min()",  "^",       "cos()",  "acos()",
            "PV",  "Clear",  "max()",  "mean()",  "tan()",  "atan()",
        ]
        # fmt: on

        # Create the calculator buttons and connect them to the input field
        grid_layout = QGridLayout()
        for i, button_text in enumerate(buttons):
            button = QPushButton(button_text, self)
            row = i // 6
            col = i % 6
            grid_layout.addWidget(button, row, col)
            # Connect the button clicked signal to the appropriate action
            # PV currently does nothing, this is a remnant
            # From when we would have the pv_list open in a new window
            if button_text == "PV":
                self.PVButton = button
                self.PVButton.setCheckable(True)
                self.PVButton.setChecked(True)
                self.PVButton.clicked.connect(self.showPVList)
            elif button_text == "Clear":
                button.clicked.connect(lambda _: self.field.clear())
            else:
                button.clicked.connect(lambda _, text=button_text: self.field.insert(text))
        layout.addLayout(grid_layout)

        # Add an "OK" button to accept the formula and close the dialog
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.accept_formula)
        layout.addWidget(ok_button)
        self.showPVList()

    def keyPressEvent(self, e: QKeyEvent) -> None:
        """Special key press tracker. If enter or return is pressed the formula
        dialog submits the formula.
        """
        if e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter:
            self.accept_formula()
        return super().keyPressEvent(e)

    @Slot()
    def showPVList(self):
        """Hide or show the PV list on PVButton click."""
        show = self.PVButton.isChecked()
        if show:
            self.pv_list.show()
        else:
            self.pv_list.hide()

    def exec_(self):
        """When the formula dialog is opened, get the latest information from
        the curve model. If a formula already exists for the selected index,
        then populate the text box with the existing formula.
        """
        self.index = self.parent().selected_index
        self.pv_list.setRowHidden(len(self.curveModel._row_names) - 1, True)
        for i in range(self.curveModel.rowCount() - 1):
            self.pv_list.setRowHidden(i, False)
        index = self.curveModel.index(self.index.row(), 0)
        curve = self.curveModel._plot._curves[self.index.row()]
        if index.data() and isinstance(curve, FormulaCurveItem):
            self.field.setText(str(index.data()).strip("f://"))
        else:
            self.field.setText("")
        super().exec_()

    @Slot()
    def accept_formula(self) -> None:
        """Set the curve in the curve model to use the entered formula. If the
        formula is invalid, then the dialog box is closed.
        """
        row = self.parent().selected_index.row()
        index = self.curveModel.index(row, 0)

        formula = "f://" + self.field.text()
        formula = re.sub(r"\s+", "", formula)

        passed = self.curveModel.setData(index, formula, Qt.EditRole)

        if passed:
            self.field.setText("")
            self.accept()
