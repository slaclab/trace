import re
from typing import Any

from qtpy.QtGui import QKeyEvent
from qtpy.QtCore import Qt, Slot, Signal, QObject, QModelIndex, QAbstractTableModel
from qtpy.QtWidgets import (
    QDialog,
    QLineEdit,
    QTableView,
    QGridLayout,
    QHeaderView,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QAbstractItemView,
)


class FormulaDialog(QDialog):
    """A QDialog that provides a user-friendly interface for creating
    mathematical formulas using existing curves as variables. It includes
    a calculator-style button layout and a table showing available curve
    variables.
    """

    formula_accepted = Signal(str)

    def __init__(self, parent: QObject):
        """Initialize the formula dialog.

        Parameters
        ----------
        parent : QObject
            The parent object
        """
        super().__init__(parent)
        self.setWindowTitle("Formula Input")

        layout = QVBoxLayout(self)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.field = QLineEdit(self)
        self.curve_model = CurveModel(parent)

        self.pv_list = QTableView(self)
        self.pv_list.setModel(self.curve_model)
        self.pv_list.setEditTriggers(QAbstractItemView.EditTriggers(0))
        self.pv_list.setMaximumWidth(1000)
        self.pv_list.setMaximumHeight(1000)

        # Hide all columns unused. Leave one to add a button to
        header = self.pv_list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

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

    def keyPressEvent(self, e: QKeyEvent) -> None:
        """Handle key press events for formula submission.

        Parameters
        ----------
        e : QKeyEvent
            The key press event
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
        """Accept the entered formula and emit the formula_accepted signal."""
        formula = "f://" + self.field.text()
        formula = re.sub(r"\s+", "", formula)

        self.formula_accepted.emit(formula)
        self.field.setText("")
        self.accept()

    @Slot(QModelIndex)
    def insert_pv_key(self, index: QModelIndex) -> None:
        """Insert the variable name into the formula field when a row is double-clicked.

        Parameters
        ----------
        index : QModelIndex
            The index of the double-clicked row
        """
        if index.isValid():
            key = self.curve_model.row_to_key(index.row())
            if key:
                current_text = self.field.text()
                cursor_pos = self.field.cursorPosition()
                # Add the variable with curly braces
                new_text = current_text[:cursor_pos] + "{" + key + "}" + current_text[cursor_pos:]
                self.field.setText(new_text)
                # Move cursor after the inserted variable (key length + 2 characters for braces)
                self.field.setCursorPosition(cursor_pos + len(key) + 2)


class CurveModel(QAbstractTableModel):
    """Table model for displaying available curves in the formula dialog.
    It provides a two-column view of available curves with their
    variable names and curve names for use in formula creation.
    """

    curve_deleted = Signal(object)

    def __init__(self, control_panel):
        """Initialize the curve model.

        Parameters
        ----------
        control_panel : ControlPanel
            The control panel containing the curve dictionary
        """
        super().__init__()
        self.control_panel = control_panel
        self._headers = ["Variable Name", "Curve Name"]

    def rowCount(self, parent=QModelIndex()) -> int:
        """Return the number of rows in the model."""
        if hasattr(self.control_panel, "curve_dict"):
            return len(self.control_panel.curve_dict)
        return 0

    def columnCount(self, parent=QModelIndex()) -> int:
        """Return the number of columns in the model."""
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole) -> Any:
        """Return the data for the given index and role.

        Parameters
        ----------
        index : QModelIndex
            The model index
        role : int
            The data role

        Returns
        -------
        Any
            The data for the given index and role
        """
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

    def headerData(self, section, orientation, role=Qt.DisplayRole) -> Any:
        """Return the header data for the given section.

        Parameters
        ----------
        section : int
            The section index
        orientation : Qt.Orientation
            The orientation (horizontal or vertical)
        role : int
            The data role

        Returns
        -------
        Any
            The header data
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def row_to_key(self, row: int) -> str:
        """Get the variable key for the given row index.

        Parameters
        ----------
        row : int
            Row index for the requested key.

        Returns
        -------
        str or None
            The variable key for the row, or None if invalid
        """
        if not (0 <= row < self.rowCount()):
            return None

        curve_dict = self.control_panel.curve_dict
        keys = list(curve_dict.keys())
        return keys[row]

    def refresh(self) -> None:
        """Force a refresh of the model data."""
        self.beginResetModel()
        self.endResetModel()
