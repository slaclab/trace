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

# class CalendarDialog(QDialog):
#     def __init__(self, parent=None):
#         super(CalendarDialog, self).__init__(parent)
#         self.setWindowTitle("Calendar")
#         self.setup_ui()

#     def setup_ui(self):
#         # Create the calendar widget
#         self.calendar_widget = QCalendarWidget()
#         self.calendar_widget.clicked.connect(self.selectDate)

#         # Set layout for the dialog
#         layout = QVBoxLayout()
#         layout.addWidget(self.calendar_widget)
#         self.setLayout(layout)

#     def selectDate(self, date):
#         self.selected_date = date

class RangeAxisTableWidget(QWidget):
    def __init__(self, parent=None):
        super(RangeAxisTableWidget, self).__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Create the range axis table widget
        self.range_axis_table = QTableWidget()
        self.range_axis_table.setColumnCount(6)
        self.range_axis_table.setHorizontalHeaderLabels(["AXIS NAME", "MAX", "MIN", "TYPE", "KEEP RANGES", "POSITION"])

        # Set the default number of rows
        self.range_axis_table.setRowCount(1)

        # Populate the cells with widgets and data
        self.axis_name_edit = PyDMLineEdit()
        self.range_axis_table.setCellWidget(0, 0, self.axis_name_edit)

        self.max_edit = PyDMLineEdit()
        self.range_axis_table.setCellWidget(0, 1, self.max_edit)

        self.min_edit = PyDMLineEdit()
        self.range_axis_table.setCellWidget(0, 2, self.min_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Type 1", "Type 2", "Type 3"])  # Replace with actual types
        self.range_axis_table.setCellWidget(0, 3, self.type_combo)

        self.keep_ranges_checkbox = QCheckBox()
        self.range_axis_table.setCellWidget(0, 4, self.keep_ranges_checkbox)

        position_spinbox = QSpinBox()
        self.range_axis_table.setCellWidget(0, 5, position_spinbox)

        # Customize the table widget
        self.range_axis_table.verticalHeader().setVisible(False)  # Hide the vertical header
        self.range_axis_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Disable cell editing
        self.range_axis_table.setSelectionMode(QTableWidget.NoSelection)  # Disable cell selection

        # Set layout for the widget
        layout = QHBoxLayout()
        layout.addWidget(self.range_axis_table)
        self.setLayout(layout)

    def get_range_axis_data(self):
        # Retrieve the range axis data from the table
        axis_name = self.axis_name_edit.text()
        max_value = self.max_edit.text()
        min_value = self.min_edit.text()
        axis_type = self.type_combo.currentText()
        keep_ranges = self.keep_ranges_checkbox.isChecked()

        return axis_name, max_value, min_value, axis_type, keep_ranges

