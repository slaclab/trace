import os
from os import getenv
from pathlib import Path
from unittest import mock

import numpy as np
import pytest
from qtpy.QtWidgets import QMenu

from pydm.application import PyDMApplication

from main import TraceDisplay
from config import logger

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def make_curve():
    """Fixture providing a factory for curve mocks that behave like TimePlotCurveItem.

    Returns
    -------
    A function make_curve(timestamps, values, min_x=None, max_x=None) that returns
    a MagicMock with data_buffer, points_accumulated, min_x, max_x, address, and units
    set from the given arguments.
    """

    def _make_curve(timestamps, values, min_x=None, max_x=None):
        ts = np.array(timestamps, dtype=float)
        vals = np.array(values, dtype=float)
        curve = mock.MagicMock()
        curve.data_buffer = np.vstack([ts, vals])
        curve.points_accumulated = len(ts)
        curve.min_x.return_value = min_x if min_x is not None else (ts[0] if len(ts) else 0.0)
        curve.max_x.return_value = max_x if max_x is not None else (ts[-1] if len(ts) else 0.0)
        curve.address = "FAKE:PV"
        curve.units = "eV"
        return curve

    return _make_curve


@pytest.fixture
def get_test_file():
    """Fixture to provide a helper function for getting test files.

    Returns
    -------
    A helper function to get file paths to test files.
    """

    def _get_test_file(file_name: str) -> Path:
        """Helper function to get file paths to test files.

        Parameters
        ----------
        file_name : str
            The name of the test file in the test_data directory

        Returns
        -------
        pathlib.Path
            Path the the test_data file that was requested
        """
        gh_workspace = getenv("GITHUB_WORKSPACE")
        if gh_workspace:
            base_path = Path(gh_workspace) / "trace" / "tests"
        else:
            base_path = Path(__file__).parent
        return base_path / "test_data" / file_name

    return _get_test_file


@pytest.fixture(scope="session")
def qapp(qapp_args):
    """Fixture for a PyDMApplication app instance.

    Parameters
    ----------
    qapp_args : list
        Arguments for the QApp.

    Yields
    -------
    An instance of PyDMApplication.
    """
    # Don't pass along the default app name we get from pytest-qt otherwise PyDM will misinterpret it as a ui file name
    if "pytest-qt-qapp" == qapp_args[0]:
        qapp_args.remove("pytest-qt-qapp")

    app = PyDMApplication(use_main_window=False, *qapp_args)
    yield app
    app.quit()


@pytest.fixture
def qtrace(qtbot, qapp):
    """Fixture for an instance of the TraceDisplay. Always uses an instance of
    PyDMApplication.

    Yields
    ------
    An instance of TraceDisplay.
    """
    # TraceDisplay.__init__ returns early when app.main_window is None (use_main_window=False).
    # Patch it with a MagicMock so build_ui() and configure_app() run normally.
    # construct_trace_menu is also patched because QMenu rejects a MagicMock parent.
    with mock.patch.object(qapp, "main_window", mock.MagicMock()):
        with mock.patch.object(TraceDisplay, "construct_trace_menu", return_value=QMenu()):
            trace = TraceDisplay()

    # updateXAxis would be called on application render; necessary for testing X-Axis
    trace.plot.updateXAxis(True)
    yield trace

    trace.close()
    qapp.processEvents()
    trace.deleteLater()


@pytest.fixture
def mock_logger():
    """Fixture to set up common mocks for logger.

    Yields
    ------
    An instance of the application's logger.
    """
    logger.debug = mock.Mock()
    logger.warning = mock.Mock()
    logger.error = mock.Mock()
    logger.info = mock.Mock()
    yield logger
