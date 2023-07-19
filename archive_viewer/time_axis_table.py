import os
import epics
import copy
import pandas as pd
import typing
from functools import partial
from datetime import datetime
from PyQt5 import QtCore, QtGui, QtWidgets
from pydm.widgets import PyDMLineEdit
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from qtpy import QtCore, QtGui
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QTabWidget, QGroupBox,
    QScrollArea, QSizePolicy, QPushButton, QCheckBox, QColorDialog, QComboBox, QSlider,
    QLineEdit, QSpacerItem, QTableWidget, QTableWidgetItem, QCalendarWidget, QSpinBox, QDialog, QVBoxLayout, QHeaderView, QToolButton,
    QDateTimeEdit, QPushButton
)
from archive_search import ArchiveSearchWidget
from collections.abc import MutableSequence


class TimeAxisTable(QWidget):
    

    send_data_change_signal = QtCore.Signal()

    def __init__(self, time_axes):
        super(TimeAxisTable, self).__init__()
        self.data = TimeAxisList()
        self.data.set_callback(self.data_changed_callback) 
        self.table_headers = ["AXIS NAME", "START", "END", "SLIDER"]
        self.number_columns = len(self.table_headers)
        self.max_rows = 1
        self.col_widths = [200, 200, 200, 200]
        self.setup_ui()
        self.time_axes = time_axes  # Store the reference to the time axes list


    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.table.setColumnCount(self.number_columns)
        self.table.setHorizontalHeaderLabels(self.table_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.main_layout.addWidget(self.table)

        self.add_Row(0)

    def add_Row(self, index):
        current_row_count = self.table.rowCount()
        self.table.insertRow(current_row_count)

        for i in range(self.table.columnCount()):
            if i == 0:
                widget = QLineEdit()
                self.table.setCellWidget(index, i, widget)
                widget.textChanged.connect(
                    partial(self.update_data, index, i, widget.text())
                )
            elif i in [1, 2]:
                widget = QDateTimeEdit()
                widget.setDisplayFormat("MM/dd/yyyy hh:mm:ss.zzz")
                widget.setCalendarPopup(True)
                self.table.setCellWidget(index, i, widget)
                widget.dateTimeChanged.connect(
                    partial(
                        self.update_data,
                        index,
                        i,
                        widget.dateTime().toPyDateTime(),
                    )
                )
            elif i == 3:
                widget = QSlider(Qt.Horizontal)
                self.table.setCellWidget(index, i, widget)
                widget.valueChanged.connect(
                    partial(self.update_data, index, i, widget.value())
                )

        self.data.append(TimeAxisList(
            [
                self.get_cell_widget_value(self.table.cellWidget(index, i))
                for i in range(self.table.columnCount())
            ]
        ))


        self.data[-1].set_callback(self.data_changed_callback)

    def update_data(self, index, position, value):
        self.data[index][position] = value
        if index == self.table.rowCount() - 1:
            self.add_Row(index + 1)  # Add a new row dynamically

    def get_cell_widget_value(self, widget):
        if isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, QDateTimeEdit):
            return widget.dateTime().toPyDateTime()
        elif isinstance(widget, QSlider):
            return widget.value()
        return None

    def get_time_data(self):
        return self.data

    def data_changed_callback(self):
        print("Data changed!")
        self.send_data_change_signal.emit()




class TimeAxisList(MutableSequence):


    def __init__(self, iterable=()):
        self._list = list(iterable)

    def __getitem__(self, key):
        return self._list.__getitem__(key)

    def __setitem__(self, key, item):
        self._list.__setitem__(key, item)
        # trigger change handler
        self.callback()

    def __delitem__(self, key):
        self._list.__delitem__(key)
        # trigger change handler
        self.callback()

    def __len__(self):
        return self._list.__len__()

    def insert(self, index, item):
        self._list.insert(index, item)
        # trigger change handler
        self.callback()
        
    def set_callback(self, callback):
        self.callback = callback



