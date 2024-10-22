from json import loads
from unittest import mock

import pytest

from widgets.item_delegates import (
    ComboBoxDelegate,
    DeleteRowDelegate,
    ColorButtonDelegate,
)


def test_traces_table_delegates(qtrace):
    """Ensure that the traces_tbl's Item Delegates are set correctly.

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    All of the table's Item Delegates are what the user expects.
    """
    curves_model = qtrace.curves_model
    table_view = qtrace.ui.traces_tbl

    delegates = []
    for column in range(curves_model.columnCount()):
        delegate = table_view.itemDelegateForColumn(column)
        delegates.append(type(delegate) if delegate else None)
    expected = [
        None,
        None,
        None,
        None,
        ColorButtonDelegate,
        ComboBoxDelegate,
        ComboBoxDelegate,
        ComboBoxDelegate,
        ComboBoxDelegate,
        ComboBoxDelegate,
        ComboBoxDelegate,
        None,
        DeleteRowDelegate,
    ]
    assert delegates == expected


@pytest.mark.parametrize(
    ("test_data", "expected_calls"),
    (("FOO:BAR:CHANNEL", 1), ("FOO:CHANNEL, BAR:CHANNEL", 2), ("FOO:CHANNEL BAR:CHANNEL", 2)),
)
def test_insert_pvs(qtrace, test_data, expected_calls):
    """Test that insertPVs() calls curves_model.set_data the correct amount of
    times. Splits on whitespace or commas.

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    test_data : str
        Data that resembles what insertPVs() might recieve
    expected_calls : int
        The number of times curves_model.set_data() is expected to be called

    Expectations
    ------------
    curves_model.set_data gets called the expected number of times.
    """
    qtrace.curves_model.set_data = mock.Mock()

    qtrace.insertPVs(test_data)

    assert qtrace.curves_model.set_data.call_count == expected_calls


def test_formula_dialog(qtrace, get_test_file):
    test_filename = get_test_file("test_file.trc")
    test_data = loads(test_filename.read_text())

    qtrace.curves_model.set_model_curves(test_data["curves"])

    # TODO: Keep working on it
    assert False
