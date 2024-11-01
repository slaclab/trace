import faulthandler
from json import loads

import pytest
from qtpy.QtCore import Qt

from pydm.widgets.archiver_time_plot import FormulaCurveItem, ArchivePlotCurveItem

faulthandler.enable()


def test_curves_model_qtmodeltester(qtmodeltester, qtrace):
    """Check the validity of the ArchiverCurveModel with pytest-qt

    Parameters
    ----------
    qtmodeltester : fixture
        pytest-qt fixture used for testing the validity of AbstractItemModels
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    qtmodeltester finds no issues with the model
    """
    qtmodeltester.check(qtrace.curves_model, force_py=True)


def test_default_curve(qtrace):
    """Check default values for curve as represented in the table model

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    The data in the initial row match expected data
    """
    model = qtrace.curves_model

    row_actual = []
    row_expected = ["", Qt.Checked, Qt.Checked, "", "#008cf9", "Axis 1",
                    "Direct", "Solid", "1px", "None", "10px", Qt.Checked, None]  # fmt: skip

    for col in range(model.columnCount()):
        index = model.index(0, col)
        role = Qt.CheckStateRole if col in model.checkable_cols else Qt.DisplayRole
        data = model.data(index, role)
        row_actual.append(data)

    assert row_actual == row_expected


def test_contains(qtrace):
    """Test that __contains__ works and that the 'in' keyword works with the model

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    The 'in' keyword should correctly tell us if a curve with the requested name
    is a part of the model
    """
    model = qtrace.curves_model
    index = model.index(0, 0)
    model.setData(index, "FOO:CHANNEL", Qt.EditRole)

    assert "FOO:CHANNEL" in model
    assert None in model
    assert "BAR:CHANNEL" not in model


def test_append_curve(qtrace):
    """Test that append actually adds a curve to the model

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    The model should have 1 more curve after append is called
    """
    model = qtrace.curves_model
    assert model.rowCount() == 1

    model.append()
    assert model.rowCount() == 2

    model.append()
    assert model.rowCount() == 3


def test_remove_curve(qtrace):
    """Test that removeAtIndex actually removes the curve from the model

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    The removed object should no longer be in the model
    """
    model = qtrace.curves_model
    assert model.rowCount() == 1

    model.append("FOO:CHANNEL")
    assert model.rowCount() == 2 and "FOO:CHANNEL" in model

    index = model.index(0, 0)
    model.removeAtIndex(index)
    assert model.rowCount() == 1 and "FOO:CHANNEL" in model

    index = model.index(0, 0)
    model.removeAtIndex(index)
    assert model.rowCount() == 1 and "FOO:CHANNEL" in model


def test_set_model_curves(qtrace, get_test_file):
    """Test that setting ArchiverCurveModel.set_model_curves() actually sets the
    model with the expected curves

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory

    Expectations
    ------------
    Calling ArchiverCurveModel.set_model_curves() results in the model containing
    the set curves data
    """
    test_filename = get_test_file("test_file.trc")
    test_data = loads(test_filename.read_text())

    qtrace.curves_model.set_model_curves(test_data["curves"])

    assert "KLYS:LI22:31:KVAC" in qtrace.curves_model
    assert None in qtrace.curves_model
    assert "FOO:BAR:CHANNEL" not in qtrace.curves_model


@pytest.mark.parametrize(
    ["column", "data_test", "data_expected"],
    [
        (0, "FOO:Curve", "FOO:Curve"),
        (1, Qt.Unchecked, Qt.Unchecked),
        (2, Qt.Unchecked, Qt.Unchecked),
        (3, "FOO Label", "FOO Label"),
        (4, "lime", "lime"),
        (5, "Axis 2", "Axis 2"),
        (6, "left", "Step"),
        (7, 3, "Dot"),
        (8, 2, "2px"),
        (9, "star", "Star"),
        (10, 20, "20px"),
        (11, Qt.Unchecked, Qt.Unchecked),
    ],
)
def test_alter_curve_data(qtrace, column, data_test, data_expected):
    """Test that users can set data in the ArchiverAxisModel

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    column : int
        The column to set the test data in
    data_test : Any
        The test data to set for a given column
    data_expected : Any
        The expected value to be stored in the model for the given index

    Expectations
    ------------
    The given column and test data should result in the given expected data
    """
    model = qtrace.curves_model
    model.append()

    index = model.index(0, column)
    role = Qt.CheckStateRole if column in model.checkable_cols else Qt.EditRole

    model.setData(index, data_test, role)
    data_actual = index.data(role)

    assert data_actual == data_expected


