import os
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import epics
import numpy as np
import pytest
from qtpy.QtCore import QByteArray
from qtpy.QtNetwork import QNetworkReply

from pydm.widgets.archiver_time_plot import ArchivePlotCurveItem

from main import TraceDisplay
from widgets.data_insight_tool import DataInsightTool, DataVisualizationModel

DUMMY_ARCHIVER_URL = "dummy.archiver.url"


CSV_TEST_DATA = (
    "Address: KLYS:LI22:31:KVAC\nUnit: torr\nDescription: KLYS:LI22:31:KVAC.DESC\n"
    + "Datetime,Value,Severity,Source\n6.0,100,NaN,Live\n7.0,101,NaN,Live\n"
    + "8.0,102,NaN,Live\n9.0,103,NaN,Live\n10.0,104,NaN,Live\n"
)
JSON_TEST_DATA = json.dumps(
    {
        "meta": {"Address": "KLYS:LI22:31:KVAC", "Unit": "torr", "Description": "KLYS:LI22:31:KVAC.DESC"},
        "data": [
            {"Datetime": 6.0, "Value": 100, "Severity": "NaN", "Source": "Live"},
            {"Datetime": 7.0, "Value": 101, "Severity": "NaN", "Source": "Live"},
            {"Datetime": 8.0, "Value": 102, "Severity": "NaN", "Source": "Live"},
            {"Datetime": 9.0, "Value": 103, "Severity": "NaN", "Source": "Live"},
            {"Datetime": 10.0, "Value": 104, "Severity": "NaN", "Source": "Live"},
        ],
    },
    indent=2,
)


ARCH_TEST_DATA = [
    {
        "data": [
            {"secs": 1, "nanos": 0, "val": 95, "severity": 0},
            {"secs": 2, "nanos": 0, "val": 96, "severity": 0},
            {"secs": 3, "nanos": 0, "val": 97, "severity": 0},
            {"secs": 4, "nanos": 0, "val": 98, "severity": 0},
            {"secs": 5, "nanos": 0, "val": 99, "severity": 0},
        ]
    }
]


@pytest.fixture
def dit_wid(qtrace: TraceDisplay):
    """Fixture for an instance of the DataInsightTool.

    Yields
    ------
    An instance of DataInsightTool.
    """
    # Set PYDM_ARCHIVER_URL so tests have a predictable state
    with patch.dict(os.environ, {"PYDM_ARCHIVER_URL": DUMMY_ARCHIVER_URL}):
        dit = DataInsightTool(qtrace, qtrace.curves_model, qtrace.ui.main_plot)
        yield dit

    dit.close()
    dit.deleteLater()


@pytest.fixture
def dit_model():
    """Fixture for an instance of the DataVisualizationModel.

    Yields
    ------
    An instance of DataVisualizationModel.
    """
    dvm = DataVisualizationModel()
    yield dvm
    dvm.deleteLater()


@pytest.fixture
def mock_curve():
    """Fixture for an instance of a mock ArchivePlotCurveItem object with preset
    values for all attributes the DataVisualizationModel uses.

    Yields
    ------
    An instance of ArchivePlotCurveItem.
    """
    curve_item = MagicMock(spec=ArchivePlotCurveItem)
    curve_item.address = "KLYS:LI22:31:KVAC"
    curve_item.units = "torr"
    curve_item.min_x.return_value = 6
    curve_item.max_x.return_value = 10
    curve_item.getBufferSize.return_value = 5
    curve_item.data_buffer = np.array([[6, 7, 8, 9, 10], [100, 101, 102, 103, 104]])

    yield curve_item


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


def test_set_meta_data(dit_wid, mock_curve, monkeypatch):
    """Test DataInsightTool.set_meta_data() is successfully called when the selected
    PV is changed, and that set_meta_data sets the meta data label to the correct value.

    Parameters
    ----------
    dit_wid : fixture
        Instance of DataInsightTool for application testing
    mock_curve : fixture
        A mock curve object with preset values for all attributes the DataVisualizationModel uses
    monkeypatch : fixture
        To override epics.caget

    Expectations
    ------------
    DataInsightTool.meta_data_label should contain the expected text for the given index
    """

    def mock_caget(address: str, *args, **kwargs):
        if address.endswith("EGU") or address.endswith(".DESC"):
            return address

    monkeypatch.setattr(epics, "caget", mock_caget)

    dit_wid.data_vis_model.set_all_data(mock_curve, (6, 9))
    dit_wid.set_meta_data()

    assert dit_wid.meta_data_label.text() == "torr, KLYS:LI22:31:KVAC.DESC"


@pytest.mark.parametrize(
    ("extension", "expected_data"),
    ((".csv", CSV_TEST_DATA), (".json", JSON_TEST_DATA)),
)
def test_export_data_success(dit_model, tmp_path, extension, expected_data):
    """Test DataVisualizationModel.export_data() successfully writes a file and it
    matches the expected output.

    Parameters
    ----------
    dit_model : fixture
        Instance of DataVisualizationModel for application testing
    tmp_path : fixture
         A fixture which will provide a temporary directory unique to each test function
    extension : str
        The file extension (and format) that to be exported
    expected_data : str
        The expected string value that should be saved in the exported file

    Expectations
    ------------
    DataInsightTool and DataVisualizationModel will make a file with the expected name and content.
    """
    # Construct testcase
    dit_model.address = "KLYS:LI22:31:KVAC"
    dit_model.unit = "torr"
    dit_model.description = "KLYS:LI22:31:KVAC.DESC"
    dit_model.df["Datetime"] = [6, 7, 8, 9, 10]
    dit_model.df["Datetime"] = dit_model.df["Datetime"].apply(datetime.fromtimestamp, tz=timezone.utc)
    dit_model.df["Value"] = [100, 101, 102, 103, 104]
    dit_model.df["Severity"] = ["NaN"] * 5
    dit_model.df["Source"] = ["Live"] * 5

    file = tmp_path / f"test_export_data_success{extension}"
    dit_model.export_data(file, extension)

    assert file.is_file()
    assert file.read_text() == expected_data


