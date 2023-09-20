import typing
from functools import partial
from qtpy import QtCore
from pydm import Display
from archive_search import ArchiveSearchWidget
from range_axis_table import CombinedAxisTables
from pv_table import PVTable
from pydm.widgets import PyDMArchiverTimePlot, PyDMWaveformPlot
from qtpy.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QTabWidget, QGroupBox,
                            QScrollArea, QSizePolicy, QPushButton, QCheckBox, QColorDialog, QComboBox, QSlider,
                            QLineEdit, QSpacerItem, QTableWidget, QTableWidgetItem, QCalendarWidget, QSpinBox)


class ArchiveViewer(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(ArchiveViewer, self).__init__(parent=parent, args=args, macros=macros)
        self.app = QApplication.instance()
        self.setWindowTitle("New Archive Viewer")
        self.archive_search_widget = ArchiveSearchWidget()
        self.pv_names_to_plot = set()
        self.default_line_width = .05  # Set default line width
        self.default_color = "white"  # Set default color
        self.setup_ui()

    def fetch_data_from_table(self):
        columns = self.input_table.table.columnCount()
        rows = self.input_table.table.rowCount()

        for row_index in range(rows):
            for column_index in range(columns):
                if column_index == 0:
                    print(self.input_table.table.cellWidget(row_index, column_index).text())

        # Dictionary to store the PV names for plotting
        self.pv_names_to_plot = []

    def update_plot(self):
        if self.input_table is None:
            return

        self.time_plots.clearCurves()  # Clear existing curves

        # Fetch data from the table
        rows = self.input_table.table.rowCount()
        new_pv_names = set()  # Use a set to store PV names from the current update

        for row_index in range(rows):
            try:
                pv_name_widget = self.input_table.table.cellWidget(row_index, 0)
                line_width_slider = self.input_table.table.cellWidget(row_index, 6)
                color_widget = self.input_table.table.cellWidget(row_index, 4)
                color = color_widget.palette().color(QPalette.Background).name()
                visible_checkbox = self.input_table.table.cellWidget(row_index, 2)
                is_visible = visible_checkbox.isChecked()

                if pv_name_widget is None or line_width_slider is None:
                    continue

                pv_name = pv_name_widget.text()
                line_width = line_width_slider.value() / 8.0  # Adjust line width based on slider values

                # Use the default line width if the user has not set it
                if line_width == 0:
                    line_width = self.default_line_width

                if pv_name:
                        if is_visible:
                            new_pv_names.add(pv_name)


                            # Plot the selected PV row with updated parameters
                            self.time_plots.addYChannel(
                                y_channel=f"ca://{pv_name}",
                                yAxisName="Name",
                                lineWidth=line_width,
                                color=color,
                                useArchiveData=True
                            )

                        else:
                            print(f"Skipping row {row_index + 1} due to missing information.")
            except Exception as e:
                print(f"Error processing row {row_index + 1}: {str(e)}")

        # Calculate the PV names to plot that are new since the last update
        pv_names_to_plot = new_pv_names - self.pv_names_to_plot

        # Update the set of PV names to include the new PV names (only for fully valid rows)
        self.pv_names_to_plot.update(new_pv_names)


    def update_x_axis(self, data):
        print("Update x-axis called")
        print("Received data:", data)  # Print the received data for debugging
        start_time, end_time = data[1], data[2]  # Access elements using indexing
        if start_time and end_time:
            start_timestamp = start_time.timestamp()
            end_timestamp = end_time.timestamp()
            print(f"Updating x-axis: Start={start_timestamp}, End={end_timestamp}")
            self.time_plots.setXRange(start_timestamp, end_timestamp, padding=0.0, update=True)
            self.update_plot()

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

        # Create the PVTable widget
        self.input_table = PVTable(
            table_headers=["PV NAME", "RANGE AXIS", "VISIBLE", "RAW", "COLOR", "TYPE", "WIDTH"],
            number_columns=7,
            col_widths=[100],
        )

        self.input_data_tab = QWidget()
        self.input_data_layout = QHBoxLayout()
        self.input_data_layout.addWidget(self.input_table)
        self.input_data_layout.setContentsMargins(0, 0, 0, 0)

        # Axes Menu
        self.axes_tab = QWidget()

        # Create the range and time axis table widget on same tab
        self.axes_table_widget = CombinedAxisTables()

        # Create the main layout
        self.axes_layout = QVBoxLayout()
        self.axes_layout.addWidget(self.axes_table_widget)

        self.input_data_tab.setLayout(self.input_data_layout)
        self.axes_tab.setLayout(self.axes_layout)


        self.settings_tab_widget = QTabWidget()
        self.settings_tab_widget.addTab(self.input_data_tab, "Input Data")
        self.settings_tab_widget.addTab(self.axes_tab, "Set Axes")


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

        self.input_table.send_data_change_signal.connect(self.update_plot)
        self.axes_table_widget.send_data_change_signal.connect(self.update_x_axis)

    def time_toggle_button_action(self, index):
        for i in range(len(self.time_toggle_buttons)):
            if i != index:
                self.time_toggle_buttons[i].setChecked(False)

    def misc_toggle_button_action(self, index):
        pass

    
class ArchiveViewerLogic():
    #manipulate pv data with formula
    #delete pv from everything 
    #add any new pv row info 
    #maybe set time span 
    pass

