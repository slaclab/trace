import os
import json
from unittest.mock import MagicMock, patch

import epics
import numpy as np
import pytest
from qtpy.QtCore import QByteArray
from qtpy.QtNetwork import QNetworkReply

from main import TraceDisplay
from widgets.data_insight_tool import DataInsightTool

DUMMY_ARCHIVER_URL = "dummy.archiver.url"


@pytest.fixture
def dit_wid(qtrace: TraceDisplay, monkeypatch, get_test_file):
    """Fixture for an instance of the DataInsightTool.

    Yields
    ------
    An instance of DataInsightTool.
    """
    # Populate the model with data and give the first curve a unit
    test_filename = get_test_file("test_file.trc")
    test_data = json.loads(test_filename.read_text())["curves"]

    qtrace.curves_model.set_model_curves(test_data)
    curve_0 = qtrace.curves_model.curve_at_index(0)
    curve_0.data = np.array([[6, 7, 8, 9], [100, 101, 102, 103, 104]])
    curve_0.units = test_data[0]["yAxisName"]
    curve_1 = qtrace.curves_model.curve_at_index(1)
    curve_1.data = np.array([[6, 7, 8, 9], [200, 201, 202, 203, 204]])

    def mock_caget(address: str, *args, **kwargs):
        if address.endswith("EGU") or address.endswith(".DESC"):
            return address

    monkeypatch.setattr(epics, "caget", mock_caget)

    # Set PYDM_ARCHIVER_URL so tests have a predictable state
    with patch.dict(os.environ, {"PYDM_ARCHIVER_URL": DUMMY_ARCHIVER_URL}):
        yield DataInsightTool(qtrace, qtrace.curves_model, qtrace.ui.main_plot)


def create_dummy_reply(data: bytes = b"", error_code=QNetworkReply.NoError):
    """Helper function to create a mock QNetworkReply with specified data and error code.

    Parameters
    ----------
    data : bytes
        Data for the dummy QNetworkReply to return
    error_code : QNetworkReply.NetworkError
        Error code for the dummy QNetworkReply to return, default is QNetworkReply.NoError
    """
    reply = MagicMock(spec=QNetworkReply)
    reply.error.return_value = error_code
    reply.readAll.return_value = QByteArray(data)
    return reply


def test_data_visualization_qtmodeltester(qtmodeltester, dit_wid):
    """Check the validity of the DataVisualizationModel with pytest-qt

    Parameters
    ----------
    qtmodeltester : fixture
        pytest-qt fixture used for testing the validity of AbstractItemModels
    dit_wid : fixture
        Instance of DataInsightTool for application testing

    Expectations
    ------------
    qtmodeltester finds no issues with the model
    """
    qtmodeltester.check(dit_wid.data_vis_model, force_py=True)


@pytest.mark.parametrize(
    ["curve_ind", "expected_meta"], ((0, "torr, KLYS:LI22:31:KVAC.DESC"), (1, "KLYS:LI22:41:KVAC.DESC"))
)
def test_set_meta_data(dit_wid, curve_ind, expected_meta):
    dit_wid.pv_select_box.setCurrentIndex(curve_ind)
    assert dit_wid.meta_data_label.text() == expected_meta


def test_get_data(dit_wid):
    pass


def test_export_data_to_file(dit_wid):
    pass


def test_model_get_live_data(dit_wid):
    pass


def test_model_get_archive_data(dit_wid):
    pass
