import typing
import numpy as np 
from numpy import sin 
from pydm import Display
from qtpy import QtCore
from qtpy.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QTabWidget, QGroupBox,
                            QScrollArea, QSizePolicy, QPushButton, QCheckBox, QColorDialog, QComboBox, QSlider,
                            QLineEdit, QSpacerItem, QTableWidget, QTableWidgetItem, QCalendarWidget, QSpinBox)
from pydm.widgets import PyDMArchiverTimePlot, PyDMWaveformPlot
from pv_table import PyDMPVTable
from time_axis_table import TimeAxisTable
from range_axis_table import RangeAxisTableWidget
from functools import partial
#from qdarkstyle import load_stylesheet, DarkPalette
from archive_search import ArchiveSearchWidget
from pydm import Display
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QTabWidget, QWidget
from pv_table import PyDMPVTable


class ArchiveViewerLogic:
    def __init__(self, archive_viewer):
        self.archive_viewer = archive_viewer

    def update_time_axes_options(self, time_axes):
        self.archive_viewer.time_axes = time_axes
        self.archive_viewer.input_table.set_time_axes(time_axes)

    def update_plot(self):
        if self.archive_viewer.input_table is None:
            return

        self.archive_viewer.time_plots.clearCurves()  # Clear existing curves

        # Fetch data from the table
        rows = self.archive_viewer.input_table.table.rowCount()
        for row_index in range(rows):
            try:
                pv_name_widget = self.archive_viewer.input_table.table.cellWidget(row_index, 0)
                line_width_widget = self.archive_viewer.input_table.table.cellWidget(row_index, 7)
                if pv_name_widget is None or line_width_widget is None:
                    continue

                pv_name = pv_name_widget.text()
                line_width = int(line_width_widget.value())

                # Check if required information is present
                if pv_name and line_width:
                    # Add the PV as a y-channel to the time plot
                    self.archive_viewer.time_plots.addYChannel(
                        y_channel=f"archiver://{pv_name}",
                        lineWidth=line_width,
                        symbol='o',
                        useArchiveData=True
                    )
                else:
                    print(f"Skipping row {row_index + 1} due to missing information.")
            except Exception as e:
                print(f"Error processing row {row_index + 1}: {str(e)}")



