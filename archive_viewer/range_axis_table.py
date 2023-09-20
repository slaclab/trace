from functools import partial
from qtpy import QtCore
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QTableWidget,
    QSpinBox,
    QHeaderView,
    QCompleter,
)
from collections.abc import MutableSequence
from time_axis_table import TimeAxisTable, TimeAxisList


class RangeAxisList(MutableSequence):
    def __init__(self, iterable=()):
        self._list = list(iterable)
        self.axis_names = []  # Maintain a list of range axis names
        self.callback = None

    def __getitem__(self, key):
        return self._list.__getitem__(key)

    def __setitem__(self, key, item):
        self._list.__setitem__(key, item)
        # trigger change handler
        if self.callback:
            self.callback()

    def __delitem__(self, key):
        self._list.__delitem__(key)
        self.axis_names.pop(key)
        if self.callback:
            self.callback()

    def __len__(self):
        return self._list.__len__()

    def insert(self, index, item):
        self._list.insert(index, item)
        self.axis_names.insert(index, item[0])  # Assuming the name is stored at index 0
        if self.callback:
            self.callback()

    def set_callback(self, callback):
        self.callback = callback


class RangeAxisTableWidget(QWidget):
    send_data_change_signal = QtCore.Signal()

    def __init__(self):
        super(RangeAxisTableWidget, self).__init__()
        self.data = RangeAxisList()  # Initialize RangeAxisList without any default value
        self.data.set_callback(self.data_changed_callback)
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["RANGE AXIS NAME", "MAX", "MIN", "TYPE", "KEEP RANGES", "POSITION"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.main_layout.addWidget(self.table)

        self.add_Row(0)

    def add_Row(self, index):
        current_row_count = self.table.rowCount()
        self.table.insertRow(current_row_count)

        for i in range(self.table.columnCount()):
            if i == 0:  # RANGE AXIS NAME column
                line_edit = QLineEdit()
                completer = QCompleter(self.data.axis_names)  # Provide existing names for completion
                line_edit.setCompleter(completer)
                self.table.setCellWidget(index, i, line_edit)
                line_edit.textChanged.connect(partial(self.update_data, index, i, line_edit.text()))
                completer.activated.connect(partial(self.update_data, index, i, completer.currentCompletion()))
            elif i in [1, 2]:
                widget = QLineEdit()
                self.table.setCellWidget(index, i, widget)
                widget.textChanged.connect(partial(self.update_data, index, i, widget.text()))
            elif i == 3:
                widget = QComboBox()
                widget.addItems(["Normal", "Log"])
                self.table.setCellWidget(index, i, widget)
                widget.currentIndexChanged.connect(partial(self.update_data, index, i, widget.currentText()))
            elif i == 4:
                widget = QCheckBox()
                self.table.setCellWidget(index, i, widget)
                widget.stateChanged.connect(partial(self.update_data, index, i, widget.isChecked()))
            elif i == 5:
                widget = QSpinBox()
                self.table.setCellWidget(index, i, widget)
                widget.valueChanged.connect(partial(self.update_data, index, i, widget.value()))

        self.data.append(
            RangeAxisList(
                [self.get_cell_widget_value(self.table.cellWidget(index, i)) for i in range(self.table.columnCount())]
            )
        )
        self.data[-1].set_callback(self.data_changed_callback)

    def update_data(self, index, position, value):
        self.data[index][position] = value
        if index == self.table.rowCount() - 1:
            self.add_Row(index + 1)  # Add a new row dynamically

    def get_cell_widget_value(self, widget):
        if isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, QComboBox):
            return widget.currentText()
        elif isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, QSpinBox):
            return widget.value()
        return None

    def get_range_axis_data(self):
        return self.data

    def data_changed_callback(self):
        print("Data changed!")
        self.send_data_change_signal.emit()


class CombinedAxisTables(QWidget):
    send_data_change_signal = QtCore.Signal(TimeAxisList, RangeAxisList)  # Emit both time and range axis data

    def __init__(self, parent=None):
        super(CombinedAxisTables, self).__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)

        # Create the time axis table
        self.time_axis_table = TimeAxisTable()

        # Create the range axis table
        self.range_axis_table = RangeAxisTableWidget()

        # Connect the data change signals from both tables to emit the CombinedAxisTables signal
        self.time_axis_table.send_data_change_signal.connect(self.emit_data_change_signal)
        self.range_axis_table.send_data_change_signal.connect(self.emit_data_change_signal)

        # Add both tables to the main layout
        self.main_layout.addWidget(self.time_axis_table)
        self.main_layout.addWidget(self.range_axis_table)

    def emit_data_change_signal(self):
        self.send_data_change_signal.emit(self.time_axis_table.data, self.range_axis_table.data)
