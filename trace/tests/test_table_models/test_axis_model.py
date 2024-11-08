from json import loads

import pytest
from qtpy.QtCore import Qt


def test_axis_table_model_qtmodeltester(qtmodeltester, qtrace):
    """Check the validity of the ArchiverAxisModel with pytest-qt

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
    qtmodeltester.check(qtrace.axis_table_model, force_py=True)


def test_default_axis(qtrace):
    """Check default values for axis as represented in the table model

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    The data in the initial row match expected data
    """
    model = qtrace.axis_table_model

    row_actual = []
    row_expected = ["Axis 1", "Left", None, -1.04, 1.04, Qt.Checked, Qt.Unchecked, Qt.Unchecked, None]

    for col in range(model.columnCount()):
        index = model.index(0, col)
        role = Qt.CheckStateRole if col in model.checkable_col else Qt.DisplayRole
        data = model.data(index, role)
        row_actual.append(data)

    assert row_actual == row_expected


def test_append_axis(qtrace):
    """Test appending new axes to the axis model

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    Appending to the model adds an axis, either with the given name or an
    incremented name
    """
    model = qtrace.axis_table_model
    model.append()
    model.append("FOOBAR")

    assert model.rowCount() == 3
    assert model.data(model.index(0, 0)) == "Axis 1"
    assert model.data(model.index(1, 0)) == "Axis 2"
    assert model.data(model.index(2, 0)) == "FOOBAR"


def test_remove_axis(qtrace):
    """Test appending new axes to the axis model

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    Appending to the model adds an axis, either with the given name or an
    incremented name
    """
    model = qtrace.axis_table_model
    model.removeAtIndex(model.index(0, 0))

    assert model.rowCount() == 1
    assert model.data(model.index(0, 0)) == "Axis 1"

    model.append("FOO")
    model.append("BAR")
    model.append("FOOBAR")

    model.removeAtIndex(model.index(1, 0))
    model.removeAxis("BAR")

    assert model.rowCount() == 2
    assert model.data(model.index(0, 0)) == "Axis 1"
    assert model.data(model.index(1, 0)) == "FOOBAR"


def test_set_model_axes(qtrace, get_test_file):
    """Test that setting ArchiverAxisModel.set_model_axes() actually sets the
    model with the expected y-axes

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory

    Expectations
    ------------
    Calling ArchiverAxisModel.set_model_axes() results in the model containing
    the set y-axis data
    """
    test_filename = get_test_file("test_file.trc")
    test_data = loads(test_filename.read_text())

    model = qtrace.axis_table_model
    model.set_model_axes(test_data["y-axes"])

    plot_data = qtrace.main_plot.getYAxes()
    for axis_test, axis_json in zip(test_data["y-axes"], plot_data):
        axis_actual = loads(axis_json)
        assert axis_test.items() <= axis_actual.items()


def test_set_model_axes_empty(qtrace, get_test_file):
    """Test that ArchiverAxisModel.set_model_axes() called with no arguments clears
    the model

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory

    Expectations
    ------------
    The ArchiverAxisModel will have no axes
    """
    test_filename = get_test_file("test_file.trc")
    test_data = loads(test_filename.read_text())

    model = qtrace.axis_table_model
    model.set_model_axes(test_data["y-axes"])
    model.set_model_axes()

    assert model.rowCount() == 0


@pytest.mark.parametrize(
    ["column", "data_test", "data_expected"],
    [
        (0, "FOO Axis", "FOO Axis"),
        (1, "right", "Right"),
        (2, "FOO Label", "FOO Label"),
        (3, -15.0, -15.0),
        (3, 20.0, 1.04),
        (4, -15.0, -1.04),
        (4, 20.0, 20.0),
        (5, Qt.Checked, Qt.Checked),
        (5, Qt.Unchecked, Qt.Unchecked),
        (6, Qt.Checked, Qt.Checked),
        (6, Qt.Unchecked, Qt.Unchecked),
    ],
)
def test_alter_axis_data(qtrace, column, data_test, data_expected):
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
    model = qtrace.axis_table_model

    index = model.index(0, column)
    role = Qt.CheckStateRole if column in model.checkable_col else Qt.EditRole

    model.setData(index, data_test, role)
    data_actual = index.data(role)

    assert data_expected == data_actual
