from qtpy.QtCore import Qt, QVariant

from main import TraceDisplay


def test_default_curve(qtrace: TraceDisplay):
    """Check default values for curve as represented in the table model"""
    curves_model = qtrace.curves_model

    row_actual = []
    row_expected = [QVariant(), Qt.Checked, Qt.Checked, "", "#008cf9", "Axis 1",
                    "Direct", "Solid", "1px", "None", "10px", Qt.Checked, None]  # fmt: skip

    for col in range(curves_model.columnCount()):
        index = curves_model.index(0, col)
        role = Qt.CheckStateRole if col in curves_model.checkable_cols else Qt.DisplayRole
        data = curves_model.data(index, role)
        row_actual.append(data)

    assert row_actual == row_expected


def test_contains(qtrace: TraceDisplay):
    pass


def test_append_curve(qtrace: TraceDisplay):
    pass


def test_remove_curve(qtrace: TraceDisplay):
    pass


def test_set_model_curves(qtrace: TraceDisplay):
    pass


def test_alter_curve_data(qtrace: TraceDisplay):
    pass


def test_convert_curve_to_formula(qtrace: TraceDisplay):
    pass


def test_convert_formula_to_curve(qtrace: TraceDisplay):
    pass


def test_invalid_formula(qtrace: TraceDisplay):
    pass


def test_recursive_formula(qtrace: TraceDisplay):
    pass


def test_next_header(qtrace: TraceDisplay):
    pass


def test_live_connection_status(qtrace: TraceDisplay):
    pass


def test_archive_connection_status(qtrace: TraceDisplay):
    pass


def test_set_axis_from_unit(qtrace: TraceDisplay):
    """Check that when a curve's units change, the curve is moved to an axis
    that reflects the new units.
    """
    pass
