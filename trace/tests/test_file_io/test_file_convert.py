import sys
import json
import subprocess
from os import environ
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from qtpy.QtGui import QColor

from file_io import TraceFileConverter

DUMMY_ARCHIVER_URL = "dummy.archiver.url"
SCRIPT_PATH = Path(__file__).parent.parent.parent / "file_io" / "trace_file_convert.py"


@pytest.fixture
def converter():
    """Fixture for an instance of the TraceFileConverter.

    Yields
    ------
    An instance of TraceFileConverter.
    """
    with patch.dict(environ, {"PYDM_ARCHIVER_URL": DUMMY_ARCHIVER_URL}):
        yield TraceFileConverter()


@pytest.mark.parametrize(("test_file_ext"), [".trc", ".xml"])
def test_import_and_convert(converter, get_test_file, test_file_ext):
    """Test that the TraceFileConverter.import_file properly imports and converts
    trace files and Java Archive Viewer files

    Parameters
    ----------
    converter : fixture
        Instance of TraceFileConverter for testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    test_file_ext : str
        The file extension to import, all test save files are named the same aside from the extension

    Expectations
    ------------
    The provided save file is returned and stored in TraceFileConverter.stored_data
    The data should be the same as trace/tests/test_data/test_file.trc
    """
    expected_filename = get_test_file("test_file.trc")
    test_filename = get_test_file("test_file" + test_file_ext)

    data_expected = json.loads(expected_filename.read_text())
    data_test = converter.import_file(test_filename)

    assert data_test == converter.stored_data
    assert data_test == data_expected


def test_import_and_convert_stp(converter, get_test_file):
    """Test that the TraceFileConverter.import_file imports and converts StripTool
    files

    Parameters
    ----------
    converter : fixture
        Instance of TraceFileConverter for testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory

    Expectations
    ------------
    The provided save file is returned and stored in TraceFileConverter.stored_data
    The data is similar to the data in trace/tests/test_data/test_file.trc, but not exactly the same
    """
    expected_filename = get_test_file("test_file.trc")
    test_filename = get_test_file("test_file.stp")

    data_expected = json.loads(expected_filename.read_text())
    data_test = converter.import_file(test_filename)

    assert data_test == converter.stored_data
    for curve_test, curve_expected in zip(data_test["curves"], data_expected["curves"]):
        assert curve_test["name"] == curve_expected["name"]
        assert curve_test["color"] == curve_expected["color"]
        assert curve_test["yAxisName"] == curve_expected["yAxisName"].replace(" ", "")
    assert data_test["time_axis"]["name"] == data_expected["time_axis"]["name"]
    assert data_test["time_axis"]["location"] == data_expected["time_axis"]["location"]


def test_import_missing_file(converter, get_test_file):
    """Test that the TraceFileConverter.import_file raises an error when the provided
    file does not exist

    Parameters
    ----------
    converter : fixture
        Instance of TraceFileConverter for testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory

    Expectations
    ------------
    TraceFileConverter.import_file raises a FileNotFound error
    """
    test_filename = get_test_file("nonexistent_file.trc")
    with pytest.raises(FileNotFoundError) as exc_info:
        converter.import_file(test_filename)
    assert exc_info.type is FileNotFoundError


@pytest.mark.parametrize(("filename"), ["test_file_no_curves.trc", "test_file_no_pvs.xml", "test_file_no_curves.stp"])
def test_import_no_curves(converter, get_test_file, filename):
    """Test that the TraceFileConverter.import_file raises an error when the provided
    file does not contain any curves

    Parameters
    ----------
    converter : fixture
        Instance of TraceFileConverter for testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    filename : str
        The name of the test file to import

    Expectations
    ------------
    TraceFileConverter.import_file raises a ValueError error
    """
    test_filename = get_test_file(filename)

    with pytest.raises(ValueError) as exc_info:
        converter.import_file(test_filename)
    assert exc_info.type is ValueError


def test_export(converter, get_test_file, tmp_path):
    """Test that the TraceFileConverter.export_file properly exports the given
    data to the given trace file

    Parameters
    ----------
    converter : fixture
        Instance of TraceFileConverter for testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    The given data is written to the given file
    """
    input_file = get_test_file("test_file.trc")
    test_data = json.loads(input_file.read_text())

    output_file = tmp_path / "output_file.trc"
    converter.export_file(output_file, test_data)

    assert json.loads(output_file.read_text()) == test_data


