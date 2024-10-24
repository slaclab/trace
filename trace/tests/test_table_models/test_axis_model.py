from json import loads

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
    axis_model = qtrace.axis_table_model

    row_actual = []
    row_expected = ["Axis 1", "Left", None, -1.04, 1.04, Qt.Checked, Qt.Unchecked, Qt.Unchecked, None]

    for col in range(axis_model.columnCount()):
        index = axis_model.index(0, col)
        role = Qt.CheckStateRole if col in axis_model.checkable_col else Qt.DisplayRole
        data = axis_model.data(index, role)
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
    axis_model = qtrace.axis_table_model
    axis_model.append()
    axis_model.append("FOOBAR")

    assert axis_model.rowCount() == 3
    assert axis_model.data(axis_model.index(0, 0)) == "Axis 1"
    assert axis_model.data(axis_model.index(1, 0)) == "Axis 2"
    assert axis_model.data(axis_model.index(2, 0)) == "FOOBAR"


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
    axis_model = qtrace.axis_table_model
    axis_model.removeAtIndex(axis_model.index(0, 0))
    assert axis_model.rowCount() == 1
    assert axis_model.data(axis_model.index(0, 0)) == "Axis 1"

    axis_model.append("FOO")
    axis_model.append("BAR")
    axis_model.append("FOOBAR")

    axis_model.removeAtIndex(axis_model.index(1, 0))
    axis_model.removeAxis("BAR")

    assert axis_model.rowCount() == 2
    assert axis_model.data(axis_model.index(0, 0)) == "Axis 1"
    assert axis_model.data(axis_model.index(1, 0)) == "FOOBAR"


def test_set_model_axes(qtrace, get_test_file):
    """

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory

    Expectations
    ------------
    """
    test_filename = get_test_file("test_file.trc")
    test_data = loads(test_filename.read_text())

    qtrace.axis_table_model.set_model_axes(test_data["y-axes"])

    assert False


def test_alter_axis_data(qtrace):
    pass
