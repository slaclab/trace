from qtpy.QtCore import Qt, QVariant

from main import TraceDisplay


def test_default_curve(qtrace: TraceDisplay):
    """Check default values for curve as represented in the table model"""
    curves_model = qtrace.curves_model

    row_actual = []
    row_expected = [
        QVariant(),
        Qt.Checked,
        Qt.Checked,
        "",
        "#008cf9",
        "Axis 1",
        "Direct",
        "Solid",
        "1px",
        "None",
        "10px",
        Qt.Checked,
        None,
    ]

    for col in range(curves_model.columnCount()):
        index = curves_model.index(0, col)
        role = Qt.CheckStateRole if col in curves_model.checkable_cols else Qt.DisplayRole
        data = curves_model.data(index, role)
        row_actual.append(data)

    assert row_actual == row_expected
