import datetime
from json import dumps, loads
from unittest import mock

import pytest
from qtpy.QtWidgets import QMessageBox

from mixins.file_io import IOTimeParser
from trace_file_convert import TraceFileConverter

FAKE_TIME = datetime.datetime(2024, 6, 30)


@pytest.fixture
def mock_qtrace(qtrace):
    """Fixture to set up common mocks for qtrace."""
    qtrace.axis_table_model.set_model_axes = mock.Mock()
    qtrace.curves_model.set_model_curves = mock.Mock()
    qtrace.plot_setup = mock.Mock()
    QMessageBox.warning = mock.Mock(return_value=QMessageBox.Yes)

    yield qtrace


@pytest.fixture
def time_parser():
    """Fixture for an instance of the IOTimeParser.

    Yields
    ------
    An instance of IOTimeParser.
    """
    yield IOTimeParser()


@pytest.fixture
def patch_datetime_now(monkeypatch):
    """Patch to override datetime.datetime.now so that it is an expected value
    that can be tested against.

    Parameters
    ----------
    monkeypatch : fixture
        To override datetime.datetime.now
    """

    class mydatetime(datetime.datetime):
        @classmethod
        def now(cls):
            return FAKE_TIME

    monkeypatch.setattr(datetime, "datetime", mydatetime)


@mock.patch("qtpy.QtWidgets.QFileDialog.getSaveFileName")
def test_export_save_file_success(mock_get_save_name, qtrace, tmp_path):
    """Test TraceDisplay.export_save_file() successfully writes a file and it
    matches the expected output.

    Parameters
    ----------
    mock_get_save_name : mock.patch
        Mock qtpy.QtWidgets.QFileDialog.getSaveFileName to return an expected file name
    qtrace : fixture
        Instance of TraceDisplay for application testing
    tmp_path : fixture
         A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    TraceDisplay and TraceFileConverter will make a file with the expected name and content.
    """
    # Construct testcase
    file = tmp_path / "test_export_save_file_success.trc"
    mock_get_save_name.return_value = (str(file), None)

    # Construct plot_data to compare against
    plot_data = TraceFileConverter.get_plot_data(qtrace.ui.main_plot)
    for obj in plot_data["y-axes"] + plot_data["curves"] + plot_data["formula"]:
        for k, v in obj.copy().items():
            if v is None:
                del obj[k]

    qtrace.export_save_file()
    assert file.is_file()
    assert file.read_text() == dumps(plot_data, indent=4)


@mock.patch("qtpy.QtWidgets.QFileDialog.getSaveFileName")
def test_export_save_file_dir(mock_get_save_name, qtrace, mock_logger, tmp_path):
    """Test TraceDisplay.export_save_file() is interrupted when the provided filename
    is a directory.

    Parameters
    ----------
    mock_get_save_name : mock.patch
        Mock qtpy.QtWidgets.QFileDialog.getSaveFileName to return an expected file name
    qtrace : fixture
        Instance of TraceDisplay for application testing
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    No files/directories should be made and the logger should give a warning.
    """
    # Construct testcase & mocks
    mock_get_save_name.return_value = (str(tmp_path), None)

    qtrace.export_save_file()
    mock_logger.warning.assert_called_once_with("No file name provided to export save file to")
    assert not tmp_path.is_file()


@mock.patch("qtpy.QtWidgets.QFileDialog.getSaveFileName")
def test_export_save_file_invalid_extension(mock_get_save_name, qtrace, mock_logger, tmp_path):
    """Test TraceDisplay.export_save_file() is interrupted when the provided filename
    has an extension other than *.trc . Needed to make a *.trc file after to prevent
    a recursive loop.

    Parameters
    ----------
    mock_get_save_name : mock.patch
        Mock qtpy.QtWidgets.QFileDialog.getSaveFileName to return an expected file name
    qtrace : fixture
        Instance of TraceDisplay for application testing
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    An error should be given when trying to make the *.csv file, but *.trc succeeds.
    """
    # Construct testcases & mocks
    file_csv = tmp_path / "test_export_save_file_invalid_extension.csv"
    file_trc = tmp_path / "test_export_save_file_invalid_extension.trc"
    mock_get_save_name.side_effect = [(str(file_csv), None), (str(file_trc), None)]

    qtrace.export_save_file()
    mock_logger.error.assert_called_once_with("Incorrect output file format: .csv")
    assert not file_csv.is_file()
    assert file_trc.is_file()


