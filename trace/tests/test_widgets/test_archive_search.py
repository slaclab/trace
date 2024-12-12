import os
from unittest.mock import MagicMock, patch

import pytest
from qtpy.QtGui import QDrag
from qtpy.QtCore import QUrl, QMimeData, QByteArray, QModelIndex
from qtpy.QtNetwork import QNetworkReply

from widgets.archive_search import ArchiveSearchWidget

DUMMY_ARCHIVER_URL = "dummy.archiver.url"


@pytest.fixture
def search_wid(qapp):
    """Fixture for an instance of the ArchiveSearchWidget.

    Yields
    ------
    An instance of ArchiveSearchWidget.
    """
    # Set PYDM_ARCHIVER_URL so tests have a predictable state
    with patch.dict(os.environ, {"PYDM_ARCHIVER_URL": DUMMY_ARCHIVER_URL}):
        yield ArchiveSearchWidget()


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


def test_archive_results_table_qtmodeltester(qtmodeltester, search_wid):
    """Check the validity of the ArchiveResultsTableModel with pytest-qt

    Parameters
    ----------
    qtmodeltester : fixture
        pytest-qt fixture used for testing the validity of AbstractItemModels
    search_wid : fixture
        Instance of ArchiveSearchWidget for application testing

    Expectations
    ------------
    qtmodeltester finds no issues with the model
    """
    qtmodeltester.check(search_wid.results_table_model, force_py=True)


@pytest.mark.parametrize(
    ("data_test", "data_expected"),
    (
        ("FOO:BAR:CHANNEL", "FOO:BAR:CHANNEL"),
        ("FOO:?:CHANNEL", "FOO:.:CHANNEL"),
        ("FOO:*:CHANNEL", "FOO:.*:CHANNEL"),
        ("FOO:%:CHANNEL", "FOO:.*:CHANNEL"),
    ),
)
@patch("qtpy.QtNetwork.QNetworkAccessManager.get")
def test_archive_search(mock_get, search_wid, data_test, data_expected):
    """Test that the ArchiveSearchWidget properly formats requests to the archiver appliance.

    Parameters
    ----------
    mock_get : mock.patch
        Mock qtpy.QtNetwork.QNetworkAccessManager.get to capture calls sent to the archiver
    search_wid : fixture
        Instance of ArchiveSearchWidget for testing
    data_test : str
        The text to search for
    data_expected : str
        The expected text sent in the archiver request

    Expectations
    ------------
    Wild card characters should be replaced and requests to the archiver should be properly formatted.
    """
    search_wid.search_box.setText(data_test)
    search_wid.search_button.click()

    url_string = f"{DUMMY_ARCHIVER_URL}/retrieval/bpl/searchForPVsRegex?regex=.*{data_expected}.*"
    mock_get.assert_called_once()
    reply_actual = mock_get.call_args.args[0]
    assert reply_actual.url() == QUrl(url_string)


def test_populate_results_list_success(search_wid):
    """Test case for populate_results_list method

    Parameters
    ----------
    search_wid : fixture
        Instance of ArchiveSearchWidget for testing

    Expectations
    ------------
    A QNetworkReply sent to populate_results_list should get parsed and PVs should be added to results_table_model
    """
    # Create a mock QNetworkReply with sample data
    sample_data = b"PV1 PV2 PV3"
    reply = create_dummy_reply(data=sample_data)

    # Assume self.results_table_model and self.loading_label are set up
    with patch.object(search_wid, "results_table_model") as mock_table_model, \
         patch.object(search_wid, "loading_label") as mock_loading_label:  # fmt: skip
        # Run the populate_results_list function
        search_wid.populate_results_list(reply)

        # Assertions to verify behavior
        mock_loading_label.hide.assert_called_once()
        mock_table_model.clear.assert_called_once()
        mock_table_model.replace_rows.assert_called_once_with(["PV1", "PV2", "PV3"])
        reply.deleteLater.assert_called_once()


