from os import environ
from unittest.mock import Mock, patch

import pytest

from file_io import TraceFileHandler

DUMMY_ARCHIVER_URL = "http://dummy.archiver.url/retrieval"


@pytest.fixture
def file_handler(qapp):
    """Fixture for an instance of TraceFileHandler with a mocked plot.

    Yields
    ------
    An instance of TraceFileHandler.
    """
    mock_plot = Mock()
    with patch.dict(environ, {"PYDM_ARCHIVER_URL": DUMMY_ARCHIVER_URL}):
        with patch("file_io.file_handler.QMessageBox.warning", return_value=Mock()):
            yield TraceFileHandler(mock_plot)


def test_open_file_curves_signal_includes_formulas(file_handler, get_test_file, qtbot):
    """Test that opening a .trc file with formulas emits curves_signal with both
    regular curves and formula curves combined into a single list.

    Parameters
    ----------
    file_handler : fixture
        Instance of TraceFileHandler for testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    qtbot : fixture
        pytest-qt fixture for Qt testing

    Expectations
    ------------
    curves_signal is emitted once with a list whose length equals the number
    of regular curves plus the number of formulas in the file.
    """
    test_file = get_test_file("test_file.trc")

    with patch.dict(environ, {"PYDM_ARCHIVER_URL": DUMMY_ARCHIVER_URL}):
        with qtbot.wait_signal(file_handler.curves_signal) as blocker:
            file_handler.open_file(test_file)

    # test_file.trc has 2 regular curves + 1 formula
    received_curves = blocker.args[0]
    assert len(received_curves) == 3


def test_open_file_formula_entries_have_formula_key(file_handler, get_test_file, qtbot):
    """Test that formula entries in the emitted curves_signal have the 'formula' key.

    Parameters
    ----------
    file_handler : fixture
        Instance of TraceFileHandler for testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    qtbot : fixture
        pytest-qt fixture for Qt testing

    Expectations
    ------------
    Exactly one entry in curves_signal has a 'formula' key, and its value
    matches the formula string from the test file.
    """
    test_file = get_test_file("test_file.trc")

    with patch.dict(environ, {"PYDM_ARCHIVER_URL": DUMMY_ARCHIVER_URL}):
        with qtbot.wait_signal(file_handler.curves_signal) as blocker:
            file_handler.open_file(test_file)

    received_curves = blocker.args[0]
    formula_entries = [c for c in received_curves if "formula" in c]

    assert len(formula_entries) == 1
    assert formula_entries[0]["formula"] == "f://{x0}+{x1}"


def test_open_file_regular_curve_entries_have_channel_key(file_handler, get_test_file, qtbot):
    """Test that regular curve entries in the emitted curves_signal have the 'channel' key.

    Parameters
    ----------
    file_handler : fixture
        Instance of TraceFileHandler for testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    qtbot : fixture
        pytest-qt fixture for Qt testing

    Expectations
    ------------
    Exactly two entries in curves_signal have a 'channel' key, corresponding
    to the regular PV curves in the test file.
    """
    test_file = get_test_file("test_file.trc")

    with patch.dict(environ, {"PYDM_ARCHIVER_URL": DUMMY_ARCHIVER_URL}):
        with qtbot.wait_signal(file_handler.curves_signal) as blocker:
            file_handler.open_file(test_file)

    received_curves = blocker.args[0]
    channel_entries = [c for c in received_curves if "channel" in c]

    assert len(channel_entries) == 2


def test_open_file_formulas_appended_after_curves(file_handler, get_test_file, qtbot):
    """Test that formula entries appear after regular curve entries in curves_signal,
    reflecting the file_data["curves"] + file_data["formula"] concatenation order.

    Parameters
    ----------
    file_handler : fixture
        Instance of TraceFileHandler for testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    qtbot : fixture
        pytest-qt fixture for Qt testing

    Expectations
    ------------
    The first entries in curves_signal have 'channel' keys (regular curves),
    and the last entries have 'formula' keys (formula curves).
    """
    test_file = get_test_file("test_file.trc")

    with patch.dict(environ, {"PYDM_ARCHIVER_URL": DUMMY_ARCHIVER_URL}):
        with qtbot.wait_signal(file_handler.curves_signal) as blocker:
            file_handler.open_file(test_file)

    received_curves = blocker.args[0]

    assert "channel" in received_curves[0]
    assert "channel" in received_curves[1]
    assert "formula" in received_curves[2]


def test_open_file_formula_properties_match_trc_file(file_handler, get_test_file, qtbot):
    """Test that the formula entry in curves_signal contains all properties
    from the .trc file, including name, color, yAxisName, and curveDict.

    Parameters
    ----------
    file_handler : fixture
        Instance of TraceFileHandler for testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory
    qtbot : fixture
        pytest-qt fixture for Qt testing

    Expectations
    ------------
    The formula entry in curves_signal has the correct formula string, name,
    color, yAxisName, lineWidth, and curveDict matching the test file.
    """
    test_file = get_test_file("test_file.trc")

    with patch.dict(environ, {"PYDM_ARCHIVER_URL": DUMMY_ARCHIVER_URL}):
        with qtbot.wait_signal(file_handler.curves_signal) as blocker:
            file_handler.open_file(test_file)

    received_curves = blocker.args[0]
    formula_entry = next(c for c in received_curves if "formula" in c)

    assert formula_entry["name"] == "formula0"
    assert formula_entry["formula"] == "f://{x0}+{x1}"
    assert formula_entry["yAxisName"] == "Main Range Axis"
    assert formula_entry["color"] == "#00ff00"
    assert formula_entry["curveDict"] == {"x0": "KLYS:LI22:31:KVAC", "x1": "KLYS:LI22:41:KVAC"}
