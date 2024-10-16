from json import loads

import pytest
from pyqtgraph import ViewBox


def test_plot_setup(qtrace, get_test_file):
    test_file = get_test_file("test_file.trc")
    test_data = loads(test_file.read_text())["plot"]

    qtrace.plot_setup(test_data)

    assert qtrace.plot.to_dict() == test_data


@pytest.mark.parametrize("test_size, expected_size", ((-5, 1), (10, 10), (200, 99)))
def test_set_font_size(qtrace, test_size, expected_size):
    qtrace.ui.xafs_spnbx.setValue(test_size)
    x_axis = qtrace.plot.getAxis("bottom")

    assert x_axis.style["tickFont"].pixelSize() == expected_size


@pytest.mark.parametrize(
    "test_index, expected_value", ((0, ViewBox.RectMode), (1, ViewBox.PanMode), (3, ViewBox.RectMode))
)
def test_change_mouse_mode(qtrace, test_index, expected_value):
    qtrace.ui.mouse_mode_cmbbx.setCurrentIndex(test_index)

    vb = qtrace.plot.plotItem.getViewBox()
    assert vb.state["mouseMode"] == expected_value


def test_auto_scroll(qtrace):
    pass


def test_change_opacity(qtrace):
    pass


def test_show_x_grid(qtrace):
    pass


def test_show_y_grid(qtrace):
    pass