def test_export_data_dir(dit_model, tmp_path):
    """Test DataVisualizationModel.export_data() is interrupted when the provided filename
    is a directory.

    Parameters
    ----------
    dit_model : fixture
        Instance of DataVisualizationModel for application testing
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    No files/directories should be made and the logger should give a warning.
    """
    # Construct testcase
    dit_model.df["Datetime"] = [6, 7, 8, 9, 10]
    dit_model.df["Datetime"] = dit_model.df["Datetime"].apply(datetime.fromtimestamp, tz=timezone.utc)
    dit_model.df["Value"] = [100, 101, 102, 103, 104]
    dit_model.df["Severity"] = ["NaN"] * 5
    dit_model.df["Source"] = ["Live"] * 5

    with pytest.raises(IsADirectoryError) as exc_info:
        dit_model.export_data(tmp_path, "")
    assert exc_info.type is IsADirectoryError

    assert not tmp_path.is_file()


def test_export_data_invalid_extension(dit_model, tmp_path):
    """Test DataVisualizationModel.export_data() is interrupted when the provided filename
    has an extension other than *.csv, *.mat, or *.json . Needed to make a valid file after to prevent
    a recursive loop.

    Parameters
    ----------
    dit_model : fixture
        Instance of DataVisualizationModel for application testing
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    An error should be given when trying to make the *.xlsx file, but *.csv succeeds.
    """
    # Construct testcase
    dit_model.df["Datetime"] = [6, 7, 8, 9, 10]
    dit_model.df["Datetime"] = dit_model.df["Datetime"].apply(datetime.fromtimestamp, tz=timezone.utc)
    dit_model.df["Value"] = [100, 101, 102, 103, 104]
    dit_model.df["Severity"] = ["NaN"] * 5
    dit_model.df["Source"] = ["Live"] * 5

    file_xlsx = tmp_path / "test_export_save_file_invalid_extension.xlsx"

    with pytest.raises(ValueError) as exc_info:
        dit_model.export_data(file_xlsx, ".xlsx")
    assert exc_info.type is ValueError
    assert not file_xlsx.is_file()


@pytest.mark.parametrize(
    ("x_range", "expected_data"),
    (
        ((5, 11), ([6, 7, 8, 9, 10], [100, 101, 102, 103, 104])),
        ((7.5, 9.5), ([8, 9], [102, 103])),
    ),
)
def test_model_set_live_data(dit_model, x_range, expected_data, mock_curve):
    """Test DataVisualizationModel.set_live_data() stores the correct data from
    the curves_model into its DataFrame.

    Parameters
    ----------
    dit_model : fixture
        Instance of DataVisualizationModel for application testing
    curve_ind : int
        The index corresponding to a curve in the curves_model
    expected_data : tuple
        The expected data to be stored in the Datetime and Value columns of the DataFrame
    mock_curve : fixture
        A mock curve object with preset values for all attributes the DataVisualizationModel uses

    Expectations
    ------------
    DataVisualizationModel.df contains the expected Datetime and Value values for the given curve.
    """

    dit_model.set_live_data(mock_curve, x_range)

    assert dit_model.df["Datetime"].apply(datetime.timestamp).to_list() == expected_data[0]
    assert dit_model.df["Value"].to_list() == expected_data[1]


def test_model_get_archive_data_success(qtbot, dit_model, mock_logger):
    """Test DataVisualizationModel.get_archive_data() stores the correct data from
    the Archiver Appliance into its DataFrame.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    dit_model : fixture
        Instance of DataVisualizationModel for application testing
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods

    Expectations
    ------------
    DataVisualizationModel.recieve_archive_reply is emitted, logger.debug is not
    called, and DataVisualizationModel.df contains the expected Datetime and Value
    values for the given curve.
    """
    mock_logger.debug.reset_mock()
    reply_str = json.dumps(ARCH_TEST_DATA).encode()
    reply = create_dummy_reply(data=reply_str)

    with qtbot.waitSignal(dit_model.reply_recieved, timeout=100):
        dit_model.recieve_archive_reply(reply)

    mock_logger.debug.assert_not_called()
    assert dit_model.df["Datetime"].apply(datetime.timestamp).to_list() == [1, 2, 3, 4, 5]
    assert dit_model.df["Value"].to_list() == [95, 96, 97, 98, 99]


def test_model_get_archive_data_error(qtbot, dit_model, mock_logger):
    """Test DataVisualizationModel.get_archive_data() does nothing when an error
    is recieved from the Archiver Appliance.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    dit_model : fixture
        Instance of DataVisualizationModel for application testing
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods

    Expectations
    ------------
    DataVisualizationModel.recieve_archive_reply is emitted, logger.debug is called,
    and DataVisualizationModel.df does not contain any extra data.
    """
    mock_logger.debug.reset_mock()
    error_reply = create_dummy_reply(error_code=QNetworkReply.UnknownServerError)

    with qtbot.waitSignal(dit_model.reply_recieved, timeout=100):
        dit_model.recieve_archive_reply(error_reply)
    mock_logger.debug.assert_called_once()