def test_export_no_suffix(converter, get_test_file, tmp_path):
    """Test that the TraceFileConverter.export_file properly exports files even
    if they're missing a suffix

    Parameters
    ----------
    converter : fixture
        Instance of TraceFileConverter for testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    The given data is written to the given file, but with the suffix '.trc'
    """
    input_file = get_test_file("test_file.trc")
    test_data = json.loads(input_file.read_text())

    output_file = tmp_path / "output_file"
    new_output_file = tmp_path / "output_file.trc"
    converter.export_file(output_file, test_data)

    assert json.loads(new_output_file.read_text()) == test_data


def test_export_bad_suffix(converter, get_test_file, tmp_path):
    """Test that the TraceFileConverter.export_file will raise an error if the
    given file has an invalid suffix (not '.trc')

    Parameters
    ----------
    converter : fixture
        Instance of TraceFileConverter for testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    TraceFileConverter.export_file raises a FileNotFoundError
    """
    input_file = get_test_file("test_file.trc")
    output_file = tmp_path / "bad_file_suffix.csv"

    converter.import_file(input_file)

    with pytest.raises(FileNotFoundError) as exc_info:
        converter.export_file(output_file)
    assert exc_info.type is FileNotFoundError


def test_export_no_data(converter, tmp_path):
    """Test that the TraceFileConverter.export_file will raise an error if there
    is no data to export

    Parameters
    ----------
    converter : fixture
        Instance of TraceFileConverter for testing
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    TraceFileConverter.export_file raises a ValueError
    """
    output_file = tmp_path / "bad_file.trc"

    with pytest.raises(ValueError) as exc_info:
        converter.export_file(output_file)
    assert exc_info.type is ValueError


@pytest.mark.parametrize(
    ("color_test", "color_expected"),
    (("-65536", QColor("#ff0000")), ("-16711936", QColor("#00ff00")), ("-16776961", QColor("#0000ff"))),
)
def test_srgb_to_qcolor(converter, color_test, color_expected):
    """Test that the TraceFileConverter.srgb_to_qColor correctly converts colors
    from the srgb format used by the Java Archive Viewer save files

    Parameters
    ----------
    converter : fixture
        Instance of TraceFileConverter for testing
    color_test : str
        A test srgb value to be converted
    color_expected : QColor
        The expected QColor object equivalent to the given color_test

    Expectations
    ------------
    The converter returns the expected QColor object
    """
    color_actual = converter.srgb_to_qColor(color_test)
    assert color_actual == color_expected


@pytest.mark.parametrize(
    ("color_test", "color_expected"),
    (([65535, 0, 0], QColor("#ff0000")), ([0, 65535, 0], QColor("#00ff00")), ([0, 0, 65535], QColor("#0000ff"))),
)
def test_xcolor_to_qcolor(converter, color_test, color_expected):
    """Test that the TraceFileConverter.srgb_to_qColor correctly converts colors
    from the xcolor format used by the StripTool save files

    Parameters
    ----------
    converter : fixture
        Instance of TraceFileConverter for testing
    color_test : List[int]
        A test xcolor value to be converted
    color_expected : QColor
        The expected QColor object equivalent to the given color_test

    Expectations
    ------------
    The converter returns the expected QColor object
    """
    color_actual = converter.xColor_to_qColor(color_test)
    assert color_actual == color_expected


