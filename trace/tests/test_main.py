import json
from pathlib import Path
from datetime import datetime, timedelta
from subprocess import CompletedProcess
from unittest.mock import patch


def test_defaults(qtrace):
    """Ensure that TraceDisplay's default values are set correctly.

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    All of the application's values are in an expected state.
    """
    # Timespan buttons: '1h' button should be checked
    assert qtrace.ui.timespan_btns.checkedButton() is qtrace.ui.hour_scale_btn

    # Check plot's timespan will be set to 1 hour immediately after init
    axis_range = [datetime.fromtimestamp(int(r)) for r in qtrace.ui.main_plot.getXAxis().range]
    assert axis_range[1] - axis_range[0] == timedelta(hours=1)

    # Curve model should have one hidden curve
    assert qtrace.curves_model.rowCount() == 1
    assert len(qtrace.ui.main_plot._curves) == 1

    # Axis model should have one axis
    assert len(qtrace.ui.main_plot._axes) == 1
    assert qtrace.axis_table_model.rowCount() == 1

    # Plot Config default values
    assert qtrace.ui.plot_title_edit.text() == ""
    assert qtrace.ui.x_grid_chckbx.isChecked() is False
    assert qtrace.ui.y_grid_chckbx.isChecked() is False
    assert qtrace.ui.legend_chckbx.isChecked() is False
    assert qtrace.ui.xafs_spnbx.value() == 12
    assert qtrace.ui.refresh_interval_spnbx.value() == 5
    assert qtrace.background_color_button.color.name() == "#ffffff"
    assert qtrace.mouse_mode_cmbbx.currentIndex() == 0
    assert qtrace.opacity_sldr.value() == 127
    assert qtrace.crosshair_chckbx.isChecked() is False


def test_timespan_buttons(qtbot, qtrace):
    """Confirm that the QButtonGroup timespan_btns contains the right buttons and
    they are connected to the correct slot

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    timespan_btns should contain all expected buttons and toggling buttons should emit buttonToggled
    """
    button_spans = {
        qtrace.ui.min_scale_btn: 60,
        qtrace.ui.hour_scale_btn: 3600,
        qtrace.ui.day_scale_btn: 86400,
        qtrace.ui.week_scale_btn: 604800,
        qtrace.ui.month_scale_btn: 2628300,
        qtrace.ui.cursor_scale_btn: -1,
    }
    assert qtrace.ui.timespan_btns.buttons() == list(button_spans.keys())

    # Check that the qtrace.ui.timespan_btns.buttonToggled signal is emitted
    for btn in button_spans.keys():
        with qtbot.waitSignal(qtrace.ui.timespan_btns.buttonToggled, timeout=100):
            btn.click()


@patch("pyqtgraph.exporters.ImageExporter.export")
@patch("qtpy.QtWidgets.QFileDialog.getSaveFileName")
def test_save_image_button_success(mock_get_save_filename, mock_export, qtbot, qtrace):
    """Test saving an image successfully

    Parameters
    ----------
    mock_get_save_filename : patch
        Mock qtpy.QtWidgets.QFileDialog.getSaveFileName to return an expected filename
    mock_export : patch
        Mock pyqtgraph.exporters.ImageExporter.export
    qtbot : fixture
        pytest-qt window for widget testing
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    When getSaveFileName returns a file path (accepted), export is triggered with that
    file path.
    """

    save_image_button = qtrace.ui.save_img_btn
    mock_get_save_filename.return_value = ("/fake/path.png", "PNG Files (*.png)")

    with qtbot.waitSignal(qtrace.ui.save_img_btn.clicked, timeout=100):
        save_image_button.click()

    mock_export.assert_called_once_with("/fake/path.png")


@patch("pyqtgraph.exporters.ImageExporter.export")
@patch("qtpy.QtWidgets.QFileDialog.getSaveFileName")
def test_save_image_button_cancelled(mock_get_save_filename, mock_export, qtbot, qtrace):
    """Test when user cancels file dialog (empty path)

    Parameters
    ----------
    mock_get_save_filename : patch
        Mock qtpy.QtWidgets.QFileDialog.getSaveFileName to return an expected filename
    mock_export : patch
        Mock pyqtgraph.exporters.ImageExporter.export
    qtbot : fixture
        pytest-qt window for widget testing
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    When getSaveFileName returns an empty string (rejected), export is not triggered.
    """
    save_image_button = qtrace.ui.save_img_btn
    mock_get_save_filename.return_value = ("", "")

    with qtbot.waitSignal(qtrace.ui.save_img_btn.clicked, timeout=100):
        save_image_button.click()

    mock_export.assert_not_called()


