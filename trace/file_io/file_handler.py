from os import getenv
from typing import Union
from pathlib import Path
from urllib.parse import urlparse

from qtpy.QtCore import QObject
from qtpy.QtWidgets import QFileDialog, QMessageBox

from pydm.widgets.archiver_time_plot import PyDMArchiverTimePlot

from config import logger, save_file_dir
from file_io.time_parser import IOTimeParser
from file_io.trace_file_convert import TraceFileConverter


class TraceFileHandler(QObject):
    def __init__(self, plot: PyDMArchiverTimePlot, parent=None):
        """Initialize the File IO Manager, which is responsible for managing
        the import and export of Trace save files
        """
        super().__init__(parent)
        self.plot = plot
        self.io_path = save_file_dir
        self.converter = TraceFileConverter()

    def export_save_file(self) -> None:
        """Prompt the user for a file to export config data to"""
        file_name, _ = QFileDialog.getSaveFileName(
            self.parent(), "Save Trace", str(self.io_path), "Trace Save File (*.trc)"
        )
        file_name = Path(file_name)
        if file_name.is_dir():
            logger.warning("No file name provided to export save file to")
            return

        try:
            logger.debug(f"Attempting to export to file: {file_name}")
            self.io_path = file_name.parent
            self.converter.export_file(file_name, self.plot)
        except FileNotFoundError as e:
            logger.error(str(e))
            self.export_save_file()

    def import_save_file(self, file_name: Union[str, Path] = None) -> None:
        """Prompt the user for which config file to import from"""
        # Get the save file from the user
        if not file_name:
            file_name, _ = QFileDialog.getOpenFileName(
                self.parent(),
                "Open Trace",
                str(self.io_path),
                "Trace Save File (*.trc *.xml *.stp);;Java Archive Viewer (*.xml);;"
                + "StripTool File (*.stp);;All Files (*)",
            )
        file_name = Path(file_name)
        if not file_name.is_file():
            logger.warning(f"Attempted import is not a file: {file_name}")
            return

        # Import the given file, and convert it from Java Archive Viewer's
        # format to Trace's format if necessary
        try:
            logger.debug(f"Attempting to import file: {file_name}")
            file_data = self.converter.import_file(file_name)
            self.io_path = file_name.parent
        except (FileNotFoundError, ValueError) as e:
            logger.error(str(e))
            self.import_save_file()
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

        # Parse the time range for the X-Axis
        try:
            start_str = file_data["time_axis"]["start"]
            end_str = file_data["time_axis"]["end"]
            start_dt, end_dt = IOTimeParser.parse_times(start_str, end_str)
            logger.debug(f"Starting time: {start_dt}")
            logger.debug(f"Ending time: {end_dt}")
        except ValueError as e:
            logger.error(str(e))
            self.import_save_file()
            return

        # Set the models to use the file data
        self.axis_table_model.set_model_axes(file_data["y-axes"])
        self.curves_model.set_model_curves(file_data["curves"] + file_data["formula"])
        self.plot_setup(file_data["plot"])

        # Enable auto scroll if the end time is "now"
        self.ui.cursor_scale_btn.click()
        if end_str == "now":
            delta = end_dt - start_dt
            timespan = delta.total_seconds()
            self.plot.setAutoScroll(True, timespan)
        else:
            x_range = (start_dt.timestamp(), end_dt.timestamp())
            self.plot.plotItem.disableXAutoRange()
            self.plot.plotItem.setXRange(*x_range)
