import os
import subprocess
from socket import gethostname
from getpass import getuser

from qtpy.QtGui import QFont
from qtpy.QtCore import Qt, QSize
from qtpy.QtWidgets import (
    QLabel,
    QWidget,
    QLineEdit,
    QSplitter,
    QTreeView,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QApplication,
    QButtonGroup,
)

from pydm import Display
from pydm.widgets import PyDMLabel, PyDMArchiverTimePlot

from config import datetime_pv


class TraceDisplay(Display):
    def __init__(self, parent=None, args=None, macros=None) -> None:
        super(TraceDisplay, self).__init__(parent=parent, args=args, macros=macros, ui_filename=None)
        self.build_ui()
        self.setup_ui()
        self.configure_app()
        self.resize(1100, 700)

    def minimumSizeHint(self):
        return QSize(700, 350)

    def build_ui(self) -> None:
        # Set window title
        self.setWindowTitle("Trace")
        # Create main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create the plotting and control widgets
        plot_side_widget = self.build_plot_side(self)
        control_side_widget = self.build_control_side(self)

        # Create main splitter
        main_splitter = QSplitter(self)
        main_splitter.addWidget(plot_side_widget)
        main_splitter.addWidget(control_side_widget)
        main_splitter.setSizes([1, 300])
        main_splitter.setCollapsible(0, False)
        main_splitter.setStretchFactor(0, 1)
        main_layout.addWidget(main_splitter)

        # Create the footer section of the app
        footer_widget = self.build_footer(self)
        main_layout.addWidget(footer_widget)

    def build_plot_side(self, parent):
        plot_side_widget = QWidget(parent)
        plot_side_layout = QVBoxLayout()
        plot_side_widget.setLayout(plot_side_layout)

        toolbar = self.build_toolbar(plot_side_widget)
        plot_side_layout.addLayout(toolbar)

        # Create plot
        self.main_plot = PyDMArchiverTimePlot(plot_side_widget, background="white", optimized_data_bins=5000)
        plot_side_layout.addWidget(self.main_plot)

        return plot_side_widget

    def build_toolbar(self, parent):
        toolbar_widget = QWidget(parent)
        # Create tool layout
        tool_layout = QHBoxLayout()
        save_image_button = QPushButton("Save Image", toolbar_widget)
        tool_layout.addWidget(save_image_button)
        logger_button = QPushButton("Logger", toolbar_widget)
        tool_layout.addWidget(logger_button)
        tool_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        tool_layout.addSpacerItem(tool_spacer)
        timespan_buttons = self.build_timespan_buttons(toolbar_widget)
        tool_layout.addWidget(timespan_buttons)
        data_insight_tool_button = QPushButton("Data Insight Tool", toolbar_widget)
        tool_layout.addWidget(data_insight_tool_button)

        return toolbar_widget

    def build_timespan_buttons(self, parent: QWidget):
        timespan_button_widget = QWidget(parent)
        timespan_button_layout = QHBoxLayout()
        timespan_button_layout.setContentsMargins(0, 0, 0, 0)
        timespan_button_widget.setLayout(timespan_button_layout)

        self.min_scale_btn = QPushButton("1m", timespan_button_widget)
        self.min_scale_btn.setMaximumWidth(40)
        self.min_scale_btn.setCheckable(True)
        timespan_button_layout.addWidget(self.min_scale_btn)

        self.hour_scale_btn = QPushButton("1h", timespan_button_widget)
        self.hour_scale_btn.setMaximumWidth(40)
        self.hour_scale_btn.setCheckable(True)
        self.hour_scale_btn.setChecked(True)
        timespan_button_layout.addWidget(self.hour_scale_btn)

        self.day_scale_btn = QPushButton("1d", timespan_button_widget)
        self.day_scale_btn.setMaximumWidth(40)
        self.day_scale_btn.setCheckable(True)
        timespan_button_layout.addWidget(self.day_scale_btn)

        self.week_scale_btn = QPushButton("1w", timespan_button_widget)
        self.week_scale_btn.setMaximumWidth(40)
        self.week_scale_btn.setCheckable(True)
        timespan_button_layout.addWidget(self.week_scale_btn)

        self.month_scale_btn = QPushButton("1M", timespan_button_widget)
        self.month_scale_btn.setMaximumWidth(40)
        self.month_scale_btn.setCheckable(True)
        timespan_button_layout.addWidget(self.month_scale_btn)

        # Create timespan button group
        timespan_buttons = QButtonGroup(timespan_button_widget)
        timespan_buttons.setExclusive(True)
        timespan_buttons.addButton(self.min_scale_btn)
        timespan_buttons.addButton(self.hour_scale_btn)
        timespan_buttons.addButton(self.day_scale_btn)
        timespan_buttons.addButton(self.week_scale_btn)
        timespan_buttons.addButton(self.month_scale_btn)

        return timespan_button_widget

    def build_control_side(self, parent):
        # Create right layout
        control_side_widget = QWidget(parent)
        control_side_layout = QVBoxLayout()
        control_side_widget.setLayout(control_side_layout)

        # Create pv plotter layout
        pv_plotter_layout = QHBoxLayout()
        control_side_layout.addLayout(pv_plotter_layout)
        pv_line_edit = QLineEdit("Enter PV", control_side_widget)
        pv_plotter_layout.addWidget(pv_line_edit)
        pv_plot_button = QPushButton("Plot", control_side_widget)
        pv_plotter_layout.addWidget(pv_plot_button)

        # Create axis & curve view
        axis_view = QTreeView(control_side_widget)
        control_side_layout.addWidget(axis_view)
        new_axis_button = QPushButton("New Axis", control_side_widget)
        control_side_layout.addWidget(new_axis_button)

        return control_side_widget

    def build_footer(self, parent: QWidget):
        label_font = QFont()
        label_font.setPointSize(8)

        footer_widget = QWidget(parent)
        # footer_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        footer_widget.setFixedHeight(12)
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_widget.setLayout(footer_layout)

        self.version_label = QLabel("<version_tag>", footer_widget)
        self.version_label.setFont(label_font)
        self.version_label.setToolTip("Trace Version")
        self.version_label.setAlignment(Qt.AlignBottom)
        footer_layout.addWidget(self.version_label)
        footer_layout.addWidget(BreakerLabel(footer_widget))

        self.node_label = QLabel("<node_name>", footer_widget)
        self.node_label.setFont(label_font)
        self.node_label.setToolTip("Node Name")
        self.node_label.setAlignment(Qt.AlignBottom)
        footer_layout.addWidget(self.node_label)
        footer_layout.addWidget(BreakerLabel(footer_widget))

        self.user_label = QLabel("<user>", footer_widget)
        self.user_label.setFont(label_font)
        self.user_label.setToolTip("User Name")
        self.user_label.setAlignment(Qt.AlignBottom)
        footer_layout.addWidget(self.user_label)
        footer_layout.addWidget(BreakerLabel(footer_widget))

        self.pid_label = QLabel("<PID>", footer_widget)
        self.pid_label.setFont(label_font)
        self.pid_label.setToolTip("PID")
        self.pid_label.setAlignment(Qt.AlignBottom)
        footer_layout.addWidget(self.pid_label)
        footer_layout.addWidget(BreakerLabel(footer_widget))

        self.url_label = QLabel("<PYDM_ARCHIVER_URL>", footer_widget)
        self.url_label.setFont(label_font)
        self.url_label.setToolTip("Archiver URL")
        self.url_label.setAlignment(Qt.AlignBottom)
        footer_layout.addWidget(self.url_label)

        footer_spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        footer_layout.addSpacerItem(footer_spacer)

        self.time_label = PyDMLabel(footer_widget, f"ca://{datetime_pv}")
        self.time_label.setAlignment(Qt.AlignBottom)
        footer_layout.addWidget(self.time_label)

        return footer_widget

    def setup_ui(self):
        self.setup_footer()

    def setup_footer(self):
        """Set footer information for application. Includes logging, nodename,
        username, PID, git version, Archiver URL, and current datetime
        """
        self.version_label.setText(self.git_version())
        self.node_label.setText(gethostname())
        self.user_label.setText(getuser())
        self.pid_label.setText(str(os.getpid()))
        self.url_label.setText(os.getenv("PYDM_ARCHIVER_URL"))

    def configure_app(self):
        """UI changes to be made to the PyDMApplication"""
        app = QApplication.instance()
        if not app.main_window:
            return

        # Hide navigation bar by default (can be shown in menu bar)
        app.main_window.toggle_nav_bar(False)
        app.main_window.ui.actionShow_Navigation_Bar.setChecked(False)

        # Hide status bar by default (can be shown in menu bar)
        app.main_window.toggle_status_bar(False)
        app.main_window.ui.actionShow_Status_Bar.setChecked(False)

    @staticmethod
    def git_version():
        """Get the current git tag for the project"""
        project_directory = __file__.rsplit("/", 1)[0]
        git_cmd = subprocess.run(
            f"cd {project_directory} && git describe --tags", text=True, shell=True, capture_output=True
        )
        return git_cmd.stdout.strip()


class BreakerLabel(QLabel):
    breaker_font = QFont()
    breaker_font.setBold(True)
    breaker_font.setPointSize(12)

    def __init__(self, parent):
        super().__init__(parent)
        self.setText("|")
        self.setFont(self.breaker_font)
        self.setAlignment(Qt.AlignBottom)
