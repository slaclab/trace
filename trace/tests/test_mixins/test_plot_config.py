from json import loads

import pytest
from pyqtgraph import ViewBox
from qtpy.QtCore import Qt


def test_plot_setup(qtrace, get_test_file):
    """Test that TraceDisplay.plot_setup(), given a dict with valid keys,
    configures the plot's settings correctly. Uses data from /test_data/test_file.trc

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory

    Expectations
    ------------
    The plot's settings match the plot config data from test_file.trc .
    """
    test_file = get_test_file("test_file.trc")
    test_data = loads(test_file.read_text())["plot"]

    qtrace.plot_setup(test_data)

    assert qtrace.plot.to_dict().items() >= test_data.items()


@pytest.mark.parametrize("test_size, expected_size", ((-5, 1), (10, 10), (200, 99)))
def test_set_font_size(qtrace, test_size, expected_size):
    """Test that users can set the font size using the provided spinbox.

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    test_size : int
        The test value to set the font size spinbox to
    expected_size : int
        The expected font size after setting the spinbox's value

    Expectations
    ------------
    The X-Axis' font size should match the expected_size value.
    """
    qtrace.ui.xafs_spnbx.setValue(test_size)

    x_axis = qtrace.plot.getAxis("bottom")
    assert x_axis.style["tickFont"].pixelSize() == expected_size


@pytest.mark.parametrize(
    "test_text, expected_value", (("Rect", ViewBox.RectMode), ("Pan", ViewBox.PanMode), ("FOOBAR", ViewBox.RectMode))
)
def test_change_mouse_mode(qtrace, test_text, expected_value):
    """Test that users can set the plot's mouse mode using the provided combobox.

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    test_text : str
        The test value string to set the combobox to
    expected_value : int
        The expected MouseMode value for the main plot viewbox

    Expectations
    ------------
    The plot's MouseMode should match the expected_value.
    """
    qtrace.ui.mouse_mode_cmbbx.setCurrentText(test_text)

    vb = qtrace.plot.plotItem.getViewBox()
    assert vb.state["mouseMode"] == expected_value


@pytest.mark.parametrize("test_value", (-10, 5, 30, 200))
def test_auto_scroll(qtrace, test_value):
    """Test that users can set the plot's refresh interval using the provided
    spinbox. The value should only be set within the range [100, 60000].

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    test_value : int
        The test value to set the refresh interval spinbox to

    Expectations
    ------------
    If the value changes, then AutoScroll is enabled on the plot using the new
    interval within the set constraints.
    """
    if test_value == qtrace.ui.refresh_interval_spnbx.value():
        qtrace.ui.refresh_interval_spnbx.setValue(test_value)
        assert not qtrace.plot.auto_scroll_timer.isActive()
        return

    # Constrain test value to be between expected min and max
    constrained_value = min(max(test_value * 1000, 1000), 60000)
    qtrace.ui.refresh_interval_spnbx.setValue(test_value)
    assert qtrace.plot.auto_scroll_timer.interval() == constrained_value
    assert qtrace.plot.auto_scroll_timer.isActive()


@pytest.mark.parametrize("test_value", (-10, 50, 200, 300))
def test_change_opacity(qtrace, test_value):
    """Test that users can set the plot's gridline opacity using the provided
    slider. The value should only be set within the range [0, 255].

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    test_value : int
        The test value to set the opacity slider to

    Expectations
    ------------
    If the value changes, the plot's gridline opacity is set to the new value
    within the set constraints.
    """
    constrained_value = min(max(test_value, 0), 255)
    qtrace.ui.opacity_sldr.setValue(test_value)
    assert qtrace.plot.getPlotItem().ctrl.gridAlphaSlider.value() == constrained_value


def test_show_grid(qtrace, qtbot):
    """Test that users can enable the plot's gridlines using the provided checkboxes.

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    qtbot : fixture
        Mock user mouse movements

    Expectations
    ------------
    The plot's gridlines should only be enabled once the checkboxes' values are set.
    """
    x_chckbx = qtrace.ui.x_grid_chckbx
    y_chckbx = qtrace.ui.y_grid_chckbx

    qtbot.addWidget(x_chckbx)
    qtbot.addWidget(y_chckbx)
    assert not qtrace.plot.getShowXGrid() and not qtrace.plot.getShowYGrid()

    qtbot.mouseClick(x_chckbx, Qt.LeftButton)
    assert qtrace.plot.getShowXGrid() and not qtrace.plot.getShowYGrid()

    qtbot.mouseClick(y_chckbx, Qt.LeftButton)
    assert qtrace.plot.getShowXGrid() and qtrace.plot.getShowYGrid()

    qtbot.mouseClick(x_chckbx, Qt.LeftButton)
    qtbot.mouseClick(y_chckbx, Qt.LeftButton)
    assert not qtrace.plot.getShowXGrid() and not qtrace.plot.getShowYGrid()
