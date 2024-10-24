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
    """Check default values for axis as represented in the table model"""
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
    pass


def test_remove_axis(qtrace):
    pass


def test_set_model_axes(qtrace):
    pass


def test_alter_axis_data(qtrace):
    pass
