import os
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import epics
import numpy as np
import pytest
from qtpy.QtCore import QByteArray
from qtpy.QtNetwork import QNetworkReply

from main import TraceDisplay
from widgets.data_insight_tool import DataInsightTool

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
    curve_0.data_buffer = np.array([[6, 7, 8, 9, 10], [100, 101, 102, 103, 104]])
    curve_0.units = test_data[0]["yAxisName"]
    curve_1 = qtrace.curves_model.curve_at_index(1)
    curve_1.data_buffer = np.array([[6, 7, 8, 9, 10], [200, 201, 202, 203, 204]])

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
    """Test DataInsightTool.set_meta_data() is successfully called when the selected
    PV is changed, and that set_meta_data sets the meta data label to the correct value.

    Parameters
    ----------
    dit_wid : fixture
        Instance of DataInsightTool for application testing
    curve_ind : int
        The index to set as the current index of the PV Selection Combobox
    expected_meta : str
        The expected text for the meta data label

    Expectations
    ------------
    DataInsightTool.meta_data_label should contain the expected text for the given index
    """
    dit_wid.pv_select_box.setCurrentIndex(curve_ind)
    assert dit_wid.meta_data_label.text() == expected_meta


@pytest.mark.parametrize(
    ("extension", "expected_data"),
    ((".csv", CSV_TEST_DATA), (".json", JSON_TEST_DATA)),
)
def test_export_data_success(dit_wid, tmp_path, extension, expected_data):
    """Test DataVisualizationModel.export_data() successfully writes a file and it
    matches the expected output.

    Parameters
    ----------
    dit_wid : fixture
        Instance of DataInsightTool for application testing
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
    model_df = dit_wid.data_vis_model.df
    model_df["Datetime"] = [6, 7, 8, 9, 10]
    model_df["Datetime"] = model_df["Datetime"].apply(datetime.fromtimestamp, tz=timezone.utc)
    model_df["Value"] = [100, 101, 102, 103, 104]
    model_df["Severity"] = ["NaN"] * 5
    model_df["Source"] = ["Live"] * 5
    file = tmp_path / f"test_export_data_success{extension}"
    dit_wid.data_vis_model.export_data(file, extension)

    assert file.is_file()
    assert file.read_text() == expected_data


def test_export_data_dir(dit_wid, tmp_path):
    """Test DataVisualizationModel.export_data() is interrupted when the provided filename
    is a directory.

    Parameters
    ----------
    dit_wid : fixture
        Instance of DataInsightTool for application testing
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    No files/directories should be made and the logger should give a warning.
    """
    # Construct testcase
    model_df = dit_wid.data_vis_model.df
    model_df["Datetime"] = [6, 7, 8, 9, 10]
    model_df["Datetime"] = model_df["Datetime"].apply(datetime.fromtimestamp, tz=timezone.utc)
    model_df["Value"] = [100, 101, 102, 103, 104]
    model_df["Severity"] = ["NaN"] * 5
    model_df["Source"] = ["Live"] * 5

    with pytest.raises(IsADirectoryError) as exc_info:
        dit_wid.data_vis_model.export_data(tmp_path, "")
    assert exc_info.type is IsADirectoryError

    assert not tmp_path.is_file()


def test_export_data_invalid_extension(dit_wid, tmp_path):
    """Test DataVisualizationModel.export_data() is interrupted when the provided filename
    has an extension other than *.csv, *.mat, or *.json . Needed to make a valid file after to prevent
    a recursive loop.

    Parameters
    ----------
    dit_wid : fixture
        Instance of DataInsightTool for application testing
    tmp_path : fixture
        A fixture which will provide a temporary directory unique to each test function

    Expectations
    ------------
    An error should be given when trying to make the *.xlsx file, but *.csv succeeds.
    """
    # Construct testcase
    model_df = dit_wid.data_vis_model.df
    model_df["Datetime"] = [6, 7, 8, 9, 10]
    model_df["Datetime"] = model_df["Datetime"].apply(datetime.fromtimestamp, tz=timezone.utc)
    model_df["Value"] = [100, 101, 102, 103, 104]
    model_df["Severity"] = ["NaN"] * 5
    model_df["Source"] = ["Live"] * 5

    file_xlsx = tmp_path / "test_export_save_file_invalid_extension.xlsx"

    with pytest.raises(ValueError) as exc_info:
        dit_wid.data_vis_model.export_data(file_xlsx, ".xlsx")
    assert exc_info.type is ValueError
    assert not file_xlsx.is_file()


@pytest.mark.parametrize(
    ("curve_ind", "x_range", "expected_data"),
    (
        (0, (5, 11), ([6, 7, 8, 9, 10], [100, 101, 102, 103, 104])),
        (0, (7.5, 9.5), ([8, 9], [102, 103])),
        (1, (6.5, 9.5), ([7, 8, 9], [201, 202, 203])),
    ),
)
def test_model_set_live_data(dit_wid, curve_ind, x_range, expected_data):
    """Test DataVisualizationModel.set_live_data() stores the correct data from
    the curves_model into its DataFrame.

    Parameters
    ----------
    dit_wid : fixture
        Instance of DataInsightTool for application testing
    curve_ind : int
        The index corresponding to a curve in the curves_model
    expected_data : tuple
        The expected data to be stored in the Datetime and Value columns of the DataFrame

    Expectations
    ------------
    DataVisualizationModel.df contains the expected Datetime and Value values for the given curve.
    """
    curve_item = dit_wid.curves_model.curve_at_index(curve_ind)
    mod = dit_wid.data_vis_model
    mod.set_live_data(curve_item, x_range)

    assert mod.df["Datetime"].apply(datetime.timestamp).to_list() == expected_data[0]
    assert mod.df["Value"].to_list() == expected_data[1]


def test_model_get_archive_data_success(qtbot, dit_wid, mock_logger):
    """Test DataVisualizationModel.get_archive_data() stores the correct data from
    the Archiver Appliance into its DataFrame.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    dit_wid : fixture
        Instance of DataInsightTool for application testing
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods

    Expectations
    ------------
    DataVisualizationModel.recieve_archive_reply is emitted, logger.debug is not
    called, and DataVisualizationModel.df contains the expected Datetime and Value
    values for the given curve.
    """
    reply_str = json.dumps(ARCH_TEST_DATA).encode()
    reply = create_dummy_reply(data=reply_str)

    mod = dit_wid.data_vis_model

    with qtbot.waitSignal(mod.reply_recieved, timeout=100):
        mod.recieve_archive_reply(reply)

    mock_logger.debug.assert_not_called()
    assert mod.df["Datetime"].apply(datetime.timestamp).to_list() == [1, 2, 3, 4, 5]
    assert mod.df["Value"].to_list() == [95, 96, 97, 98, 99]


def test_model_get_archive_data_error(qtbot, dit_wid, mock_logger):
    """Test DataVisualizationModel.get_archive_data() does nothing when an error
    is recieved from the Archiver Appliance.

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    dit_wid : fixture
        Instance of DataInsightTool for application testing
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods

    Expectations
    ------------
    DataVisualizationModel.recieve_archive_reply is emitted, logger.debug is called,
    and DataVisualizationModel.df does not contain any extra data.
    """
    error_reply = create_dummy_reply(error_code=QNetworkReply.UnknownServerError)

    with qtbot.waitSignal(dit_wid.data_vis_model.reply_recieved, timeout=100):
        dit_wid.data_vis_model.recieve_archive_reply(error_reply)
    mock_logger.debug.assert_called_once()