@patch("pyqtgraph.exporters.ImageExporter.export")
@patch("qtpy.QtWidgets.QFileDialog.getSaveFileName")
def test_save_image_button_error(mock_get_save_filename, mock_export, qtbot, qtrace, mock_logger):
    """Test handling of an export failure

    Parameters
    ----------
    mock_get_save_filename : patch
        Mock qtpy.QtWidgets.QFileDialog.getSaveFileName to return an expected filename
    mock_export : patch
        Mock pyqtgraph.exporters.ImageExporter.export
    qtbot : fixture
        pytest-qt window for widget testing
    qtrace : fixture
        Instance of TraceDisplay for application testing
    mock_logger: fixture
        Mock logger


    Expectations
    ------------
    When an error occurs when exporting, the error is logged.
    """
    save_image_button = qtrace.ui.save_img_btn
    mock_get_save_filename.return_value = ("/fake/path.png", "PNG Files (*.png)")
    mock_export.side_effect = Exception("Export failed!")
    with qtbot.waitSignal(qtrace.ui.save_img_btn.clicked, timeout=100):
        save_image_button.click()

    mock_logger.error.assert_called_with("Failed to save image: Export failed!")


def test_fetch_archive_button_success(qtbot, qtrace):
    """Test fetch archive button correctly prompts for archive request

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    qtrace : fixture
        Instance of TraceDisplay for application testing


    Expectations
    ------------
    When the button is clicked, an archive data request is queued and the flag is set to True.
    """
    fetch_archive_button = qtrace.ui.fetch_archive_btn

    with qtbot.waitSignal(fetch_archive_button.clicked, timeout=100):
        fetch_archive_button.click()

    assert qtrace.ui.main_plot._archive_request_queued == True


def test_fetch_archive_button_duplicate(qtbot, qtrace, mock_logger):
    """Test fetch archive button doesn't make an additional request if a request is already queued

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    qtrace : fixture
        Instance of TraceDisplay for application testing
    mock_logger: fixture
        Mock logger

    Expectations
    ------------
    When the button is clicked, but there is already a request, a duplicate shouldn't be done.
    """
    fetch_archive_button = qtrace.ui.fetch_archive_btn
    qtrace.ui.main_plot._archive_request_queued = True

    with qtbot.waitSignal(fetch_archive_button.clicked, timeout=100):
        fetch_archive_button.click()

    mock_logger.info.assert_called_with("Archive fetch is already queued")


def test_click_toggled_timespan_button(qtbot, qtrace):
    """Confirm that clicking the toggled button in timespan_btns does not emit
    the buttonToggled signal

    Parameters
    ----------
    qtbot : fixture
        pytest-qt window for widget testing
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    Clicking the toggled button should do nothing
    """
    qtrace.ui.hour_scale_btn.click()

    with qtbot.assertNotEmitted(qtrace.ui.timespan_btns.buttonToggled, wait=100):
        qtrace.ui.hour_scale_btn.click()


def test_parse_macros_and_args_file_and_pvs(qtrace):
    """Test that TraceDisplay.parse_macros_and_args correctly parses user inputted
    macros and arguments

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    All arguments and macros should be parsed as a tuple of PVs and a file; If
    a file is passed as a macro and an argument, the argument is prioritized
    """
    # Define macros and args for the test case
    macros = {"INPUT_FILE": "macros_file.trc"}
    args = ["--input_file", "args_file.trc", "--pvs", "PV1", "PV2", "--macro", '{"PVS": ["ADDITIONAL:PV"]}']

    # Call the function
    result = qtrace.parse_macros_and_args(macros, args)

    # Check the expected outcome
    expected_file = Path("args_file.trc").resolve()  # args input_file should take priority over macro
    expected_pvs = ["ADDITIONAL:PV", "PV1", "PV2"]

    assert result == (expected_file, expected_pvs)


