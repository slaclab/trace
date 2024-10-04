from main import TraceDisplay
from widgets.item_delegates import (
    ComboBoxDelegate,
    DeleteRowDelegate,
    ScientificNotationDelegate,
)


def test_axis_table_delegates(qtrace: TraceDisplay):
    """Ensure that the axis_tbl looks and functions as expected"""
    axis_model = qtrace.axis_table_model
    table_view = qtrace.ui.time_axis_tbl

    orientation_col = axis_model.getColumnIndex("Y-Axis Orientation")
    min_range_col = axis_model.getColumnIndex("Min Y Range")
    max_range_col = axis_model.getColumnIndex("Max Y Range")
    delete_col = axis_model.getColumnIndex("")

    assert type(table_view.itemDelegateForColumn(orientation_col)) is ComboBoxDelegate
    assert type(table_view.itemDelegateForColumn(min_range_col)) is ScientificNotationDelegate
    assert type(table_view.itemDelegateForColumn(max_range_col)) is ScientificNotationDelegate
    assert type(table_view.itemDelegateForColumn(delete_col)) is DeleteRowDelegate
