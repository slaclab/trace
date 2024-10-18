from os import getenv
from pathlib import Path
from unittest import mock

import pytest

from pydm.application import PyDMApplication

from main import TraceDisplay
from config import logger


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

    yield PyDMApplication(use_main_window=False, *qapp_args)


@pytest.fixture
def qtrace(qapp):
    """Fixture for an instance of the TraceDisplay. Always uses an instance of
    PyDMApplication.

    Yields
    ------
    An instance of TraceDisplay.
    """
    trace = TraceDisplay()

    # updateXAxis would be called on application render; necessary for testing X-Axis
    trace.ui.main_plot.updateXAxis(True)

    yield trace


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
    yield logger
