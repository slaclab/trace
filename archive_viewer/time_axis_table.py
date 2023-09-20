import os
import epics
import copy
import pandas as pd
import typing
from functools import partial
from datetime import datetime
from qtpy import QtCore, QtGui, QtWidgets
from pydm.widgets import PyDMLineEdit
from qtpy import QtCore, QtGui
from qtpy.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QTabWidget, QGroupBox,
    QScrollArea, QSizePolicy, QPushButton, QCheckBox, QColorDialog, QComboBox, QSlider,
    QLineEdit, QSpacerItem, QTableWidget, QTableWidgetItem, QCalendarWidget, QSpinBox, QDialog, QVBoxLayout, QHeaderView, QToolButton,
    QDateTimeEdit, QPushButton
)
from qtpy.QtCore import QDate, QDateTime
from archive_search import ArchiveSearchWidget
from collections.abc import MutableSequence



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


class TimeAxisTable(QWidget):
    
    send_data_change_signal = QtCore.Signal(TimeAxisList)

    def __init__(self):
        super(TimeAxisTable, self).__init__()
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)

        labels = ["Main Time Axis", None, None]  # Labels for each column

        row_layout = QHBoxLayout()

        # Initialize the TimeAxisList with placeholders
        initial_data = [None] * len(labels)
        self.data = TimeAxisList(initial_data)
        self.data.set_callback(self.data_changed_callback)

        for i, label in enumerate(labels):
            if label is None:
                if i == 1 or i == 2:
                    widget = QDateTimeEdit()
                    widget.setDisplayFormat("MM/dd/yyyy hh:mm:ss.zzz")
                    widget.setCalendarPopup(True)
                    widget.setDateTime(QDateTime.currentDateTime())
                    widget.dateTimeChanged.connect(
                        partial(
                            self.update_data,
                            i,
                            widget,
                        )
                    )
                    row_layout.addWidget(widget)
            else:
                label_widget = QLabel(label)
                row_layout.addWidget(label_widget)

        self.main_layout.addLayout(row_layout)

    def update_data(self, position, widget):
        if isinstance(widget, QDateTimeEdit):
            if position == 1:
                new_value = widget.dateTime().toPyDateTime()
                print(f"Updating data at position 1: {new_value}")
                self.data[1] = new_value
            elif position == 2:
                new_value = widget.dateTime().toPyDateTime()
                print(f"Updating data at position 2: {new_value}")
                self.data[2] = new_value
        self.send_data_change_signal.emit(self.data)

    def data_changed_callback(self):
        print("Data changed!")
        self.send_data_change_signal.emit(self.data)

    def update_data(self, position, widget):
        if isinstance(widget, QDateTimeEdit):
            if position == 1:
                new_value = widget.dateTime().toPyDateTime()
                print(f"Updating data at position 1: {new_value}")
                self.data[1] = new_value
            elif position == 2:
                new_value = widget.dateTime().toPyDateTime()
                print(f"Updating data at position 2: {new_value}")
                self.data[2] = new_value
        elif isinstance(widget, QSlider):
            new_value = widget.value()
            print(f"Updating data at position 3: {new_value}")
            self.data[3] = new_value
        self.send_data_change_signal.emit(self.data)

    def data_changed_callback(self):
        print("Data changed!")
        self.send_data_change_signal.emit(self.data)
