from os import getenv
from pathlib import Path
from urllib.parse import urlparse

from qtpy.QtCore import Slot, Signal, QObject
from qtpy.QtWidgets import QFileDialog, QMessageBox

from pydm.widgets.archiver_time_plot import PyDMArchiverTimePlot

from config import logger, save_file_dir
from file_io import IOTimeParser, TraceFileConverter


class TraceFileHandler(QObject):
    """Manage import/export of Trace save files and update the plot/UI.

    This QObject coordinates file dialogs, format conversion, and plot updates
    for Trace configuration files. It uses `TraceFileConverter` to read and
    write various supported formats (``.trc`` native, ``.xml`` from Java
    Archive Viewer, and ``.stp`` from StripTool), validates the archiver URL,
    parses time ranges via `IOTimeParser`, and emits signals that other
    components consume to update axes, curves, plot settings, and the x-axis
    range.
    """

    axes_signal = Signal(list)
    curves_signal = Signal(list)
    plot_settings_signal = Signal(dict)
    timerange_signal = Signal(tuple)
    auto_scroll_span_signal = Signal(float)
    file_loaded_signal = Signal(Path)

    def __init__(self, plot: PyDMArchiverTimePlot, parent=None):
        """Initialize the File IO Manager, which is responsible for managing
        the import and export of Trace save files

        Parameters
        ----------
        plot : PyDMArchiverTimePlot
            Target plot whose configuration and data are exported/imported.
        parent : QObject | None, optional
            Parent QObject for Qt ownership, by default None.
        """
        super().__init__(parent)
        self.plot = plot
        self.current_file = None
        self.current_dir = save_file_dir
        self.converter = TraceFileConverter()

    @Slot()
    def save_file(self) -> None:
        """Export the current plot data to the current file"""
        if self.current_file is None:
            logger.debug("No current file set, prompting for save location")
            self.save_as()
            return
        elif not self.current_file.match("*.trc"):
            self.current_file = self.current_file.with_suffix(".trc")

        try:
            logger.debug(f"Attempting to export to file: {self.current_file}")
            self.converter.export_file(self.current_file, self.plot)
        except FileNotFoundError as e:
            logger.error(str(e))
            self.save_as()

    @Slot()
    def save_as(self) -> None:
        """Prompt the user for a file to export config data to"""
        file_name, _ = QFileDialog.getSaveFileName(
            self.parent(), "Save Trace", str(self.current_dir), "Trace Save File (*.trc)"
        )
        file_path = Path(file_name)
        if file_path.is_dir():
            logger.warning("No file name provided to export save file to")
            return

        self.current_file = file_path
        self.current_dir = file_path.parent

        self.save_file()

    @Slot()
    @Slot(str)
    @Slot(Path)
    def open_file(self, file_name: str | Path = None) -> None:
        """Prompt the user for which config file to load from"""
        # Get the save file from the user
        if not file_name:
            file_name, _ = QFileDialog.getOpenFileName(
                self.parent(),
                "Open Trace",
                str(self.current_dir),
                "Trace Save File (*.trc *.xml *.stp);;Java Archive Viewer (*.xml);;"
                + "StripTool File (*.stp);;All Files (*)",
            )
        file_path = Path(file_name)
        if not file_path.is_file():
            logger.warning(f"Attempted import is not a file: {file_path}")
            return

        # Import the given file, and convert it from Java Archive Viewer's
        # format to Trace's format if necessary
        try:
            logger.debug(f"Attempting to import file: {file_path}")
            file_data = self.converter.import_file(file_path)
            self.current_file = file_path
            self.current_dir = file_path.parent
            logger.info(f"Successfully loaded file: {file_path}")
        except (FileNotFoundError, ValueError) as e:
            logger.error(str(e))
            self.open_file()
            return

        # Confirm the PYDM_ARCHIVER_URL is the same as the imported Archiver URL
        # If they are not the same, prompt the user to confirm continuing
        import_url = urlparse(file_data["archiver_url"])
        archiver_url = urlparse(getenv("PYDM_ARCHIVER_URL"))
        if import_url.hostname != archiver_url.hostname:
            logger.warning(f"Attempting to import save file using different Archiver URL: {import_url.hostname}")
            ret = QMessageBox.warning(
                self.parent(),
                "Import Error",
                "The config file you tried to open reads from a different archiver.\n"
                f"\nCurrent archiver is:\n{archiver_url.hostname}\n"
                f"\nAttempted import uses:\n{import_url.hostname}\n\n"
                "\nContinue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if ret == QMessageBox.No:
                return

        # Parse the time range for the X-Axis; check validity before prompting changes
        try:
            start_str = file_data["time_axis"]["start"]
            end_str = file_data["time_axis"]["end"]
            start_dt, end_dt = IOTimeParser.parse_times(start_str, end_str)
            logger.debug(f"Starting time: {start_dt}")
            logger.debug(f"Ending time: {end_dt}")
        except ValueError as e:
            logger.error(str(e))
            self.open_file()
            return

        # Prompt a change to the plot's axes, curves, and settings
        self.axes_signal.emit(file_data["y-axes"])
        self.curves_signal.emit(file_data["curves"] + file_data["formula"])
        self.plot_settings_signal.emit(file_data["plot"])
        self.file_loaded_signal.emit(file_path)

        # Prompt a change to the X-axis timerange
        if end_str == "now":
            delta = end_dt - start_dt
            timespan = delta.total_seconds()
            self.auto_scroll_span_signal.emit(timespan)
        else:
            x_range = (start_dt.timestamp(), end_dt.timestamp())
            self.timerange_signal.emit(x_range)
