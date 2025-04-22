import os
import subprocess
from socket import gethostname
from getpass import getuser
from datetime import datetime

import qtawesome as qta
from qtpy.QtGui import QFont
from qtpy.QtCore import Qt, Slot, QSize
from qtpy.QtWidgets import (
    QLabel,
    QWidget,
    QLineEdit,
    QSplitter,
    QTreeView,
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QApplication,
    QButtonGroup,
)
from pyqtgraph.exporters import ImageExporter

from pydm import Display
from pydm.widgets import PyDMLabel, PyDMArchiverTimePlot

from config import logger, datetime_pv
from mixins import FileIOMixin, AxisTableMixin, PlotConfigMixin, TracesTableMixin
from widgets import DataInsightTool, PlotSettingsModal


class TraceDisplay(Display, TracesTableMixin, AxisTableMixin, FileIOMixin, PlotConfigMixin):
    def __init__(self, parent=None, args=None, macros=None) -> None:
        super(TraceDisplay, self).__init__(parent=parent, args=args, macros=macros, ui_filename=None)
        self.build_ui()
        self.configure_app()
        self.resize(1000, 600)

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
        plot_side_layout.addWidget(toolbar)

        # Create plot
        self.plot = PyDMArchiverTimePlot(
            plot_side_widget,
            background="white",
            optimized_data_bins=5000,
            cache_data=False,
            show_all=False,
            show_extension_lines=True,
        )
        multi_axis_plot = self.plot.plotItem
        multi_axis_plot.vb.menu = None
        multi_axis_plot.sigXRangeChangedManually.connect(self.disable_auto_scroll_button.click)
        plot_side_layout.addWidget(self.plot)

        self.settings_button = QPushButton(self.plot)
        self.settings_button.setIcon(qta.icon("msc.settings-gear"))
        self.settings_button.setFlat(True)

        self.plot_settings = PlotSettingsModal(self.settings_button, self.plot)
        self.settings_button.clicked.connect(self.plot_settings.show)

        return plot_side_widget

    def build_toolbar(self, parent):
        toolbar_widget = QWidget(parent)
        # Create tool layout
        tool_layout = QHBoxLayout()
        tool_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_widget.setLayout(tool_layout)
        save_image_button = QPushButton("Save Image", toolbar_widget)
        save_image_button.clicked.connect(self.save_plot_image)
        tool_layout.addWidget(save_image_button)
        tool_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        tool_layout.addSpacerItem(tool_spacer)
        timespan_buttons = self.build_timespan_buttons(toolbar_widget)
        tool_layout.addWidget(timespan_buttons)
        data_insight_tool_button = QPushButton("Data Insight Tool", toolbar_widget)
        data_insight_tool_button.clicked.connect(self.open_data_insight_tool)
        tool_layout.addWidget(data_insight_tool_button)

        return toolbar_widget

    def build_timespan_buttons(self, parent: QWidget):
        timespan_button_widget = QWidget(parent)
        timespan_button_layout = QHBoxLayout()
        timespan_button_layout.setContentsMargins(0, 0, 0, 0)
        timespan_button_widget.setLayout(timespan_button_layout)

        self.timespan_buttons = QButtonGroup(timespan_button_widget)
        self.timespan_buttons.setExclusive(True)

        timespan_button_data = (
            ("1m", 60),
            ("1h", 3600),
            ("1d", 86400),
            ("1w", 604800),
            ("1M", 2628300),
            ("Disable AutoScroll", -2),
        )

        for text, id in timespan_button_data:
            timespan_button = QPushButton(text, timespan_button_widget)
            timespan_button.setMaximumWidth(35)
            timespan_button.setCheckable(True)
            timespan_button_layout.addWidget(timespan_button)
            self.timespan_buttons.addButton(timespan_button, id)

        default_button = self.timespan_buttons.button(3600)
        default_button.setChecked(True)

        self.disable_auto_scroll_button = self.timespan_buttons.button(-2)
        self.disable_auto_scroll_button.hide()

        self.timespan_buttons.buttonToggled.connect(self.set_plot_timerange)

        return timespan_button_widget

    def build_control_side(self, parent):
        # Create right layout
        control_side_widget = QWidget(parent)
        control_side_layout = QVBoxLayout()
        control_side_widget.setLayout(control_side_layout)

        # Create pv plotter layout
        pv_plotter_layout = QHBoxLayout()
        control_side_layout.addLayout(pv_plotter_layout)
        pv_line_edit = QLineEdit(control_side_widget)
        pv_line_edit.setPlaceholderText("Enter PV")
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
        footer_widget.setFixedHeight(12)
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_widget.setLayout(footer_layout)

        footer_label_data = (
            (self.git_version(), "Trace Version"),
            (gethostname(), "Node Name"),
            (getuser(), "User Name"),
            (str(os.getpid()), "PID"),
            (os.getenv("PYDM_ARCHIVER_URL"), "Archiver URL"),
        )

        for text, tooltip in footer_label_data:
            label = QLabel(text, footer_widget)
            label.setFont(label_font)
            label.setToolTip(tooltip)
            label.setAlignment(Qt.AlignBottom)
            footer_layout.addWidget(label)
            footer_layout.addWidget(BreakerLabel(footer_widget))

        last_breaker = footer_widget.children()[-1]
        footer_layout.removeWidget(last_breaker)

        footer_spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        footer_layout.addSpacerItem(footer_spacer)

        self.time_label = PyDMLabel(footer_widget, f"ca://{datetime_pv}")
        self.time_label.setAlignment(Qt.AlignBottom)
        footer_layout.addWidget(self.time_label)

        return footer_widget

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

    @Slot()
    def save_plot_image(self) -> None:
        """Saves current plot as an image. Opens file dialog to allow user to
        set custom location."""
        exporter = ImageExporter(self.plot.plotItem)
        default_filename = datetime.now().strftime(f"{getuser()}_trace_%Y%m%d_%H%M%S.png")
        usr_home_dir = os.path.expanduser("~")
        file_path, _ = QFileDialog.getSaveFileName(
            None,
            "Save Plot Image",
            os.path.join(usr_home_dir, default_filename),
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)",
        )
        if file_path:
            try:
                exporter.export(file_path)
                logger.info(f"Saved image file to: {file_path}")
            except Exception as e:
                logger.error(f"Failed to save image: {e}")

    @Slot()
    def fetch_archive(self) -> None:
        """Triggers a fetch to the archive"""
        if not (self.plot._archive_request_queued):
            logger.info("Requesting data from archiver")
            self.plot.requestDataFromArchiver()
        else:
            logger.info("Archive fetch is already queued")

    @Slot()
    def open_data_insight_tool(self):
        """Create a new instance of the Data Insight Tool"""
        dit = DataInsightTool(self, self.curves_model, self.plot)
        dit.show()

    @Slot()
    def set_plot_timerange(self) -> None:
        """Slot to be called when a timespan setting button is pressed.
        This will enable autoscrolling along the x-axis and disable mouse
        controls. If the "Cursor" button is pressed, then autoscrolling is
        disabled and mouse controls are enabled.
        """
        timespan = self.timespan_buttons.checkedId()

        enable_scroll = timespan != -2
        if enable_scroll:
            logger.debug(f"Enabling plot autoscroll for {timespan}s")
        else:
            logger.debug("Disabling plot autoscroll, using mouse controls")
        self.autoScroll(enable=enable_scroll, timespan=timespan)

    @Slot(bool)
    @Slot(bool, int)
    def autoScroll(self, enable: bool, timespan: int = None):
        if timespan is None:
            timespan = self.timespan_buttons.checkedId()
            if timespan < 0:
                return

        refresh_rate = self.plot_settings.auto_scroll_interval
        self.plot.setAutoScroll(enable, timespan, refresh_rate=refresh_rate)

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