@pytest.mark.parametrize(("test_file_ext"), [".trc", ".xml", ".stp"])
def test_import_save_file_success(mock_qtrace, get_test_file, test_file_ext):
    """Test TraceDisplay.import_save_file() successfully opens a save file and
    attempts to setup the application correctly.

    Parameters
    ----------
    mock_qtrace : fixture
        Instance of TraceDisplay for application testing; some methods are mocked
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    test_file_ext : str
        The file extension to import, all test save files are named the same aside from the extension

    Expectations
    ------------
    TraceDisplay and TraceFileConverter will import the given file and update the application models.
    """
    test_filename = get_test_file("test_file" + test_file_ext)

    with mock.patch("qtpy.QtWidgets.QFileDialog.getOpenFileName") as mock_get_open_file_name:
        mock_get_open_file_name.return_value = (test_filename, None)
        mock_qtrace.import_save_file()

    # Check that mocks were called the correct amount
    mock_qtrace.axis_table_model.set_model_axes.assert_called_once()
    mock_qtrace.curves_model.set_model_curves.assert_called_once()
    mock_qtrace.plot_setup.assert_called_once()


@pytest.mark.parametrize(("test_file_name"), ["/test_data", "/test_data/not_a_file.trc"])
def test_import_save_file_directory(mock_qtrace, mock_logger, get_test_file, test_file_name):
    """Test TraceDisplay.import_save_file() is interrupted when the provided filename
    is either a directory or a nonexistent file.

    Parameters
    ----------
    mock_qtrace : fixture
        Instance of TraceDisplay for application testing; some methods are mocked
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    test_file_name : str
        The file name to test, should be directory or nonexistent file

    Expectations
    ------------
    The logger gives an warning and quits early.
    """
    test_filename = get_test_file(test_file_name)

    with mock.patch("qtpy.QtWidgets.QFileDialog.getOpenFileName") as mock_get_open_file_name:
        mock_get_open_file_name.return_value = (test_filename, None)
        mock_qtrace.import_save_file()

    # Check that mocks were called the correct amount
    mock_qtrace.axis_table_model.set_model_axes.assert_not_called()
    mock_qtrace.curves_model.set_model_curves.assert_not_called()
    mock_qtrace.plot_setup.assert_not_called()
    mock_logger.warning.assert_called_once_with(f"Attempted import is not a file: {test_filename}")


@pytest.mark.parametrize(("test_file_name"), ["test_file_no_curves.trc", "test_file_no_pvs.xml"])
def test_import_save_file_invalid(mock_qtrace, mock_logger, get_test_file, test_file_name):
    """Test TraceDisplay.import_save_file() is interrupted when the provided file
    contains no curves if it's a *.trc file or pvs if it's a *.xml file.

    Parameters
    ----------
    mock_qtrace : fixture
        Instance of TraceDisplay for application testing; some methods are mocked
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    test_file_name : str
        The file name to test, should be directory or nonexistent file

    Expectations
    ------------
    The logger gives an error and prompts the user to select another file.
    """
    # Set up test and mocks
    test_filename = get_test_file(test_file_name)
    known_good_file = get_test_file("test_file.trc")

    with mock.patch("qtpy.QtWidgets.QFileDialog.getOpenFileName") as mock_get_open_file_name:
        mock_get_open_file_name.side_effect = [(test_filename, None), (known_good_file, None)]
        mock_qtrace.import_save_file()

    # Check that mocks were called the correct amount
    mock_qtrace.axis_table_model.set_model_axes.assert_called_once()
    mock_qtrace.curves_model.set_model_curves.assert_called_once()
    mock_qtrace.plot_setup.assert_called_once()
    mock_logger.error.assert_called_once_with(f"Incorrect input file format: {test_filename}")


def test_import_save_file_bad_time(mock_qtrace, mock_logger, get_test_file):
    """Test TraceDisplay.import_save_file() is interrupted when the provided filename
    has x-axis times that are not parsable.

    Parameters
    ----------
    mock_qtrace : fixture
        Instance of TraceDisplay for application testing; some methods are mocked
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods
    get_test_file : fixture
        A fixture used to get test files from the test_data directory

    Expectations
    ------------
    A QMessageBox should be shown for the user to decide whether or not to continue.
    """
    # Create good data and bad data; TraceFileConverter.import_file returns bad_data then good_data
    test_filename = get_test_file("test_file.trc")
    good_data = loads(test_filename.read_text())
    bad_data = loads(test_filename.read_text())
    bad_data["time_axis"]["start"] = "6/15/2024"
    bad_data["time_axis"]["end"] = "now + 15h"

    with mock.patch("qtpy.QtWidgets.QFileDialog.getOpenFileName") as mock_get_open_file_name:
        with mock.patch("trace_file_convert.TraceFileConverter.import_file") as mock_import_file:
            mock_get_open_file_name.return_value = (test_filename, None)
            mock_import_file.side_effect = (bad_data, good_data)
            mock_qtrace.import_save_file()

    # Check that mocks were called the correct amount
    mock_qtrace.axis_table_model.set_model_axes.assert_called_once()
    mock_qtrace.curves_model.set_model_curves.assert_called_once()
    mock_qtrace.plot_setup.assert_called_once()
    mock_logger.error.assert_called_once_with("Time Axis end value is in an unexpected format.")


