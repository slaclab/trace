import re

from qtpy.QtGui import QKeyEvent
from qtpy.QtCore import Qt, Slot, Signal, QObject, QModelIndex, QAbstractTableModel
from qtpy.QtWidgets import (
    QDialog,
    QLineEdit,
    QTableView,
    QGridLayout,
    QHeaderView,
    QPushButton,
    QVBoxLayout,
    QAbstractItemView,
)


class FormulaDialog(QDialog):
    """Formula Dialog - when a user right clicks on a row in the list of
    curves, they have the option to input a formula. They could opt to type it
    instead, but this opens a box that is a nicer UI for inputting a formula.
    """

    formula_accepted = Signal(str)

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.setWindowTitle("Formula Input")

        layout = QVBoxLayout(self)
        self.field = QLineEdit(self)
        self.curve_model = CurveModel(parent)

        self.pv_list = QTableView(self)
        self.pv_list.setModel(self.curve_model)
        self.pv_list.setEditTriggers(QAbstractItemView.EditTriggers(0))
        self.pv_list.setMaximumWidth(1000)
        self.pv_list.setMaximumHeight(1000)

        # Hide all columns unused. Leave one to add a button to
        header = self.pv_list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)

        layout.addWidget(self.pv_list)
        layout.addWidget(self.field)

        self.pv_list.doubleClicked.connect(self.insert_pv_key)

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
        ok_button = QPushButton("Add Formula Curve", self)
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

    @Slot()
    def accept_formula(self) -> None:
        """Set the curve in the curve model to use the entered formula. If the
        formula is invalid, then the dialog box is closed.
        """
        formula = "f://" + self.field.text()
        formula = re.sub(r"\s+", "", formula)

        self.formula_accepted.emit(formula)
        self.field.setText("")
        self.accept()

    @Slot(QModelIndex)
    def insert_pv_key(self, index):
        """Insert the variable name into the formula field when a row is double-clicked"""
        if index.isValid() and index.column() == 0:  # Only respond to clicks on the key column
            key = index.data()
            if key:
                current_text = self.field.text()
                cursor_pos = self.field.cursorPosition()
                # Add the variable with curly braces
                new_text = current_text[:cursor_pos] + "{" + key + "}" + current_text[cursor_pos:]
                self.field.setText(new_text)
                # Move cursor after the inserted variable (key length + 2 characters for braces)
                self.field.setCursorPosition(cursor_pos + len(key) + 2)


class CurveModel(QAbstractTableModel):
    curve_deleted = Signal(object)

    def __init__(self, control_panel):
        super().__init__()
        self.control_panel = control_panel
        self._headers = ["Variable Name", "Curve Name"]

    def _get_plot(self):
        """Safely get the plot from the control panel"""
        try:
            if hasattr(self.control_panel, "_plot") and self.control_panel._plot:
                return self.control_panel._plot
            elif hasattr(self.control_panel, "plot"):
                return self.control_panel.plot
            return None
        except AttributeError:
            return None

    def rowCount(self, parent=QModelIndex()):
        if hasattr(self.control_panel, "curve_dict"):
            return len(self.control_panel.curve_dict)
        return 0

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if not hasattr(self.control_panel, "curve_dict"):
            return None

        curve_dict = self.control_panel.curve_dict
        if len(curve_dict) == 0:
            return None

        # Get the key at this row
        keys = list(curve_dict.keys())
        if index.row() >= len(keys):
            return None

        key = keys[index.row()]
        curve = curve_dict[key]

        if role == Qt.DisplayRole:
            if index.column() == 0:
                return key
            elif index.column() == 1:
                if hasattr(curve, "name") and callable(curve.name):
                    return curve.name()
                elif hasattr(curve, "name"):
                    return curve.name
                elif hasattr(curve, "address"):
                    return curve.address
                return str(curve)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def refresh(self):
        """Force a refresh of the model data"""
        self.beginResetModel()
        self.endResetModel()
