import os
import subprocess
from socket import gethostname
from getpass import getuser
from datetime import datetime

import qtawesome as qta
from axis_item import AxisItem
from qtpy.QtGui import QFont, QCloseEvent
from qtpy.QtCore import Qt, Slot, QSize, Signal
from qtpy.QtWidgets import (
    QLabel,
    QWidget,
    QLineEdit,
    QSplitter,
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
from mixins import FileIOMixin, PlotConfigMixin
from widgets import DataInsightTool, PlotSettingsModal


class TraceDisplay(Display, FileIOMixin, PlotConfigMixin):
    gridline_opacity_change = Signal(int)

    def __init__(self, parent=None, args=None, macros=None) -> None:
        super(TraceDisplay, self).__init__(parent=parent, args=args, macros=macros, ui_filename=None)
        self.build_ui()
        self.configure_app()
        self.resize(1000, 600)

    @property
    def gridline_opacity(self) -> int:
        """Get the current gridline opacity value from the plot settings"""
        return self.plot_settings.gridline_opacity

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
        control_panel = ControlPanel()
        control_panel.plot = self.plot

        # Create main splitter
        main_splitter = QSplitter(self)
        main_splitter.addWidget(plot_side_widget)
        main_splitter.addWidget(control_panel)
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
        )
        multi_axis_plot = self.plot.plotItem
        multi_axis_plot.vb.menu = None
        multi_axis_plot.sigXRangeChangedManually.connect(self.disable_auto_scroll_button.click)
        plot_side_layout.addWidget(self.plot)

        self.settings_button = QPushButton(self.plot)
        self.settings_button.setIcon(qta.icon("msc.settings-gear"))
        self.settings_button.setFlat(True)

        self.plot_settings = PlotSettingsModal(self.settings_button, self.plot)
        self.plot_settings.grid_alpha_change.connect(self.gridline_opacity_change.emit)
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


class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())

        # Create pv plotter layout
        pv_plotter_layout = QHBoxLayout()
        self.layout().addLayout(pv_plotter_layout)
        self.pv_line_edit = QLineEdit()
        self.pv_line_edit.setPlaceholderText("Enter PV")
        self.pv_line_edit.returnPressed.connect(self.add_curve_from_line_edit)
        pv_plotter_layout.addWidget(self.pv_line_edit)
        pv_plot_button = QPushButton("Plot")
        pv_plot_button.clicked.connect(self.add_curve_from_line_edit)
        pv_plotter_layout.addWidget(pv_plot_button)

        # Create axis & curve view
        self.axis_list = QVBoxLayout()
        self.axis_list.addStretch()
        self.layout().addLayout(self.axis_list)
        new_axis_button = QPushButton("New Axis")
        new_axis_button.clicked.connect(self.add_axis)
        self.layout().addWidget(new_axis_button)

    def add_curve_from_line_edit(self):
        pv = self.pv_line_edit.text()
        self.add_curve(pv)
        self.pv_line_edit.clear()

    @property
    def plot(self):
        if not self._plot:
            parent = self.parent()
            while not hasattr(parent, "plot"):
                parent = parent.parent()
            self._plot = parent.plot
        return self._plot

    @plot.setter
    def plot(self, plot):
        self._plot = plot

    def add_axis(self, name: str = ""):
        logger.debug("Adding new empty axis to the plot")
        if not name:
            counter = len(self.plot.plotItem.axes) - 2
            while (name := f"Y-Axis {counter}") in self.plot.plotItem.axes:
                counter += 1

        self.plot.addAxis(plot_data_item=None, name=name, orientation="left", label=name)
        new_axis = self.plot._axes[-1]

        axis_item = AxisItem(new_axis)
        self.axis_list.insertWidget(self.axis_list.count() - 1, axis_item)

        logger.debug(f"Added axis {new_axis.name} to plot")

    def add_curve(self, pv):
        last_axis = self.axis_list.itemAt(self.axis_list.count() - 2).widget()
        last_axis.add_curve(pv)

    def closeEvent(self, a0: QCloseEvent):
        for axis_item in range(self.axis_list.count()):
            axis_item.close()
        super().closeEvent(a0)