@mock.patch("qtpy.QtWidgets.QMessageBox.warning", return_value=QMessageBox.No)
def test_import_save_file_bad_hostname(mock_messagebox_warning, mock_qtrace, mock_logger, get_test_file):
    """Test TraceDisplay.import_save_file() is interrupted when the provided filename
    has a different Archiver URL than expected.

    Parameters
    ----------
    mock_messagebox_warning : mock.patch
        Mock qtpy.QtWidgets.QMessageBox.warning to return an expected button press
    mock_qtrace : fixture
        Instance of TraceDisplay for application testing; some methods are mocked
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods
    get_test_file : fixture
        A fixture used to get test files from the test_data directory

    Expectations
    ------------
    A QMessageBox should be shown for the user to decide whether or not to continue.
    """
    # Create bad data; TraceFileConverter.import_file will return bad_data
    test_filename = get_test_file("test_file.trc")
    bad_data = loads(test_filename.read_text())
    bad_data["archiver_url"] = "http://not.a.real.url"

    with mock.patch("qtpy.QtWidgets.QFileDialog.getOpenFileName") as mock_get_open_file_name:
        with mock.patch("trace_file_convert.TraceFileConverter.import_file") as mock_import_file:
            mock_get_open_file_name.return_value = (test_filename, None)
            mock_import_file.return_value = bad_data
            mock_qtrace.import_save_file()

    # Check that mocks were called the correct amount
    mock_qtrace.axis_table_model.set_model_axes.assert_not_called()
    mock_qtrace.curves_model.set_model_curves.assert_not_called()
    mock_qtrace.plot_setup.assert_not_called()
    mock_logger.warning.assert_called_once_with(
        "Attempting to import save file using different Archiver URL: not.a.real.url"
    )
    mock_messagebox_warning.assert_called_once()


@pytest.mark.parametrize(
    # fmt: off
    ("given", "expected"),
    [
        (("+1d", "now"), (None,)),                                      # Relative (+) & Now          -> Exception
        (("+1d", "+1h"), (None,)),                                      # Relative (+) & Relative (+) -> Exception
        (("+1d", "-1h"), (None,)),                                      # Relative (+) & Relative (-) -> Exception
        (("+1d", "2024-06-10"), (None,)),                               # Relative (+) & Absolute     -> Exception
        (("-1d", "now"), ((2024, 6, 29), (2024, 6, 30))),               # Relative (-) & Now
        (("-1d", "+1H"), ((2024, 6, 29), (2024, 6, 29, 1))),            # Relative (-) & Relative (+)
        (("-1d", "-1H"), ((2024, 6, 29), (2024, 6, 29, 23))),           # Relative (-) & Relative (-)
        (("-1d", "2024-06-10"), ((2024, 6, 9), (2024, 6, 10))),         # Relative (-) & Absolute
        (("2024-06-10", "now"), ((2024, 6, 10), (2024, 6, 30))),        # Absolute     & Now
        (("2024-06-10", "+1d"), ((2024, 6, 10), (2024, 6, 11))),        # Absolute     & Relative (+)
        (("2024-06-10", "-1d"), ((2024, 6, 10), (2024, 6, 29))),        # Absolute     & Relative (-)
        (("2024-06-10", "2024-06-20"),((2024, 6, 10), (2024, 6, 20)))   # Absolute     & Absolute
    ],
    # fmt: on
)
def test_time_parser(patch_datetime_now, time_parser, given, expected):
    """Test the IOTimeParser correctly parses start and end strings into datetimes.
    The datetimes may be relative to datetime.now or they may be absolute.

    Parameters
    ----------
    patch_datetime_now : fixture
        To override datetime.datetime.now
    time_parser : fixture
        Instance of IOTimeParser for application testing
    given : tuple
        The given start & end strings to test against
    expected : tuple
        The expected start & end datetimes to be returned. If None, then an
        exception is expected

    Expectations
    ------------
    IOTimeParser should be able to correctly parse start and end strings that
    are absolute or relative to the current time. If the start time is after the
    current time, that is impossible and will raise an exception. IOTimeParser
    should be able to determine what the base of the relative time should be.
    """
    # Test that expected exceptions get raised
    if expected[0] is None:
        with pytest.raises(ValueError) as exc_info:
            start_dt, end_dt = time_parser.parse_times(*given)
        assert exc_info.type is ValueError
    else:
        # If not expecting an exception, then check start and end datetimes
        start_dt, end_dt = time_parser.parse_times(*given)
        assert start_dt == datetime.datetime(*expected[0])
        assert end_dt == datetime.datetime(*expected[1])
