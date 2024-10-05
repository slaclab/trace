import pytest

from widgets.table_widgets import ColorButton


@pytest.fixture
def color_btn():
    yield ColorButton()


def test_color_setter(color_btn: ColorButton):
    pass


def test_random_color(color_btn: ColorButton):
    pass


def test_index_color(color_btn: ColorButton):
    pass