def test_parse_macros_and_args_only_macros(qtrace):
    """Test that TraceDisplay.parse_macros_and_args correctly parses user inputted
    macros

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    All macros should be parsed as a tuple of PVs and a file
    """
    # Define macros and args with no additional PVs or input_file from args
    macros = {"PVS": ["MACRO_PV1", "MACRO_PV2"], "INPUT_FILE": "macros_file.trc"}
    args = []

    # Call the function
    result = qtrace.parse_macros_and_args(
        macros,
        args,
    )

    # Expected values when only macros are provided
    expected_file = "macros_file.trc"
    expected_pvs = ["MACRO_PV1", "MACRO_PV2"]

    assert result == (expected_file, expected_pvs)


def test_parse_macros_and_args_empty_input(qtrace):
    """Test that TraceDisplay.parse_macros_and_args works given empty arguments

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    The returned tuple should contain an empty string and an empty list
    """
    # No macros and no arguments provided
    macros = {}
    args = []

    # Call the function
    result = qtrace.parse_macros_and_args(macros, args)

    # Expected to return empty file and PVs list
    expected_file = ""
    expected_pvs = []

    assert result == (expected_file, expected_pvs)


@patch("subprocess.run")
def test_git_version(mock_run, qtrace):
    """Test that TraceDisplay.git_version gets the correct git tag

    Parameters
    ----------
    mock_run : mock.patch
        Mock subprocess.run to return an expected git tag
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    TraceDisplay.git_version should return the mocked git tag
    """
    # Define the expected output of the git command
    expected_tag = "R1.2.3"

    # Mock the subprocess.run call to return this output
    mock_run.return_value = CompletedProcess(args=["git describe --tags"], returncode=0, stdout=expected_tag, stderr="")

    # Call the git_version method and check the output
    result = qtrace.git_version()
    assert result == expected_tag


def test_reset_plot(qtrace, get_test_file):
    """Test that TraceDisplay.resetPlot sets the axis model and curve model to
    expected default states

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    get_test_file : fixture
        A fixture used to get test files from the test_data directory

    Expectations
    ------------
    TraceDisplay.resetPlot should set the axis model and curve model to expected
    default states
    """
    test_filename = get_test_file("test_file.trc")
    test_data = json.loads(test_filename.read_text())

    qtrace.curves_model.set_model_curves(test_data["curves"])
    qtrace.axis_table_model.set_model_axes(test_data["y-axes"])

    qtrace.resetPlot()

    assert qtrace.curves_model.rowCount() == 1
    assert qtrace.axis_table_model.rowCount() == 1


def test_set_plot_timerange_enable_autoscroll(qtrace, mock_logger):
    """Test that autoscrolling is enabled for valid non-cursor buttons

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods

    Expectations
    ------------
    TraceDisplay.timespan is set to the expected value, TraceDisplay.autoScroll
    gets called once, and the logger is given a debug message to print
    """
    button = qtrace.ui.min_scale_btn
    with patch.object(qtrace, "autoScroll") as mock_autoScroll:
        qtrace.set_plot_timerange(button, toggled=True)

    # Check that autoScroll was called with enable=True
    assert qtrace.timespan == 60
    mock_autoScroll.assert_called_once_with(enable=True)
    mock_logger.debug.assert_called_with("Enabling plot autoscroll for 60s")


def test_set_plot_timerange_disable_autoscroll(qtrace, mock_logger):
    """Test that autoscrolling is disabled when cursor button is toggled

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods

    Expectations
    ------------
    TraceDisplay.autoScroll gets called with 'False' and the logger is given a
    debug message to print
    """
    button = qtrace.ui.cursor_scale_btn
    with patch.object(qtrace, "autoScroll") as mock_autoScroll:
        qtrace.set_plot_timerange(button, toggled=True)

    # Check that autoScroll was called with enable=False
    assert qtrace.timespan == -1
    mock_autoScroll.assert_called_with(enable=False)
    mock_logger.debug.assert_called_with("Disabling plot autoscroll, using mouse controls")


def test_set_plot_timerange_not_toggled(qtrace, mock_logger):
    """Test that the function does nothing if toggled is False

    Parameters
    ----------
    qtrace : fixture
        Instance of TraceDisplay for application testing
    mock_logger : fixture
        A fixture used for mocking the logger's warning and error methods

    Expectations
    ------------
    Neither TraceDisplay.autoScroll or the logger are called
    """
    button = qtrace.ui.min_scale_btn
    with patch.object(qtrace, "autoScroll") as mock_autoScroll:
        qtrace.set_plot_timerange(button, toggled=False)

    # Check that autoScroll and logger.debug are not called
    mock_autoScroll.assert_not_called()
    mock_logger.debug.assert_not_called()
