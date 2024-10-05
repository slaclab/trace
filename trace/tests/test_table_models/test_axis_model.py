from qtpy.QtCore import Qt

from main import TraceDisplay


def test_default_axis(qtrace: TraceDisplay):
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


def test_append_axis(qtrace: TraceDisplay):
    pass


def test_remove_axis(qtrace: TraceDisplay):
    pass


def test_set_model_axes(qtrace: TraceDisplay):
    pass


def test_alter_axis_data(qtrace: TraceDisplay):
    pass
