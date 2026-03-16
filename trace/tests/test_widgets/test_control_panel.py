from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def control_panel(qtrace):
    """Fixture for the ControlPanel embedded in a TraceDisplay instance.

    Yields
    ------
    The ControlPanel instance from TraceDisplay.
    """
    yield qtrace.control_panel


@pytest.fixture
def control_panel_with_axis(control_panel):
    """Fixture for a ControlPanel with one real axis named 'Y-Axis 0'.

    Yields
    ------
    Tuple of (ControlPanel, AxisItem) for 'Y-Axis 0'.
    """
    axis_item = control_panel.add_empty_axis("Y-Axis 0")
    yield control_panel, axis_item


def test_set_curves_formula_calls_add_formula_curve(control_panel_with_axis):
    """Test that set_curves calls add_formula_curve when a formula entry is provided.

    Parameters
    ----------
    control_panel_with_axis : fixture
        A ControlPanel with an existing axis named 'Y-Axis 0'

    Expectations
    ------------
    When a curve dict with a 'formula' key is passed to set_curves,
    add_formula_curve should be called on the correct AxisItem with
    the formula string.
    """
    cp, axis_item = control_panel_with_axis
    formula = "f://{x1}+1"

    with patch.object(axis_item, "add_formula_curve", return_value=MagicMock()) as mock_add:
        cp.set_curves([{"formula": formula, "yAxisName": "Y-Axis 0"}])

    mock_add.assert_called_once_with(formula)


def test_set_curves_formula_uses_default_axis_when_yaxisname_missing(control_panel_with_axis):
    """Test that set_curves routes to 'Y-Axis 0' when yAxisName is absent from the curve dict.

    Parameters
    ----------
    control_panel_with_axis : fixture
        A ControlPanel with an existing axis named 'Y-Axis 0'

    Expectations
    ------------
    When a formula curve dict has no 'yAxisName' key, set_curves defaults
    to 'Y-Axis 0' and calls add_formula_curve on that axis.
    """
    cp, axis_item = control_panel_with_axis
    formula = "f://{x1}+1"

    with patch.object(axis_item, "add_formula_curve", return_value=MagicMock()) as mock_add:
        cp.set_curves([{"formula": formula}])

    mock_add.assert_called_once_with(formula)


def test_set_curves_formula_targets_named_axis(control_panel_with_axis, qtrace):
    """Test that set_curves adds the formula curve to the axis matching yAxisName.

    Parameters
    ----------
    control_panel_with_axis : fixture
        A ControlPanel with an existing axis named 'Y-Axis 0'
    qtrace : fixture
        The TraceDisplay instance

    Expectations
    ------------
    The formula is routed to the axis specified by yAxisName, not a
    different axis.
    """
    cp, axis_item = control_panel_with_axis
    other_axis = cp.add_empty_axis("Other Axis")

    formula = "f://{x1}*2"

    with patch.object(axis_item, "add_formula_curve", return_value=MagicMock()) as mock_target, \
         patch.object(other_axis, "add_formula_curve", return_value=MagicMock()) as mock_other:  # fmt: skip
        cp.set_curves([{"formula": formula, "yAxisName": "Y-Axis 0"}])

    mock_target.assert_called_once_with(formula)
    mock_other.assert_not_called()


def test_set_curves_formula_creates_axis_when_missing(control_panel_with_axis):
    """Test that set_curves creates a new axis when yAxisName does not exist.

    Parameters
    ----------
    control_panel_with_axis : fixture
        A ControlPanel with an existing axis (used so axis_list is non-empty
        and the trailing axis_list.itemAt() call in set_curves doesn't crash)

    Expectations
    ------------
    When a formula curve dict references an axis that doesn't exist,
    add_empty_axis is called and add_formula_curve is then called on
    the newly created axis.
    """
    cp, axis_item = control_panel_with_axis
    formula = "f://{x1}+{x2}"

    with patch.object(cp, "get_axis_item", return_value=None), \
         patch.object(cp, "add_empty_axis", return_value=axis_item) as mock_add_axis, \
         patch.object(axis_item, "add_formula_curve", return_value=MagicMock()) as mock_add_formula:  # fmt: skip
        cp.set_curves([{"formula": formula, "yAxisName": "Missing Axis"}])

    mock_add_axis.assert_called_once_with("Missing Axis")
    mock_add_formula.assert_called_once_with(formula)


def test_set_curves_channel_removes_channel_key_before_add_curve(control_panel_with_axis):
    """Test that the 'channel' key is removed from curve_dict before calling add_curve.

    Parameters
    ----------
    control_panel_with_axis : fixture
        A ControlPanel with an existing axis named 'Y-Axis 0'

    Expectations
    ------------
    add_curve is called with the PV name and the curve_dict, where the
    'channel' key has been deleted to avoid conflicts with y_channel.
    """
    cp, axis_item = control_panel_with_axis
    curve_dict = {"channel": "SOME:PV", "color": "#ff0000", "yAxisName": "Y-Axis 0"}

    with patch.object(axis_item, "add_curve", return_value=MagicMock()) as mock_add_curve:
        cp.set_curves([curve_dict])

    args = mock_add_curve.call_args
    pv_name_arg, dict_arg = args[0]

    assert pv_name_arg == "SOME:PV"
    assert "channel" not in dict_arg


def test_set_curves_mixed_channel_and_formula(control_panel_with_axis):
    """Test that set_curves correctly handles a mix of channel and formula entries.

    Parameters
    ----------
    control_panel_with_axis : fixture
        A ControlPanel with an existing axis named 'Y-Axis 0'

    Expectations
    ------------
    Each entry is routed correctly: channel entries call add_curve and
    formula entries call add_formula_curve, each exactly once.
    """
    cp, axis_item = control_panel_with_axis
    formula = "f://{x1}+{x2}"

    with patch.object(axis_item, "add_curve", return_value=MagicMock()) as mock_add_curve, \
         patch.object(axis_item, "add_formula_curve", return_value=MagicMock()) as mock_add_formula:  # fmt: skip
        cp.set_curves(
            [
                {"channel": "SOME:PV", "yAxisName": "Y-Axis 0"},
                {"formula": formula, "yAxisName": "Y-Axis 0"},
            ]
        )

    mock_add_curve.assert_called_once()
    mock_add_formula.assert_called_once_with(formula)
