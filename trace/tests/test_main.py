from trace.main import TraceDisplay

import pytest
from qtpy.QtWidgets import QApplication


@pytest.fixture
def app(qtbot):
    test_app = QApplication([])
    yield test_app
    test_app.quit()


def test_atrace_fetch_data_from_table(app):
    TraceDisplay()