def test_populate_results_list_error(search_wid):
    """Test case for populate_results_list method when the given QNetworkReply has an error

    Parameters
    ----------
    search_wid : fixture
        Instance of ArchiveSearchWidget for testing

    Expectations
    ------------
    The data in the QNetworkReply w/ error should be ignored and the logger should give a message
    """
    # Create a mock QNetworkReply that simulates an error
    error_reply = create_dummy_reply(error_code=QNetworkReply.UnknownServerError)

    # Assume self.results_table_model and self.loading_label are set up
    with patch.object(search_wid, "results_table_model") as mock_table_model, \
         patch.object(search_wid, "loading_label") as mock_loading_label, \
         patch("widgets.archive_search.logger.error") as mock_logger_error:  # fmt: skip
        # Run the populate_results_list function
        search_wid.populate_results_list(error_reply)

        # Assertions to verify behavior
        mock_loading_label.hide.assert_called_once()
        mock_table_model.clear.assert_not_called()  # Should not clear table on error
        mock_logger_error.assert_called_once_with(f"Could not retrieve archiver results due to: {error_reply.error()}")
        error_reply.deleteLater.assert_called_once()


def test_start_drag_action(search_wid):
    """Test ArchiveSearchWidget.startDragAction, used for dragging text to the main trace application

    Parameters
    ----------
    search_wid : fixture
        Instance of ArchiveSearchWidget for testing

    Expectations
    ------------
    The QDrag action is initialized properly and contains the right mime data
    """
    # Patch the QDrag and QMimeData classes to monitor their usage
    with patch.object(search_wid, "selectedPVs", return_value="PV1 PV2 PV3"), \
         patch.object(QMimeData, "setText") as mock_setText, \
         patch.object(QDrag, "setMimeData") as mock_setMimeData, \
         patch.object(QDrag, "exec_", return_value=None) as mock_exec:  # fmt: skip
        # Run the startDragAction method
        search_wid.startDragAction(supported_actions=None)

        # Assertions to verify behavior
        mock_setText.assert_called_once_with("PV1 PV2 PV3")
        mock_setMimeData.assert_called_once()
        mock_exec.assert_called_once()


def test_insert_button(search_wid):
    """Test ArchiveSearchWidget.insert_button widget

    Parameters
    ----------
    search_wid : fixture
        Instance of ArchiveSearchWidget for testing

    Expectations
    ------------
    Clicking the button results in the signal ArchiveSearchWidget.append_PVs_requested
    being emitted for all listeners. The signal should include the return value
    of ArchiveSearchWidget.selectedPVs
    """
    with patch.object(search_wid, "append_PVs_requested") as mock_append_signal, \
         patch.object(search_wid, "selectedPVs", return_value="PV1 PV2 PV3"):  # fmt: skip
        # Prompt the insertion by mimicing a user clicking the insert_button
        search_wid.insert_button.click()

        # Assertions to verify behavior
        mock_append_signal.emit.assert_called_once_with("PV1 PV2 PV3")


def test_result_view_double_click(search_wid):
    """Test double-clicking ArchiveSearchWidget.results_view

    Parameters
    ----------
    search_wid : fixture
        Instance of ArchiveSearchWidget for testing

    Expectations
    ------------
    Double-clicking the table view results in the signal ArchiveSearchWidget.append_PVs_requested
    being emitted for all listeners. The signal should include the return value
    of ArchiveSearchWidget.selectedPVs
    """
    with patch.object(search_wid, "append_PVs_requested") as mock_append_signal, \
         patch.object(search_wid, "selectedPVs", return_value="PV1 PV2 PV3"):  # fmt: skip
        # Prompt the insertion by mimicing a user double-clicking the table
        search_wid.results_view.doubleClicked.emit(QModelIndex())

        # Assertions to verify behavior
        mock_append_signal.emit.assert_called_once_with("PV1 PV2 PV3")
