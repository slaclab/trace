import pytest
from qtpy.QtWidgets import QApplication
from trace.main import TraceDisplay


@pytest.fixture
def app(qtbot):
    test_app = QApplication([])
    yield test_app
    test_app.quit()


def test_atrace_fetch_data_from_table(app):
    TraceDisplay()