class ArchiveViewer(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(ArchiveViewer, self).__init__(parent=parent, args=args, macros=macros)
        self.app = QApplication.instance()
        self.setWindowTitle("New Archive Viewer")
        self.archive_search_widget = ArchiveSearchWidget()
        self.time_axes = []  # Array to store the time axes
        self.logic = ArchiveViewerLogic(self)
        self.setup_ui()

    def fetch_data_from_table(self):
        columns = self.input_table.table.columnCount()
        rows = self.input_table.table.rowCount()

        for row_index in range(rows):
            for column_index in range(columns):
                if column_index == 0:
                    print(self.input_table.table.cellWidget(row_index, column_index).text())

    # def update_plot(self):
    #     if self.input_table is None:
    #         return

    #     self.time_plots.clearCurves()  # Clear existing curves

    #     # Fetch data from the table
    #     rows = self.input_table.table.rowCount()
    #     for row_index in range(rows):
    #         try:
    #             pv_name_widget = self.input_table.table.cellWidget(row_index, 0)
    #             line_width_widget = self.input_table.table.cellWidget(row_index, 7)
    #             if pv_name_widget is None or line_width_widget is None:
    #                 continue

    #             pv_name = pv_name_widget.text()
    #             line_width = int(line_width_widget.value())

    #             # Check if required information is present
    #             if pv_name and line_width:
    #                 # Add the PV as a y-channel to the time plot
    #                 self.time_plots.addYChannel(
    #                     y_channel=f"archiver://{pv_name}",
    #                     lineWidth=line_width,
    #                     symbol='o',
    #                     useArchiveData=True
    #                 )
    #             else:
    #                 print(f"Skipping row {row_index + 1} due to missing information.")
    #         except Exception as e:
    #             print(f"Error processing row {row_index + 1}: {str(e)}")

    def minimumSizeHint(self):
        return QtCore.QSize(1050, 600)

    def setup_ui(self):
        # main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # plot widgets
        self.time_plots = PyDMArchiverTimePlot()
        self.waveforms = PyDMWaveformPlot()
        self.correlations = PyDMWaveformPlot()  # needs changing

        # tab widget to hold plots
        plot_tab_widget = QTabWidget()
        plot_tab_widget.addTab(self.time_plots, "Time Plots")
        plot_tab_widget.addTab(self.waveforms, "Waveforms")
        plot_tab_widget.addTab(self.correlations, "Correlations")

        # Create the PyDMPVTable widget with time_axes parameter
        self.input_table = PyDMPVTable(
            table_headers=["PV NAME", "TIME AXIS", "RANGE AXIS", "VISIBLE", "RAW", "COLOR", "TYPE", "WIDTH"],
            number_columns=8,
            col_widths=[100],
            time_axes=self.time_axes  # Pass the time_axes array as an argument
        )


        self.input_data_tab = QWidget()
        self.input_data_layout = QHBoxLayout()
        self.input_data_layout.addWidget(self.input_table)
        self.input_data_layout.setContentsMargins(0, 0, 0, 0)

        # Range Menu
        range_tab = QWidget()

        # Create the range axis table widget
        range_table_widget = RangeAxisTableWidget()

        # Create the main layout
        range_layout = QVBoxLayout()
        range_layout.addWidget(range_table_widget)

        # time Menu
        time_tab = QWidget()

        # Create the time menu widget
        time_axes = []  # Create an empty array to store the time axes

        time_menu_widget = TimeAxisTable(self.time_axes)  # Pass the time_axes array as an argument
        self.logic.update_time_axes_options(time_menu_widget.time_axes)  # Update time axes options



        # Add the time menu widget to the layout
        time_layout = QVBoxLayout()
        time_layout.addWidget(time_menu_widget)

        self.input_data_tab.setLayout(self.input_data_layout)
        range_tab.setLayout(range_layout)
        time_tab.setLayout(time_layout)

        self.settings_tab_widget = QTabWidget()
        self.settings_tab_widget.addTab(self.input_data_tab, "Input Data")
        self.settings_tab_widget.addTab(range_tab, "Range")
        self.settings_tab_widget.addTab(time_tab, "Time Axis")

        # set up time toggle buttons
        self.time_toggle_buttons = []
        time_toggle_layout = QHBoxLayout()

        # horizontal spacer for toggle buttons
        horizontal_spacer = QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        time_toggle_layout.addItem(horizontal_spacer)

        self.time_toggle = [('30s', None), ('1m', None), ('1h', None), ('1w', None), ('1m', None)]
        for index in range(len(self.time_toggle)):
            self.time_toggle_buttons.append(QPushButton(self.time_toggle[index][0], self))
            self.time_toggle_buttons[index].setGeometry(200, 150, 100, 40)
            self.time_toggle_buttons[index].setCheckable(True)
            self.time_toggle_buttons[index].clicked.connect(partial(self.time_toggle_button_action, index))
            time_toggle_layout.addWidget(self.time_toggle_buttons[index])

        # set up misc toggle buttons
        self.misc_button = []
        misc_toggle_layout = QHBoxLayout()

        self.misc_toggle = [('curser', None), ('Y axis autoscale', None), ('Live', None)]
        for index in range(len(self.misc_toggle)):
            self.misc_button.append(QPushButton(self.misc_toggle[index][0], self))
            self.misc_button[index].setGeometry(200, 150, 100, 40)
            self.misc_button[index].setCheckable(True)
            self.misc_button[index].clicked.connect(partial(self.misc_toggle_button_action, index))
            misc_toggle_layout.addWidget(self.misc_button[index])

        time_misc_boxes_layout = QHBoxLayout()
        time_misc_boxes_layout.addLayout(time_toggle_layout)
        time_misc_boxes_layout.addLayout(misc_toggle_layout)

        main_layout.addLayout(time_misc_boxes_layout)
        main_layout.addWidget(plot_tab_widget)
        main_layout.addWidget(self.settings_tab_widget)

        self.input_table.send_data_change_signal.connect(self.logic.update_plot)

    def time_toggle_button_action(self, index):
        for i in range(len(self.time_toggle_buttons)):
            if i != index:
                self.time_toggle_buttons[i].setChecked(False)

    def misc_toggle_button_action(self, index):
        pass


# class ArchivedPV:
#     def __init__(self, pv_name):
#         self.pv_name = pv_name
#         self.range_of_times = ""
#         self.color = ""
#         self.archived_data = {}

#     def update_data(self, from_time, to_time):
#         data = self.get_pv_data(self.pv_name, from_time, to_time)
#         self.archived_data = data

#     def get_pv_data(self, pv_name, from_time, to_time):
#         pv_data = epics.caget(pv_name, starttime=from_time, endtime=to_time)
#         timestamps = pv_data['time']
#         values = pv_data['value']
#         data = {"timestamps": timestamps, "values": values}
#         return data




# class ArchiveViewerLogic:
#     def __init__(self):
#         self.archived_pvs = {}


#     def add_pv(self, pv_name):
#         archived_pv = ArchivedPV(pv_name, self.time_axes)  # Pass the time axes array
#         self.archived_pvs.append(archived_pv)

#     def remove_pv(self, pv_name):
#         if pv_name in self.archived_pvs:
#             del self.archived_pvs[pv_name]

#     def get_pv_data(self, pv_name, from_time, to_time):
#         archived_pv = self.archived_pvs.get(pv_name)
#         if archived_pv:
#             archived_pv.update_data(from_time, to_time)
#             return archived_pv.archived_data
#         return {}




# class ArchiveViewer(Display):
#     """
#     PyDM version of the Archive Viewer.
#     """


#     def __init__(self, parent=None, args=None, macros=None):
#         super(ArchiveViewer, self).__init__(parent=parent, args=args, macros=macros)
#         self.app = QApplication.instance()
#         # self.app.setStyleSheet(load_stylesheet(palette=DarkPalette))
#         self.time_axes = []  # Array to store the time axes
#         self.setWindowTitle("New Archive Viewer")
#         self.archive_search_widget = ArchiveSearchWidget()
#         self.setup_ui()

#     def fetch_data_from_table(self):
#         columns = self.input_table.table.columnCount()
#         rows = self.input_table.table.rowCount()

#         print(self.input_table.data[0]())
#         print(rows, columns)

#         for row_index in range(0, rows):
#             for column_index in range(0, columns):
#                 print(row_index, column_index)
#                 #print(self.input_table.table.cellWidget(row_index, column_index))

#                 if column_index == 0:
#                     print(self.input_table.table.cellWidget(row_index, column_index).text)

#     def update_plot(self):
#         if self.input_table is None:
#             return

#         self.time_plots.clearCurves()  # Clear existing curves

#         # Fetch data from the table
#         rows = self.input_table.table.rowCount()
#         for row_index in range(rows):
#             try:
#                 pv_name_widget = self.input_table.table.cellWidget(row_index, 0)
#                 line_width_widget = self.input_table.table.cellWidget(row_index, 7)
#                 if pv_name_widget is None or line_width_widget is None:
#                     continue

#                 pv_name = pv_name_widget.text()
#                 line_width = int(line_width_widget.text())

#                 # Check if required information is present
#                 if pv_name and line_width:
#                     # Add the PV as a y-channel to the time plot
#                     self.time_plots.addYChannel(
#                         y_channel=f"archiver://{pv_name}",
#                         lineWidth=line_width
#                     )
#                 else:
#                     print(f"Skipping row {row_index + 1} due to missing information.")
#             except Exception as e:
#                 print(f"Error processing row {row_index + 1}: {str(e)}")


#         '''
#         color=self.input_table.data[index][5],

#         lineStyle=self.input_table.data[index][6],

#         self.input_table.data[index][2](),
#         self.input_table.data[index][3](),
#         self.input_table.data[index][4]()
#         '''

#     def minimumSizeHint(self):
#         """

#         """
#         return QtCore.QSize(1050, 600)

    
#     # def populate_time_axes_options(self):
#     #     if isinstance(self.input_table, PyDMPVTable):
#     #         if self.time_axes:
#     #             self.input_table.set_time_axes(self.time_axes)

#     def setup_ui(self):
#         """

#         """
#         # main layout
#         main_layout = QVBoxLayout()
#         self.setLayout(main_layout)

#         # plot widgets
#         self.time_plots = PyDMArchiverTimePlot()
    

#         self.waveforms = PyDMWaveformPlot()
#         self.correlations = PyDMWaveformPlot()  # needs changing

#         # tab widget to hold plots
#         plot_tab_widget = QTabWidget()
#         plot_tab_widget.addTab(self.time_plots, "Time Plots")
#         plot_tab_widget.addTab(self.waveforms, "Waveforms")
#         plot_tab_widget.addTab(self.correlations, "Correlations")



#         # Create the PyDMPVTable widget 
#         self.input_table = PyDMPVTable(
#             table_headers=["PV NAME", "TIME AXIS", "RANGE AXIS", "VISIBLE", "RAW", "COLOR", "TYPE", "WIDTH"],
#             number_columns=8,
#             col_widths=[100],
#         )

        
#         self.input_data_tab = QWidget()
#         self.input_data_layout = QHBoxLayout()
#         self.input_data_layout.addWidget(self.input_table)
#         self.input_data_layout.setContentsMargins(0, 0, 0, 0)

#         # Range Menu
#         range_tab = QWidget()

#         # Create the range axis table widget
#         range_table_widget = RangeAxisTableWidget()

#         # Create the main layout
#         range_layout = QVBoxLayout()
#         range_layout.addWidget(range_table_widget)

#         # time Menu
#         time_tab = QWidget()

#         # Create the time menu widget
#         time_axes = []  # Create an empty array to store the time axes
#         time_menu_widget = TimeAxisTable(self.time_axes)  # Pass the time_axes array as an argument


#         # Add the time menu widget to the layout
#         time_layout = QVBoxLayout()
#         time_layout.addWidget(time_menu_widget)

        
#         self.input_data_tab.setLayout(self.input_data_layout)
#         range_tab.setLayout(range_layout)
#         time_tab.setLayout(time_layout)


#         self.settings_tab_widget = QTabWidget()
#         self.settings_tab_widget.addTab(self.input_data_tab, "Input Data")
#         self.settings_tab_widget.addTab(range_tab, "Range")
#         self.settings_tab_widget.addTab(time_tab, "Time Axis")
        

#         #set up time toggle buttons 
#         self.time_toggle_buttons = []
#         time_toggle_layout = QHBoxLayout()

#         #horizontal spacer for toggle buttons
#         horizontal_spacer = QSpacerItem(100, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
#         time_toggle_layout.addItem(horizontal_spacer)

#         self.time_toggle = [('30s', None), ('1m', None), ('1h', None), ('1w', None), ('1m', None)]
#         for index in range(0, len(self.time_toggle)):
#             self.time_toggle_buttons.append(QPushButton(self.time_toggle[index][0], self))
#             self.time_toggle_buttons[index].setGeometry(200, 150, 100, 40)
#             self.time_toggle_buttons[index].setCheckable(True)
#             self.time_toggle_buttons[index].clicked.connect(partial(self.time_toggle_button_action, index))
#             time_toggle_layout.addWidget(self.time_toggle_buttons[index])

#         #set up misc toggle buttons 
#         self.misc_button = []
#         misc_toggle_layout = QHBoxLayout()

#         self.misc_toggle = [('curser', None), ('Y axis autoscale', None), ('Live', None)]
#         for index in range(0, len(self.misc_toggle)):
#             self.misc_button.append(QPushButton(self.misc_toggle[index][0], self))
#             self.misc_button[index].setGeometry(200, 150, 100, 40)
#             self.misc_button[index].setCheckable(True)
#             self.misc_button[index].clicked.connect(partial(self.misc_toggle_button_action, index))
#             misc_toggle_layout.addWidget(self.misc_button[index])

#         time_misc_boxes_layout = QHBoxLayout()
#         time_misc_boxes_layout.addLayout(time_toggle_layout)
#         time_misc_boxes_layout.addLayout(misc_toggle_layout)

#         main_layout.addLayout(time_misc_boxes_layout)
#         main_layout.addWidget(plot_tab_widget)
#         main_layout.addWidget(self.settings_tab_widget)

#         self.input_table.send_data_change_signal.connect(self.update_plot)

#     def time_toggle_button_action(self, index):            
#         for i in range(0, len(self.time_toggle_buttons)):
#             if i != index: 
#                 self.time_toggle_buttons[i].setChecked(False)

#         #self.time_toggle[index][1]
    
#     def misc_toggle_button_action(self, index):            
#         pass

#         # self.misc_toggle[index][1]


    
