import os
import argparse
import subprocess
from socket import gethostname
from getpass import getuser
from pathlib import Path
from datetime import datetime

from qtpy.QtGui import QFont, QColor, QImage, QKeySequence
from qtpy.QtCore import Qt, Slot, QSize, Signal, QBuffer, QIODevice, QSettings
from qtpy.QtWidgets import (
    QMenu,
    QLabel,
    QDialog,
    QWidget,
    QMenuBar,
    QLineEdit,
    QSplitter,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QApplication,
    QButtonGroup,
    QAbstractButton,
)
from pyqtgraph.exporters import ImageExporter

from pydm import Display
from pydm.widgets import PyDMLabel, PyDMArchiverTimePlot
from pydm.utilities.macro import parse_macro_string

from config import logger, datetime_pv
from file_io import PathAction, TraceFileHandler
from widgets import ControlPanel, ElogPostModal, DataInsightTool, PlotSettingsModal
from services import Theme, IconColors, ThemeManager, get_user, post_entry

DISABLE_AUTO_SCROLL = -2  # Using -2 as invalid since QButtonGroups use -1 as invalid


class TraceDisplay(Display):
    """Main display widget for the Trace application.

    This class builds and manages the user interface, including the plot, control
    panel, menus, theme handling, and interactions such as file I/O and E-Log
    posting.

    """

    gridline_opacity_change = Signal(int)
    set_all_y_axis_gridlines = Signal(bool)

    def __init__(self, parent=None, args=None, macros=None) -> None:
        """Initialize the Trace display and construct the UI.

        Parameters
        ----------
        parent : QWidget, optional
            The parent widget, by default None.
        args : list[str] | None, optional
            Command-line style arguments passed in by the host application.
        macros : dict | None, optional
            PyDM-style macro substitutions that can influence startup behavior.

        Returns
        -------
        None
            This method initializes the widget in place.
        """
        super(TraceDisplay, self).__init__(parent=parent, args=args, macros=macros, ui_filename=None)

        app = QApplication.instance()
        if not app.main_window:
            return

        self.theme_manager = ThemeManager(
            app,
        )
        settings = QSettings()
        self.is_dark_mode = settings.value("isDarkTheme", False, type=bool)
        self.build_ui()
        self.configure_app(app)
        self.setup_icons()
        self.resize(1000, 600)

        # Set plot's timerange after the UI is built
        default_button = self.timespan_buttons.button(3600)
        default_button.setChecked(True)

        input_file, startup_pvs = self.parse_cli_args(args, macros)
        if input_file:
            self.file_handler.open_file(input_file)
        for pv in startup_pvs:
            self.layout().itemAt(0).widget().widget(1).add_curve(pv)

    @property
    def gridline_opacity(self) -> int:
        """Get the current gridline opacity value from the plot settings.

        Returns
        -------
        int
            The alpha value (0-255) used for y-axis gridline opacity.
        """
        return self.plot_settings.gridline_opacity

    def minimumSizeHint(self) -> QSize:
        """Return the minimum recommended size for the widget.

        Returns
        -------
        QSize
            The minimum size hint used by Qt layouts.
        """
        return QSize(700, 350)

    def build_ui(self) -> None:
        """Set up the main UI for the application.

        Returns
        -------
        None
            Constructs and lays out child widgets.
        """
        # Set window title
        self.setWindowTitle("Trace")
        # Create main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create the plotting and control widgets
        plot_side_widget = self.build_plot_side(self)
        self.control_panel = ControlPanel(theme_manager=self.theme_manager)
        self.control_panel.layout().setContentsMargins(8, 0, 0, 0)
        self.control_panel.plot = self.plot
        self.control_panel.curve_list_changed.connect(self.data_insight_tool.update_pv_select_box)

        # Create main splitter
        main_splitter = QSplitter(self)
        main_splitter.addWidget(plot_side_widget)
        main_splitter.addWidget(self.control_panel)
        main_splitter.setCollapsible(0, False)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setHandleWidth(10)

        main_layout.addWidget(main_splitter)

        # Create the footer section of the app
        footer_widget = self.build_footer(self)
        main_layout.addWidget(footer_widget)

    def build_plot_side(self, parent: QWidget) -> QWidget:
        """Build the plot side of the application, including the toolbar
        and plot widget.

        Parameters
        ----------
        parent : QWidget
            The parent widget for the plot side.

        Returns
        -------
        QWidget
            Returns the plot side widget.
        """
        plot_side_widget = QWidget(parent)
        plot_side_layout = QVBoxLayout()
        plot_side_layout.setContentsMargins(0, 0, 8, 0)
        plot_side_widget.setLayout(plot_side_layout)

        toolbar = self.build_toolbar(plot_side_widget)
        plot_side_layout.addWidget(toolbar)

        background_color = "#1E1E1E" if self.theme_manager.get_current_theme() == Theme.DARK else "white"

        self.plot = PyDMArchiverTimePlot(
            plot_side_widget,
            background=background_color,
            optimized_data_bins=5000,
            cache_data=False,
            show_all=False,
        )

        multi_axis_plot = self.plot.plotItem
        multi_axis_plot.vb.menu = None
        multi_axis_plot.sigXRangeChangedManually.connect(self.disable_auto_scroll_button.click)
        plot_side_layout.addWidget(self.plot)

        self.data_insight_tool = DataInsightTool(self)
        self.data_insight_tool.plot = self.plot

        self.settings_button = QPushButton(self.plot)
        self.settings_button.setFlat(True)

        self.plot_settings = PlotSettingsModal(self.settings_button, self.plot)
        self.plot_settings.auto_scroll_interval_change.connect(self.set_auto_scroll_interval)
        self.plot_settings.grid_alpha_change.connect(self.gridline_opacity_change.emit)
        self.plot_settings.set_all_y_axis_gridlines.connect(self.plot.setShowYGrid)
        self.plot_settings.set_all_y_axis_gridlines.connect(self.set_all_y_axis_gridlines.emit)
        self.plot_settings.disable_autoscroll.connect(self.disable_auto_scroll_button.click)
        self.plot_settings.sig_curve_palette_changed.connect(self.set_curve_palette)
        self.settings_button.clicked.connect(self.plot_settings.show)

        return plot_side_widget

    def build_toolbar(self, parent: QWidget) -> QWidget:
        """Build the toolbar for the plotting section of the application. This
        includes buttons for setting the autoscroll timespan.

        Parameters
        ----------
        parent : QWidget
            The parent widget for the toolbar.

        Returns
        -------
        QWidget
            Returns the toolbar widget.
        """
        toolbar_widget = QWidget(parent)
        # Create tool layout
        tool_layout = QHBoxLayout()
        tool_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_widget.setLayout(tool_layout)

        tool_spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        tool_layout.addSpacerItem(tool_spacer)

        timespan_buttons = self.build_timespan_buttons(toolbar_widget)
        tool_layout.addWidget(timespan_buttons)

        self.timespan_lineEdit = QLineEdit()
        self.timespan_lineEdit.returnPressed.connect(self.parse_time_input)
        self.timespan_lineEdit.setFixedWidth(120)
        self.timespan_lineEdit.setPlaceholderText("Enter timescale")
        tool_layout.addWidget(self.timespan_lineEdit)

        return toolbar_widget

    def build_timespan_buttons(self, parent: QWidget) -> QWidget:
        """Build the timespan buttons for the toolbar. This includes buttons
        for users to set enable autoscrolling for various timespans.

        Parameters
        ----------
        parent : QWidget
            The parent widget for the timespan buttons.

        Returns
        -------
        QWidget
            Returns the timespan buttons widget.
        """
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
            ("Disable AutoScroll", DISABLE_AUTO_SCROLL),
        )

        for text, id in timespan_button_data:
            timespan_button = QPushButton(text, timespan_button_widget)
            timespan_button.setMaximumWidth(35)
            timespan_button.setCheckable(True)
            timespan_button_layout.addWidget(timespan_button)
            self.timespan_buttons.addButton(timespan_button, id)

        self.disable_auto_scroll_button = self.timespan_buttons.button(DISABLE_AUTO_SCROLL)
        self.disable_auto_scroll_button.hide()

        self.timespan_buttons.buttonToggled.connect(self.set_auto_scroll_span)

        return timespan_button_widget

    def build_footer(self, parent: QWidget) -> QWidget:
        """Build the footer for the application. This displays the name
        of the server the application is running on, the archiver URL,
        and a timestamp PV.

        Parameters
        ----------
        parent : QWidget
            The parent widget for the footer.

        Returns
        -------
        QWidget
            The footer widget to be added to a layout.
        """
        self.footer_label_font = QFont()
        self.footer_label_font.setPointSize(8)

        footer_widget = QWidget(parent)
        footer_widget.setFixedHeight(12)
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_widget.setLayout(footer_layout)

        # Left side of footer, with various info labels
        self.footer_info_widget = QWidget(footer_widget)
        footer_layout.addWidget(self.footer_info_widget)
        footer_info_layout = QHBoxLayout(self.footer_info_widget)
        footer_info_layout.setContentsMargins(0, 0, 0, 0)

        footer_label_data = (
            (gethostname(), "Node Name"),
            (os.getenv("PYDM_ARCHIVER_URL"), "Archiver URL"),
        )

        for text, tooltip in footer_label_data:
            label = QLabel(text, self.footer_info_widget)
            label.setFont(self.footer_label_font)
            label.setToolTip(tooltip)
            label.setAlignment(Qt.AlignBottom)
            footer_info_layout.addWidget(label)
            footer_info_layout.addWidget(BreakerLabel(self.footer_info_widget))

        last_breaker = self.footer_info_widget.children()[-1]
        footer_info_layout.removeWidget(last_breaker)

        footer_spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        footer_layout.addSpacerItem(footer_spacer)

        self.time_label = PyDMLabel(footer_widget, f"ca://{datetime_pv}")
        self.time_label.setAlignment(Qt.AlignBottom)
        footer_layout.addWidget(self.time_label)

        return footer_widget

    def parse_time_input(self) -> None:
        """
        Parse user entered time input. Allows user to add 'm' 'h', 'd', 'w', or 'M'
        to the end of a float timescale to select minutes, hours, days, weeks, or months.
        Timescale multiplier is set accordingly, and if the remaining entry can be
        converted to a float, the timescale is changed accordingly.
        """

        MULTIPLIERS = {"m": 60, "h": 3600, "d": 86400, "w": 604800, "M": 2628300}

        time_str = self.timespan_lineEdit.text()

        if time_str == "":
            return

        if time_str[0] == "-":
            time_str = time_str[1:]

        final_char = time_str[-1]
        if final_char not in MULTIPLIERS:
            return

        try:
            time = float(time_str[:-1])
        except ValueError:
            return

        multiplier = MULTIPLIERS.get(final_char)

        time_sec = time * multiplier
        self.set_auto_scroll_span(time_sec)

    @Slot(Path)
    def set_file_indicator(self, file_path: Path) -> None:
        """Set the file indicator label to the given file path.

        Parameters
        ----------
        file_path : Path
            The file path to set the label to.

        Returns
        -------
        None
            Updates the footer to indicate the currently loaded file.
        """
        if not file_path:
            return
        filename = file_path.name
        if hasattr(self, "file_label") and self.file_label is not None:
            self.file_label.setText(filename)
        else:
            self.footer_info_widget.layout().addWidget(BreakerLabel(self.footer_info_widget))
            self.file_label = QLabel(filename, self.footer_info_widget)
            self.file_label.setFont(self.footer_label_font)
            self.file_label.setToolTip("Currently loaded file")
            self.footer_info_widget.layout().addWidget(self.file_label)

    def setup_icons(self) -> None:
        """Set up all icons after the theme manager is initialized.

        Returns
        -------
        None
            Updates icon assets for current theme.
        """
        self.settings_button.setIcon(self.theme_manager.create_icon("msc.settings-gear", IconColors.PRIMARY))

    def on_theme_changed(self, theme: Theme) -> None:
        """Handle theme changes - update icons and button text

        Parameters
        ----------
        theme : Theme
            The new theme that was set.

        Returns
        -------
        None
            Applies UI updates relevant to the selected theme.
        """
        if theme == Theme.DARK:
            self.theme_toggle_button.setText("Light Mode")
            icon = self.theme_manager.create_icon("fa.sun-o", IconColors.PRIMARY)
        else:
            self.theme_toggle_button.setText("Dark Mode")
            icon = self.theme_manager.create_icon("fa.moon-o", IconColors.PRIMARY)

        if icon:
            self.theme_toggle_button.setIcon(icon)

        settings_icon = self.theme_manager.create_icon("msc.settings-gear", IconColors.PRIMARY)
        if settings_icon:
            self.settings_button.setIcon(settings_icon)

    def set_curve_palette(self, palette_name: str, apply: bool = False):
        """
        Set color palette for adding new curves

        Args:
            palette_name (str): name of the selected palette, from trace/config.color_palette
            apply (bool): boolean indicator of whether to apply palette to existing curves.
        """
        self.control_panel.set_curve_palette(palette_name=palette_name, apply=apply)

    def configure_app(self, app: QApplication) -> None:
        """UI changes to be made to the PyDMApplication. Hides navigation
        & status bars, sets up file IO, sets up shortcuts & menus.

        Parameters
        ----------
        app : QApplication
            The instance of the QApplication.

        Returns
        -------
        None
            Applies application-wide configuration.
        """
        # Hide navigation bar by default (can be shown in menu bar)
        app.main_window.toggle_nav_bar(False)
        app.main_window.ui.actionShow_Navigation_Bar.setChecked(False)

        # Hide status bar by default (can be shown in menu bar)
        app.main_window.toggle_status_bar(False)
        app.main_window.ui.actionShow_Status_Bar.setChecked(False)

        # Create a TraceFileController instance for handling file I/O operations
        self.file_handler = TraceFileHandler(self.plot, self)
        self.file_handler.axes_signal.connect(self.control_panel.set_axes)
        self.file_handler.curves_signal.connect(self.control_panel.set_curves)
        self.file_handler.plot_settings_signal.connect(self.plot_settings.plot_setup)
        self.file_handler.auto_scroll_span_signal.connect(self.set_auto_scroll_span)
        self.file_handler.timerange_signal.connect(self.set_plot_timerange)
        self.file_handler.file_loaded_signal.connect(self.set_file_indicator)

        # Remove shortcut from the "Open File" menu action
        open_file_action = app.main_window.ui.actionOpen_File
        open_file_action.setText("Open PyDM File...")
        open_file_action.setShortcut(QKeySequence())

        # Create a custom menu for the application
        menu_bar: QMenuBar = app.main_window.ui.menubar
        first_menu = app.main_window.ui.menuFile.menuAction()
        trace_menu = self.construct_trace_menu(menu_bar)
        menu_bar.insertMenu(first_menu, trace_menu)

    def construct_trace_menu(self, parent: QMenuBar) -> QMenu:
        """Create the menu for the application. This includes actions for
        file IO, saving to the E-Log, opening tools, and setting the app theme.

        Parameters
        ----------
        parent : QMenuBar
            The menu bar that the Trace menu will be a part of.

        Returns
        -------
        QMenu
            The Trace menu consisting of actions for configuring the app.
        """
        menu = QMenu("Trace", parent)
        save = menu.addAction("Save", self.file_handler.save_file)
        save.setShortcut(QKeySequence("Ctrl+S"))
        save_as = menu.addAction("Save As...", self.file_handler.save_as)
        save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        load = menu.addAction("Open Trace Config...", self.file_handler.open_file)
        load.setShortcut(QKeySequence("Ctrl+O"))
        menu.addSeparator()

        save_image = menu.addAction("Save Plot Image...", self.save_plot_image)
        save_image.setShortcut(QKeySequence("Ctrl+I"))
        save_elog = menu.addAction("Save ELOG Entry...", self.elog_button_clicked)
        save_elog.setShortcut(QKeySequence("Ctrl+E"))
        menu.addSeparator()

        fetch_archive = menu.addAction("Fetch Archive Data", self.fetch_archive)
        fetch_archive.setShortcut(QKeySequence("Ctrl+F"))
        dit_action = menu.addAction("Data Insight Tool...", self.data_insight_tool.show)
        dit_action.setShortcut(QKeySequence("Ctrl+D"))

        menu.addSeparator()

        if self.is_dark_mode:
            self.theme_action = menu.addAction("Switch to Light Mode", self.toggle_theme)
        else:
            self.theme_action = menu.addAction("Switch to Dark Mode", self.toggle_theme)

        self.theme_action.setShortcut(QKeySequence("Ctrl+T"))

        return menu

    def toggle_theme(self):
        """Toggle between dark and light mode.

        Returns
        -------
        None
            Applies the selected theme and refreshes the UI.
        """
        if self.is_dark_mode:
            self.theme_manager.set_theme(Theme.LIGHT)
            self.theme_action.setText("Switch to Dark Mode")
            self.plot.setBackgroundColor(QColor("#FFFFFF"))
            self.setup_icons()
            self.is_dark_mode = False
        else:
            self.theme_manager.set_theme(Theme.DARK)
            self.theme_action.setText("Switch to Light Mode")
            self.plot.setBackgroundColor(QColor("#1E1E1E"))
            self.setup_icons()
            self.is_dark_mode = True

        QApplication.processEvents()
        self.repaint()

    @Slot()
    def save_plot_image(self) -> None:
        """Saves current plot as an image. Opens file dialog to allow user to
        set custom location.

        Returns
        -------
        None
            Writes the exported image to disk when a path is selected.
        """
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
    def elog_button_clicked(self) -> bool:
        """Takes a snapshot of the plot and posts it to the Elog API.

        Returns
        -------
        bool
            True if the post was successful, False otherwise.
        """
        # Test if API is reachable
        status_code, _ = get_user()
        if status_code != 200:
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Warning)
            error_dialog.setWindowTitle("Connection Error")
            error_dialog.setText("Failed to connect to the Elog API.")
            error_dialog.setInformativeText(
                f"""No entry was posted. If this issue persists, please report it in the
                #elog-general Slack channel. \n\nError Code: {status_code}"""
            )
            error_dialog.setStandardButtons(QMessageBox.Ok)
            error_dialog.exec_()
            return False

        # Form the request info
        # Use ImageExporter to take a snapshot of the plot
        exporter = ImageExporter(self.plot.plotItem)
        img: QImage = exporter.export(toBytes=True)
        # Convert Qimage to bytes
        buffer = QBuffer()
        buffer.open(QIODevice.ReadWrite)
        img.save(buffer, "PNG")
        image_bytes = buffer.data()
        # Get entry info from user
        dialog = ElogPostModal.maybe_create(self, image_bytes=image_bytes)
        if dialog is not None and dialog.exec_() == QDialog.Accepted:
            title, body, logbooks, attach_config = dialog.get_inputs()
        else:
            return False

        config_file_path = None
        if attach_config:
            self.file_handler.save_file()
            config_file_path = self.file_handler.current_file

        # Post the request to the Elog API
        status_code, _ = post_entry(title, body, logbooks, image_bytes, config_file_path)

        # Check if the request was successful
        if status_code == 201:
            success_dialog = QMessageBox()
            success_dialog.setIcon(QMessageBox.Information)
            success_dialog.setWindowTitle("Elog Entry Posted")
            success_dialog.setText("Elog entry posted successfully!")
            success_dialog.setStandardButtons(QMessageBox.Ok)
            success_dialog.exec_()
            return True
        else:
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Warning)
            error_dialog.setWindowTitle("Connection Error")
            error_dialog.setText("Failed to connect to the Elog API.")
            error_dialog.setInformativeText(
                f"No entry was posted. If this issue persists, please report it in the \
                #elog-general Slack channel. \n\nError Code: {status_code}"
            )
            error_dialog.setStandardButtons(QMessageBox.Ok)
            error_dialog.exec_()
            return False

    @Slot()
    def fetch_archive(self) -> None:
        """Trigger a fetch of data from the EPICS Archiver Appliance.

        Returns
        -------
        None
            Queues a data request if one is not already pending.
        """
        if not (self.plot._archive_request_queued):
            logger.info("Requesting data from archiver")
            self.plot.requestDataFromArchiver()
        else:
            logger.info("Archive fetch is already queued")

    @Slot(tuple)
    def set_plot_timerange(self, timerange: tuple[float, float]) -> None:
        """Set the plot's timerange to the given start and end datetimes.

        Parameters
        ----------
        timerange : tuple[float, float]
            The new time range for the plot to show. Index 0 is the
            timestamp on the left side of the plot, index 1 on the right.

        Returns
        -------
        None
            Sets the x-axis view range of the plot.
        """
        self.disable_auto_scroll_button.click()
        self.plot.setXRange(*timerange)
        logger.debug(f"Plot timerange set to {timerange[0]} - {timerange[1]}")

    @Slot()
    @Slot(float)
    @Slot(QAbstractButton, float)
    def set_auto_scroll_span(self, arg1=None, arg2=None) -> None:
        """Update the auto-scroll timespan based on UI interaction or input.

        This enables autoscrolling of the x-axis for the selected span and
        disables manual mouse controls. When the special "Disable AutoScroll"
        button is selected, autoscrolling is turned off and mouse controls are
        re-enabled.

        Parameters
        ----------
        arg1 : QAbstractButton | float | int | None, optional
            The toggled timespan button or an explicit timespan value in
            seconds. If None, the currently checked button is used.
        arg2 : float | None, optional
            The checked state flag passed by Qt when connected to a button
            toggled signal; ignored unless `arg1` is a button.

        Returns
        -------
        None
            Applies the autoscroll configuration to the plot.
        """
        if isinstance(arg1, QAbstractButton):
            if not arg2:
                return
            timespan = self.timespan_buttons.id(arg1)
        elif isinstance(arg1, (int, float)):
            timespan = arg1
        else:
            timespan = self.timespan_buttons.checkedId()

        enable_scroll = timespan != DISABLE_AUTO_SCROLL

        if enable_scroll:
            logger.debug(f"Enabling plot autoscroll for {timespan}s")
        else:
            logger.debug("Disabling plot autoscroll, using mouse controls")
            self.disable_auto_scroll_button.click()

        self.autoScroll(enable=enable_scroll, timespan=timespan)

    @Slot(int)
    def set_auto_scroll_interval(self, inteval: int) -> None:
        """Set the auto-scroll refresh interval for the plot.

        Parameters
        ----------
        inteval : int
            The refresh interval in milliseconds.

        Returns
        -------
        None
            Updates the plot's autoscroll refresh rate.
        """
        timespan = self.timespan_buttons.checkedId()
        enable_scroll = timespan != DISABLE_AUTO_SCROLL

        self.plot.setAutoScroll(enable_scroll, timespan, refresh_rate=inteval)

    @Slot(bool)
    @Slot(bool, float)
    def autoScroll(self, enable: bool, timespan: float = None):
        """Enable or disable autoscroll, optionally specifying a timespan.

        Parameters
        ----------
        enable : bool
            Whether autoscroll should be enabled.
        timespan : float | None, optional
            The x-axis span, in seconds, to keep visible while autoscrolling.
            If None, uses the currently selected timespan button.

        Returns
        -------
        None
            Configures autoscroll on the underlying plot widget.
        """
        if timespan is None:
            timespan = self.timespan_buttons.checkedId()
            if timespan < 0:
                return

        refresh_interval = self.plot_settings.auto_scroll_interval
        self.plot.setAutoScroll(enable, timespan, refresh_rate=refresh_interval)

    @staticmethod
    def git_version():
        """Get the current git tag for the project.

        Returns
        -------
        str
            The output of `git describe --tags`, or an empty string on failure.
        """
        project_directory = __file__.rsplit("/", 1)[0]
        git_cmd = subprocess.run(
            f"cd {project_directory} && git describe --tags", text=True, shell=True, capture_output=True
        )
        return git_cmd.stdout.strip()

    def parse_cli_args(self, args, macros):
        """Parse CLI-style arguments and macros into startup configuration.

        Parameters
        ----------
        args : list[str] | None
            Argument vector to parse. Unknown options are ignored.
        macros : dict | None
            PyDM-style macro substitutions. Values for `INPUT_FILE`, `PV`, or
            `PVS` here are merged with CLI options.

        Returns
        -------
        tuple[str, list[str]]
            A tuple of `(input_file, startup_pvs)` where `input_file` is the
            selected configuration file path (or empty string) and
            `startup_pvs` is a de-duplicated list of PV/formula strings to add.
        """
        args = args or []
        macros = macros or {}

        parser = argparse.ArgumentParser(
            prog="trace",
            description="Trace\nThis is a PyDM application used to display archived and live pv data.",
            epilog="\n\t".join(
                [
                    "Examples:",
                    "pydm $PHYSICS_TOP/trace/main.py"
                    "bash $PHYSICS_TOP/trace/launch_trace.bash"
                    "%(prog)s"
                    "%(prog)s -i some_input_file.trc"
                    "%(prog)s -p SOME:PV:TO:PLOT OTHER:PV:TO:PLOT"
                    '%(prog)s -m \'{"PVS": ["FOO:CHANNEL", "BAR:CHANNEL", "f://{A}+{B}"]}\''
                    '%(prog)s -m "INPUT_FILE = trace/examples/FormulaExample.trc"',
                ]
            ),
            formatter_class=argparse.RawTextHelpFormatter,
        )

        parser.add_argument("-v", "--version", action="version", version="%(prog)s " + self.git_version())
        parser.add_argument(
            "-i",
            "--input_file",
            action=PathAction,
            nargs="?",
            default=[],
            help="Absolute file path to import from\nAlternatively can be provided as INPUT_FILE macro",
        )
        parser.add_argument(
            "-p",
            "--pvs",
            nargs="*",
            default=[],
            help="\n".join(
                [
                    "Space-separated list of PVs to show on startup",
                    "Formulas should be passed without spaces: f://{A}+{B}",
                    "Alternatively can be provided as PV or PVS macros",
                ]
            ),
        )
        parser.add_argument(
            "-m",
            "--macro",
            default="",
            help="\n\t".join(
                [
                    "Mimic PyDM macro replacements to use. Should be in JSON object format.",
                    "ON Formatting Reminder:",
                    "JSON requires double quotes for strings, so you should wrap this",
                    "whole argument in single quotes.",
                    "--or--",
                    "Specify macro replacements as KEY=value pairs using a comma as a",
                    "delimiter. If you want to uses spaces after the delimiters or around",
                    "the '=' signs, wrap the entire set with quotes.",
                ]
            ),
        )

        # Parse arguments and ignore unknowns
        known, unknown = parser.parse_known_args(args)
        for arg in unknown:
            if arg:
                logger.warning(f"Not using unknown argument: {arg}")

        # Parse any macros passed into trace
        if known.macro:
            parsed_macros = parse_macro_string(known.macro)
            macros.update(**parsed_macros)

        # Get the file to import from if one is provided. Prioritize args over macro
        try:
            # Need to unpack as PathAction returns a list
            input_file = known.input_file[0]
        except IndexError:
            input_file = macros.get("INPUT_FILE", "")

        # Get the list of PVs to show on startup
        startup_pvs = []
        for key in ("PV", "PVS"):
            if key in macros:
                val = macros[key]
                if isinstance(val, str):
                    startup_pvs.append(val)
                elif isinstance(val, list):
                    startup_pvs.extend(val)
        startup_pvs += known.pvs

        # Remove duplicates from startup_pvs
        startup_pvs = list(dict.fromkeys(startup_pvs))

        return (input_file, startup_pvs)


class BreakerLabel(QLabel):
    """A simple visual separator label used in the footer area.

    Displays a bold vertical bar character to separate adjacent labels.

    """

    breaker_font = QFont()
    breaker_font.setBold(True)
    breaker_font.setPointSize(12)

    def __init__(self, parent):
        """Create a breaker label.

        Parameters
        ----------
        parent : QWidget
            The parent widget that will own this label.

        Returns
        -------
        None
            Initializes the label and applies styling.
        """
        super().__init__(parent)
        self.setText("|")
        self.setFont(self.breaker_font)
        self.setAlignment(Qt.AlignBottom)