def test_get_plot_data(converter):
    """Test that the TraceFileConverter.get_plot_data gets the correct data from
    the given plot item

    Parameters
    ----------
    converter : fixture
        Instance of TraceFileConverter for testing

    Expectations
    ------------
    Extracts the correct data from the plot object
    """
    # Create a mock plot object
    mock_plot = Mock()

    # Mock the x-axis range with example timestamps
    start_ts = datetime(2021, 10, 1, 12).timestamp()
    end_ts = datetime(2021, 10, 2, 12).timestamp()
    mock_plot.getXAxis.return_value.range = [start_ts, end_ts]

    # Mock the to_dict method for the plot
    mock_plot.to_dict.return_value = {"title": "Sample Plot"}

    # Mock y-axes data (as JSON strings)
    mock_y_axis_json = json.dumps({"label": "Y Axis 1", "unit": "A"})
    mock_plot.getYAxes.return_value = [mock_y_axis_json]

    # Mock the auto_scroll_timer is inactive
    mock_plot.auto_scroll_timer.isActive.return_value = False

    # Mock curve data with both channel and formula data
    mock_curve_with_channel = json.dumps({"channel": "test_channel", "name": "Curve 1"})
    mock_curve_with_formula = json.dumps({"formula": "x^2", "name": "Curve 2"})
    mock_curve_without_channel = json.dumps({"channel": None, "name": "Curve without channel"})

    # Return curves including both valid and edge cases
    mock_plot.getCurves.return_value = [
        mock_curve_with_channel,
        mock_curve_with_formula,
        mock_curve_without_channel,
    ]

    # Call the static method
    result = converter.get_plot_data(mock_plot)

    # Expected output dictionary
    expected_output = {
        "archiver_url": DUMMY_ARCHIVER_URL,
        "plot": {"title": "Sample Plot"},
        "time_axis": {
            "name": "Main Time Axis",
            "start": "2021-10-01 12:00:00",
            "end": "2021-10-02 12:00:00",
            "location": "bottom",
        },
        "y-axes": [{"label": "Y Axis 1", "unit": "A"}],
        "curves": [{"channel": "test_channel", "name": "Curve 1"}],
        "formula": [{"formula": "x^2", "name": "Curve 2"}],
    }

    # Assertions to check if the result matches expected output
    assert result["archiver_url"] == expected_output["archiver_url"]
    assert result["plot"] == expected_output["plot"]
    assert result["time_axis"] == expected_output["time_axis"]
    assert result["y-axes"] == expected_output["y-axes"]
    assert result["curves"] == expected_output["curves"]
    assert result["formula"] == expected_output["formula"]


def test_convert_cli(get_test_file, tmp_path):
    """Test that the TraceFileConverter can be run from the command line

    Parameters
    ----------
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    The process runs correctly and the provided output file contains the expected data
    """
    input_path = get_test_file("test_file.xml")
    output_path = tmp_path / "test_out.trc"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            str(input_path),  # Input file
            "--output_file",
            str(output_path),  # Output file
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert json.loads(output_path.read_text()) == json.loads(get_test_file("test_file.trc").read_text())


def test_convert_cli_overwrite(get_test_file, tmp_path):
    """Test that the TraceFileConverter command line tool's 'overwrite' flag works

    Parameters
    ----------
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    The existing output file does not get overwritten if the '--output-file' flag isn't included
    """
    input_path = get_test_file("test_file.xml")
    output_path = tmp_path / "test_out.trc"
    expected_data = get_test_file("test_file.trc").read_text()

    output_path.write_text("content")
    assert output_path.exists()

    run_kwargs = {
        "args": [
            sys.executable,
            str(SCRIPT_PATH),
            str(input_path),  # Input file
            "--output_file",
            str(output_path),  # Output file
        ],
        "capture_output": True,
        "text": True,
    }

    result = subprocess.run(**run_kwargs)
    assert "Output file exists but overwrite not enabled:" in result.stderr
    assert output_path.read_text() != expected_data

    run_kwargs["args"].append("--overwrite")
    result = subprocess.run(**run_kwargs)

    assert result.returncode == 0
    assert output_path.read_text() == expected_data


def test_convert_cli_clean(get_test_file, tmp_path):
    """Test that the TraceFileConverter command line tool's 'clean' flag works

    Parameters
    ----------
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    The input file does not get removed if the '--clean' flag isn't included
    """
    file_to_copy = get_test_file("test_file.xml")
    input_path = tmp_path / "test_in.xml"
    output_path = tmp_path / "test_out.trc"

    input_path.write_text(file_to_copy.read_text())
    assert input_path.exists()

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(input_path), "--output_file", str(output_path), "--clean"],
        capture_output=True,
        text=True,
    )

    assert not input_path.exists()
    assert result.returncode == 0
    assert json.loads(output_path.read_text()) == json.loads(get_test_file("test_file.trc").read_text())


def test_convert_cli_batch(get_test_file, tmp_path):
    """Test that the TraceFileConverter command line tool can convert multiple files at once

    Parameters
    ----------
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    The process runs correctly and the provided output files exist
    """
    output_xml_path = tmp_path / "test_out_xml.trc"
    output_stp_path = tmp_path / "test_out_stp.trc"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            str(get_test_file("test_file.xml")),  # Input files
            str(get_test_file("test_file.stp")),
            "--output_file",
            str(output_xml_path),  # Output files
            str(output_stp_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert output_xml_path.exists()
    assert output_stp_path.exists()
