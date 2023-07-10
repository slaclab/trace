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

class CalendarDialog(QDialog):
    def __init__(self, parent=None):
        super(CalendarDialog, self).__init__(parent)
        self.setWindowTitle("Calendar")
        self.setup_ui()

    def setup_ui(self):
        # Create the calendar widget
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.clicked.connect(self.selectDate)

        # Set layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(self.calendar_widget)
        self.setLayout(layout)

    def selectDate(self, date):
        self.selected_date = date

class TimeMenuWidget(QWidget):
    def __init__(self, parent=None):
        super(TimeMenuWidget, self).__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Create the time axis table widget
        self.time_axis_table = QTableWidget()
        self.time_axis_table.setColumnCount(6)
        self.time_axis_table.setHorizontalHeaderLabels(["AXIS NAME", "START", "END", "CALENDAR", "SLIDER", "POSITION"])

        # Set the default number of rows
        self.time_axis_table.setRowCount(1)

        # Populate the cells with widgets and data
        self.axis_name_edit = PyDMLineEdit()
        self.time_axis_table.setCellWidget(0, 0, self.axis_name_edit)

        self.start_edit = PyDMLineEdit()
        self.time_axis_table.setCellWidget(0, 1, self.start_edit)

        self.end_edit = PyDMLineEdit()
        self.time_axis_table.setCellWidget(0, 2, self.end_edit)

        calendar_widget = QCalendarWidget()
        calendar_button = QPushButton()
        calendar_button.setIcon(QIcon("/Users/fatima-osman/Downloads/calendar.png"))
        calendar_button.setIconSize(QSize(24, 24))
        calendar_button.clicked.connect(self.openCalendar)
        self.time_axis_table.setCellWidget(0, 3, calendar_button)

        slider = QSlider(Qt.Horizontal)
        self.time_axis_table.setCellWidget(0, 4, slider)

        position_spinbox = QSpinBox()
        self.time_axis_table.setCellWidget(0, 5, position_spinbox)

        # Customize the table widget
        self.time_axis_table.verticalHeader().setVisible(False)  # Hide the vertical header
        self.time_axis_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Disable cell editing
        self.time_axis_table.setSelectionMode(QTableWidget.NoSelection)  # Disable cell selection

        # # Set column widths
        # column_widths = [150, 150, 150, 100, 150, 150]
        # for i, width in enumerate(column_widths):
        #     self.time_axis_table.setColumnWidth(i, width)

        # Set layout for the widget
        layout = QHBoxLayout()
        layout.addWidget(self.time_axis_table)
        self.setLayout(layout)

    def openCalendar(self):
        dialog = CalendarDialog()
        dialog.exec_()

    def get_time_data(self):
        # Retrieve the time data from the table
        axis_name = self.axis_name_edit.text()
        start = self.start_edit.text()
        end = self.end_edit.text()
        calendar_widget = self.time_axis_table.cellWidget(0, 3)
        slider = self.time_axis_table.cellWidget(0, 4)
        position_spinbox = self.time_axis_table.cellWidget(0, 5)

        calendar_date = calendar_widget.selectedDate().toString(Qt.ISODate)
        slider_value = slider.value()
        position = position_spinbox.value()

        return axis_name, start, end, calendar_date, slider_value, position


# class MainWidget(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setupUI()

#     def setupUI(self):
#         self.table_widget = PyDMPVTable()
#         self.time_menu_widget = TimeMenuWidget()

#         layout = QVBoxLayout()
#         layout.addWidget(self.table_widget)
#         layout.addWidget(self.time_menu_widget)

#         central_widget = QWidget()
#         central_widget.setLayout(layout)
#         self.setCentralWidget(central_widget)
# # Connect the time_edit.timeChanged signal from TimeMenuWidget to a method in your PyDMPVTable class that will handle the selected time change.

# By separating the time menu table into its own QWidget, you can easily manage its functionality and appearance independently from other components. It promotes reusability and makes your code more modular and maintainable.
