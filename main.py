from pydm import Display

from qtpy import QtCore
from qtpy.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QTabWidget, QGroupBox,
                            QScrollArea, QSizePolicy, QPushButton, QCheckBox, QColorDialog, QComboBox, QSlider,
                            QLineEdit)
from pydm.widgets import PyDMLabel, PyDMLineEdit, PyDMArchiverTimePlot, PyDMWaveformPlot
from pvTable import PyDMPVTable


class ArchiveViewer(Display):
    """
    PyDM version of the Archive Viewer.
    """
    def __init__(self, parent=None, args=None, macros=None):
        super(ArchiveViewer, self).__init__(parent=parent, args=args, macros=macros)
        self.app = QApplication.instance()
        self.setup_ui()

    def minimumSizeHint(self):
        """

        """
        return QtCore.QSize(1050, 600)

    def setup_ui(self):
        """

        """
        # main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # plot widgets
        time_plots = PyDMArchiverTimePlot()
        waveforms = PyDMWaveformPlot()
        correlations = PyDMWaveformPlot()  # needs changing

        # tab widget to hold plots
        plot_tab_widget = QTabWidget()
        plot_tab_widget.addTab(time_plots, "Time Plots")
        plot_tab_widget.addTab(waveforms, "Waveforms")
        plot_tab_widget.addTab(correlations, "Correlations")
        #plot_tab_widget.setLayoutDirection(QtCore.Qt.RightToLeft)

        # layout to hold the input and plot settings containers
        settings_boxes_layout = QHBoxLayout()

        # containers for the input data and the
        plot_settings_box = QGroupBox("Archive Plot Settings")
        plot_input_box = QGroupBox("Archive Plot Input Data")
        # plot_input_box.setContentsMargins(0, 0, 0, 0)
        # plot_settings_box.setContentsMargins(0, 0, 0, 0)
        plot_input_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        settings_boxes_layout.addWidget(plot_settings_box)
        settings_boxes_layout.addWidget(plot_input_box, 1)

        # Range Menu
        min_label = QLabel("Min")
        max_label = QLabel("Max")
        min_input = QLineEdit()
        max_input = QLineEdit()
        keep_range_label = QLabel("Keep Ranges")
        keep_range_check_box = QCheckBox()
        type_lable = QLabel("Type")

        range_tab = QWidget()
        range_layout = QGridLayout()
        range_layout.addWidget(min_label)
        range_layout.addWidget(min_input,  0, 1)
        range_layout.addWidget(max_label)
        range_layout.addWidget(max_input,  1, 1)
        range_layout.addWidget(keep_range_label)
        range_layout.addWidget(keep_range_check_box)
        range_layout.addWidget(type_lable, 1, 2)

        range_tab.setLayout(range_layout)
        settings_tab_widget = QTabWidget()
        settings_tab_widget.addTab(range_tab, "Range")
        #settings_tab_widget.addTab(max_label, "Time Axis")

        plot_setting_box_layout = QVBoxLayout()
        plot_setting_box_layout.addWidget(settings_tab_widget)
        plot_settings_box.setLayout(plot_setting_box_layout)

        #data_scroll_area = QScrollArea()
        input_table = PyDMPVTable(
            table_headers=["PV NAME", "TIME AXIS", "RANGE AXIS", "VISIBLE", "RAW", "COLOR", "TYPE", "WIDTH"],
            number_columns=8,
            col_widths=[100],
            widget_list=[PyDMLineEdit(), QComboBox(),
                         QComboBox(), QCheckBox(),
                         QCheckBox(), QPushButton(),
                         QComboBox(), QSlider(orientation=QtCore.Qt.Horizontal)])
        input_data_box_layout = QHBoxLayout()
        input_data_box_layout.addWidget(input_table)
        input_data_box_layout.setContentsMargins(0, 0, 0, 0)

        plot_input_box.setLayout(input_data_box_layout)
        main_layout.addWidget(plot_tab_widget)
        main_layout.addLayout(settings_boxes_layout)