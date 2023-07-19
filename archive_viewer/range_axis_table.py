import os
import epics
import copy
import pandas as pd
import typing
from functools import partial
from datetime import datetime
from qtpy import QtCore, QtGui
from qtpy.QtGui import QIcon
from pydm.widgets import PyDMLineEdit
from qtpy.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QTabWidget, QGroupBox,
                            QScrollArea, QSizePolicy, QPushButton, QCheckBox, QColorDialog, QComboBox, QSlider,
                            QLineEdit, QSpacerItem, QTableWidget, QTableWidgetItem, QCalendarWidget, QSpinBox, QDialog, QVBoxLayout, QHeaderView, QToolButton)
from qtpy.QtCore import Qt, QSize


from collections.abc import MutableSequence



class RangeAxisTableWidget(QWidget):
    def __init__(self, parent=None):
        super(RangeAxisTableWidget, self).__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["AXIS NAME", "MAX", "MIN", "TYPE", "KEEP RANGES", "POSITION"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.main_layout.addWidget(self.table)

        self.add_Row(0)

    def add_Row(self, index):
        current_row_count = self.table.rowCount()
        self.table.insertRow(current_row_count)

        for i in range(self.table.columnCount()):
            if i == 0:
                widget = QLineEdit()
                self.table.setCellWidget(index, i, widget)
            elif i in [1, 2]:
                widget = QLineEdit()
                self.table.setCellWidget(index, i, widget)
            elif i == 3:
                widget = QComboBox()
                widget.addItems(["Normal", "Log"])
                self.table.setCellWidget(index, i, widget)
            elif i == 4:
                widget = QCheckBox()
                self.table.setCellWidget(index, i, widget)
            elif i == 5:
                widget = QSpinBox()
                self.table.setCellWidget(index, i, widget)

    def get_range_axis_data(self):
        axis_data = []
        for row in range(self.table.rowCount()):
            axis_name = self.get_cell_widget_value(self.table.cellWidget(row, 0))
            max_value = self.get_cell_widget_value(self.table.cellWidget(row, 1))
            min_value = self.get_cell_widget_value(self.table.cellWidget(row, 2))
            axis_type = self.get_cell_widget_value(self.table.cellWidget(row, 3))
            keep_ranges = self.get_cell_widget_value(self.table.cellWidget(row, 4))
            position = self.get_cell_widget_value(self.table.cellWidget(row, 5))
            axis_data.append((axis_name, max_value, min_value, axis_type, keep_ranges, position))
        return axis_data

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

class RangeAxisList(MutableSequence):
    def __init__(self, iterable=()):
        self._list = list(iterable)
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
        # trigger change handler
        if self.callback:
            self.callback()

    def __len__(self):
        return self._list.__len__()

    def insert(self, index, item):
        self._list.insert(index, item)
        # trigger change handler
        if self.callback:
            self.callback()

    def set_callback(self, callback):
        self.callback = callback