def test_convert_curve_to_formula(qtrace):
    """Test that conversion from an ArchiverPlotCurveItem to a FormulaCurveItem

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    The selected curve object should be an instance of the expected class
    """
    model = qtrace.curves_model

    index = model.index(0, 0)
    model.setData(index, "f://5+1", Qt.EditRole)
    assert isinstance(model.curve_at_index(0), FormulaCurveItem)

    index = model.index(1, 0)
    model.setData(index, "f://{A} * 2", Qt.EditRole)
    assert isinstance(model.curve_at_index(1), FormulaCurveItem)


def test_convert_formula_to_curve(qtrace, mock_logger):
    """Test that conversion from a FormulaCurveItem to an ArchiverPlotCurveItem

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods

    Expectations
    ------------
    The selected curve object should be an instance of the expected class
    """
    model = qtrace.curves_model

    index = model.index(0, 0)
    model.setData(index, "f://{B}+1", Qt.EditRole)
    mock_logger.error.assert_called_once_with("B is an invalid variable name")

    model.setData(index, "f://5+1", Qt.EditRole)
    assert isinstance(model.curve_at_index(0), FormulaCurveItem)

    model.setData(index, "FOO:CHANNEL", Qt.EditRole)
    assert isinstance(model.curve_at_index(0), ArchivePlotCurveItem)


def test_recursive_formula(qtrace, mock_logger):
    """Test the recursive formula checker

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods

    Expectations
    ------------
    Users should be prevented from entering recursive formulas and an error should be printed to stdout
    """
    model = qtrace.curves_model

    index = model.index(0, 0)
    model.setData(index, "f://{A}+1", Qt.EditRole)
    mock_logger.error.assert_called_once_with("A is recursive")

    mock_logger.error.reset_mock()
    model.setData(index, "f://5+1", Qt.EditRole)

    model.setData(model.index(1, 0), "f://{A}+1", Qt.EditRole)
    model.setData(model.index(0, 0), "f://{B}+1", Qt.EditRole)
    mock_logger.error.assert_called_once_with("There was a recursive dependency somewhere")


@pytest.mark.parametrize(
    ["data_test", "data_expected"],
    [(None, "B"), ("L", "M"), ("Z", "AA"), ("LM", "LN"), ("AZ", "BA"), ("ZZZZ", "AAAAA")],
)
def test_next_header(qtrace, data_test, data_expected):
    """Test the row header generation works as expected

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    data_test : str
        The "last header" in the table to test against
    data_expected : str
        The expected header to be returned based on the "last header"

    Expectations
    ------------
    Row headers should be generated based on the previous header
    """
    model = qtrace.curves_model
    if data_test:
        model._row_names.append(data_test)

    data_actual = model.next_header()
    assert data_actual == data_expected


@pytest.mark.parametrize("enabled", [True, False])
def test_live_connection_status(qtrace, enabled):
    """Test that the model reflects a curve's live connection status

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    enabled : bool
        Enable/disable the live connection status; used as test data and
        expected value

    Expectations
    ------------
    When the curve's live connection status is disconnected, the table will
    disable the checkbox for fetching live data and make its background red
    """
    model = qtrace.curves_model
    model.setData(model.index(0, 0), "FOO:CHANNEL", Qt.EditRole)

    curve = model.curve_at_index(0)
    curve.live_channel_connection.emit(enabled)
    live_flags = model.flags(model.index(0, 1))

    assert bool(live_flags & Qt.ItemIsEnabled) == enabled


@pytest.mark.parametrize("enabled", [True, False])
def test_archive_connection_status(qtrace, enabled):
    """Test that the model reflects a curve's archive connection status

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    enabled : bool
        Enable/disable the archive connection status; used as test data and
        expected value

    Expectations
    ------------
    When the curve's archive connection status is disconnected, the table will
    disable the checkbox for fetching archive data and make its background red
    """
    model = qtrace.curves_model
    model.setData(model.index(0, 0), "FOO:CHANNEL", Qt.EditRole)

    curve = model.curve_at_index(0)
    curve.archive_channel_connection.emit(enabled)
    archive_flags = model.flags(model.index(0, 2))

    assert bool(archive_flags & Qt.ItemIsEnabled) == enabled


def test_set_axis_from_unit(qtrace):
    """Check that when a curve's units change, the curve is moved to an axis
    that reflects the new units.

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    The curve's unit changing should create a new axis. The curve should be
    attached to the new axis.
    """
    model = qtrace.curves_model
    curve = model.curve_at_index(0)
    model.setData(model.index(0, 0), "FOO:CHANNEL", Qt.EditRole)

    assert curve.y_axis_name == "Axis 1"

    curve.unitSignal.emit("foo unit")

    assert curve.y_axis_name == "foo unit"
