import os
import argparse
import subprocess
from socket import gethostname
from typing import Dict, List, Tuple, Union
from getpass import getuser
from logging import Handler, LogRecord

from qtpy.sip import isdeleted
from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import QLabel, QApplication, QAbstractButton

from pydm import Display
from pydm.utilities.macro import parse_macro_string

from config import logger, datetime_pv
from mixins import FileIOMixin, AxisTableMixin, PlotConfigMixin, TracesTableMixin
from styles import CenterCheckStyle
from trace_file_convert import PathAction


class TraceDisplay(Display, TracesTableMixin, AxisTableMixin, FileIOMixin, PlotConfigMixin):
    def __init__(self, parent=None, args=None, macros=None, ui_filename=__file__.replace(".py", ".ui")) -> None:
        super(TraceDisplay, self).__init__(parent=parent, args=args, macros=macros, ui_filename=ui_filename)
        # Set up PyDMApplication
        self.configure_app()
        self.set_footer()

        # Initialize the Mixins
        self.axis_table_init()
        self.traces_table_init()
        self.plot_config_init()
        self.file_io_init()

        self.curve_delegates_init()
        self.axis_delegates_init()
        self.timespan = -1
        self.axis_table_model.reset_everything.connect(self.resetPlot)
        # Create reference dict for timespan_btns button group
        self.button_spans = {
            self.ui.min_scale_btn: 60,
            self.ui.hour_scale_btn: 3600,
            self.ui.day_scale_btn: 86400,
            self.ui.week_scale_btn: 604800,
            self.ui.month_scale_btn: 2628300,
            self.ui.cursor_scale_btn: -1,
        }
        self.ui.timespan_btns.buttonToggled.connect(self.set_plot_timerange)

        # Toggle "Cursor" button on plot-mouse interaction
        multi_axis_plot = self.ui.main_plot.plotItem
        multi_axis_plot.vb.menu = None
        multi_axis_plot.sigXRangeChangedManually.connect(self.ui.cursor_scale_btn.toggle)

        # Parse macros & arguments, then include them in startup
        input_file, startup_pvs = self.parse_macros_and_args(macros, args)
        if input_file:
            self.import_save_file(input_file)
        for pv in startup_pvs:
            if pv in self.curves_model:
                continue
            last_row = self.curves_model.rowCount() - 1
            index = self.curves_model.index(last_row, 0)
            self.curves_model.setData(index, pv, Qt.EditRole)

    def menu_items(self) -> dict:
        """Add export & import functionality to File menu"""
        return {"Export": (self.export_save_file, "Ctrl+S"), "Import": (self.import_save_file, "Ctrl+L")}

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

        # Add style to center checkboxes in table cells
        app.setStyle(CenterCheckStyle())

        # Adjust settings for main_spltr
        self.ui.main_spltr.setSizes([1, 200])
        self.ui.main_spltr.setCollapsible(0, False)
        self.ui.main_spltr.setStretchFactor(0, 1)

    def set_footer(self):
        """Set footer information for application. Includes logging, nodename,
        username, PID, git version, Archiver URL, and current datetime
        """
        self.logging_handler = LoggingHandler(self.ui.logger_lbl)
        logger.addHandler(self.logging_handler)
        logger.setLevel("NOTSET")

        self.ui.ftr_ver_lbl.setText(self.git_version())
        self.ui.ftr_node_lbl.setText(gethostname())
        self.ui.ftr_user_lbl.setText(getuser())
        self.ui.ftr_pid_lbl.setText(str(os.getpid()))
        self.ui.ftr_url_lbl.setText(os.getenv("PYDM_ARCHIVER_URL"))
        self.ui.ftr_time_lbl.channel = "ca://" + datetime_pv

    def parse_macros_and_args(self, macros: Dict[str, Union[str, list]], args: List[str]) -> Tuple[str, list]:
        """Parse user provided macros and args into lists of PVs to use on
        startup or which file to import on startup

        Parameters
        ----------
        macros : Dict[str, str | list]
            Dictionary containing all of the macros passed into PyDM
        args : List[str]
            List of all arguments passed into the application to be parsed

        Returns
        -------
        tuple
            A tuple containing the file to import from and the list of PVs to use on startup
        """
        # Default macros is None
        if not macros:
            macros = {}

        # Construct an argument parser for args
        trace_parser = argparse.ArgumentParser(
            prog="trace",
            description="Trace\nThis is a PyDM application used to display archived and live pv data.",
            epilog="Examples:\n\tpydm $PHYSICS_TOP/trace/main.py"
            + "\n\tbash $PHYSICS_TOP/trace/launch_trace.bash"
            + "\n\t%(prog)s"
            + "\n\t%(prog)s -i some_input_file.trc"
            + "\n\t%(prog)s -p SOME:PV:TO:PLOT OTHER:PV:TO:PLOT"
            + '\n\t%(prog)s -m \'{"PVS": ["FOO:CHANNEL", "BAR:CHANNEL", "f://{A}+{B}"]}\''
            + '\n\t%(prog)s -m "INPUT_FILE = trace/examples/FormulaExample.trc"',
            formatter_class=argparse.RawTextHelpFormatter,
        )
        trace_parser.add_argument("-V", "--version", action="version", version="%(prog)s " + self.git_version())
        trace_parser.add_argument(
            "-i",
            "--input_file",
            action=PathAction,
            nargs="?",
            default=[],
            help="Absolute file path to import from\nAlternatively can be provided as INPUT_FILE macro",
        )
        trace_parser.add_argument(
            "-p",
            "--pvs",
            nargs="*",
            default=[],
            help="Space-separated list of PVs to show on startup\nFormulas should be passed without spaces: "
            + "f://{A}+{B}\nAlternatively can be provided as PV or PVS macros",
        )
        trace_parser.add_argument(
            "-m",
            "--macro",
            default="",
            help="Mimic PyDM macro replacements to use. Should be in JSON object format."
            + "\nJSON Formatting Reminder:"
            + "\n\tJSON requires double quotes for strings, so you should wrap this"
            + "\n\twhole argument in single quotes.\n\t--or--"
            + "\n\tSpecify macro replacements as KEY=value pairs using a comma as a"
            + "\n\tdelimiter. If you want to uses spaces after the delimiters or around"
            + "\n\tthe '=' signs, wrap the entire set with quotes.",
        )

        # Parse arguments and ignore unknowns
        trace_args, unknown = trace_parser.parse_known_args(args)
        for u in unknown:
            if not u:
                continue
            logger.warning(f"Not using unknown arguments: {u}")

        # Parse any macros passed into trace
        if trace_args.macro:
            parsed_macros = parse_macro_string(trace_args.macro)
            macros.update(**parsed_macros)

        # Get the file to import from if one is provided. Prioritize args over macro
        input_file = ""
        if trace_args.input_file:
            # Need to unpack as PathAction returns a list
            input_file = trace_args.input_file[0]
        elif "INPUT_FILE" in macros:
            input_file = macros["INPUT_FILE"]

        # Get the list of PVs to show on startup
        startup_pvs = []
        for key in ("PV", "PVS"):
            if key in macros:
                val = macros[key]
                if isinstance(val, str):
                    startup_pvs.append(val)
                elif isinstance(val, list):
                    startup_pvs += val
        startup_pvs += trace_args.pvs

        # Remove duplicates from startup_pvs
        startup_pvs = list(dict.fromkeys(startup_pvs))

        return (input_file, startup_pvs)

    @staticmethod
    def git_version():
        """Get the current git tag for the project"""
        project_directory = __file__.rsplit("/", 1)[0]
        git_cmd = subprocess.run(
            f"cd {project_directory} && git describe --tags", text=True, shell=True, capture_output=True
        )
        return git_cmd.stdout.strip()

    @Slot()
    def resetPlot(self) -> None:
        """Reset the Axis model and the Curve model to empty states"""
        self.axis_table_model.set_model_axes()
        self.curves_model.set_model_curves()

    @Slot(QAbstractButton, bool)
    def set_plot_timerange(self, button: QAbstractButton, toggled: bool) -> None:
        """Slot to be called when a timespan setting button is pressed.
        This will enable autoscrolling along the x-axis and disable mouse
        controls. If the "Cursor" button is pressed, then autoscrolling is
        disabled and mouse controls are enabled.

        Parameters
        ----------
        button : QAbstractButton
            The timespan setting button pressed. Determines which timespan
            to set.
        toggled : bool
            Whether or not the associated button is toggled or not.
        """
        if not toggled:
            return

        logger.debug("Setting plot timerange")
        if button not in self.button_spans:
            logger.error(f"{button} is not a valid timespan button")
            return
        enable_scroll = button != self.ui.cursor_scale_btn
        self.timespan = self.button_spans[button]
        if enable_scroll:
            logger.debug(f"Enabling plot autoscroll for {self.timespan}s")
        else:
            logger.debug("Disabling plot autoscroll, using mouse controls")
        self.autoScroll(enable=enable_scroll)


class LoggingHandler(Handler):
    def __init__(self, logging_lbl: QLabel, level: int = 0) -> None:
        super().__init__(level)
        self.logging_lbl = logging_lbl

    def emit(self, record: LogRecord):
        """Any logs from the logger will be displayed on the logging label. If
        the log level is greater than 20 (INFO), then the level will be shown as
        well. Also checks if the logging label has been deleted.

        Parameters
        ----------
        record : LogRecord
            The logger's log record.
        """
        if isdeleted(self.logging_lbl):
            return
        log = record.msg
        if record.levelno > 20:
            log = f"[{record.levelname}] - {log}"
        self.logging_lbl.setText(log)
