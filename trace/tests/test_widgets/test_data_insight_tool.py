from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from qtpy.QtCore import Qt, QModelIndex

from widgets.data_insight_tool import (
    SEVERITY_MAP,
    CAGetThread,
    DataInsightTool,
    DataVisualizationModel,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def model(qapp):
    """Fixture for a bare DataVisualizationModel instance.

    Yields
    ------
    A DataVisualizationModel instance.
    """
    m = DataVisualizationModel()
    yield m
    m.deleteLater()
    qapp.processEvents()


@pytest.fixture
def dit(qapp, make_curve):
    """Fixture for a DataInsightTool with a mocked plot.

    The plot's curveAtIndex returns a curve mock with float-returning min_x/max_x
    so that get_data (triggered by Qt signals even when patched) does not raise.
    CAGetThread.start is suppressed to prevent real EPICS CA connections.

    Yields
    ------
    A DataInsightTool instance.
    """
    mock_plot = MagicMock()
    mock_plot._curves = []
    mock_plot.curveAtIndex.return_value = make_curve([], [], min_x=0.0, max_x=1e9)
    mock_plot.getXAxis.return_value = MagicMock(range=[0.0, 1e9])

    with patch.object(CAGetThread, "start"):
        tool = DataInsightTool(parent=None)
        tool._plot = mock_plot
        yield tool

    tool.close()
    qapp.processEvents()
    tool.deleteLater()


# ---------------------------------------------------------------------------
# DataVisualizationModel — QAbstractItemModel contract
# ---------------------------------------------------------------------------


def test_model_passes_qtmodeltester_empty(model, qtmodeltester):
    """An empty DataVisualizationModel should satisfy the QAbstractItemModel contract."""
    qtmodeltester.check(model)


def test_model_passes_qtmodeltester_populated(model, make_curve, qtmodeltester):
    """A populated DataVisualizationModel should satisfy the QAbstractItemModel contract."""
    model.set_live_data(make_curve([1_000_000.0, 1_000_001.0], [1.0, 2.0]), (1_000_000.0, 1_000_001.0))
    model.set_archive_data(_make_archive_dict([999_998.0, 999_999.0], [3.0, 4.0]))
    qtmodeltester.check(model)


# ---------------------------------------------------------------------------
# DataVisualizationModel — class-level attributes
# ---------------------------------------------------------------------------


def test_df_columns_class_attribute():
    """_df_columns should list all four expected column names."""
    assert DataVisualizationModel._df_columns == ["Datetime", "Value", "Severity", "Source"]


def test_initial_df_uses_df_columns(model):
    """The initial empty dataframe should have exactly the four expected column names."""
    assert list(model.df.columns) == ["Datetime", "Value", "Severity", "Source"]
    assert model.df.empty


# ---------------------------------------------------------------------------
# DataVisualizationModel — set_live_data
# ---------------------------------------------------------------------------


def test_set_live_data_populates_df(model, make_curve):
    """set_live_data with in-range data should insert rows into the model's df."""
    ts = [1_000_000.0, 1_000_001.0, 1_000_002.0]
    vals = [1.1, 2.2, 3.3]
    curve = make_curve(ts, vals)

    model.set_live_data(curve, (ts[0], ts[-1]))

    assert model.df.shape[0] == 3
    assert list(model.df["Source"]) == ["Live", "Live", "Live"]
    assert list(model.df["Severity"]) == ["NaN", "NaN", "NaN"]


def test_set_live_data_converts_timestamps_to_datetime(model, make_curve):
    """Datetime column must contain datetime objects, not raw floats."""
    ts = [1_000_000.0]
    curve = make_curve(ts, [42.0])

    model.set_live_data(curve, (ts[0], ts[0]))

    dt_value = model.df["Datetime"].iloc[0]
    assert isinstance(dt_value, datetime)
    assert dt_value == datetime.fromtimestamp(ts[0])


def test_set_live_data_filters_by_x_range(model, make_curve):
    """Only timestamps within x_range should be inserted."""
    ts = [1_000_000.0, 1_000_001.0, 1_000_002.0, 1_000_003.0]
    vals = [1.0, 2.0, 3.0, 4.0]
    curve = make_curve(ts, vals)

    model.set_live_data(curve, (1_000_001.0, 1_000_002.0))

    assert model.df.shape[0] == 2
    assert list(model.df["Value"]) == pytest.approx([2.0, 3.0])


def test_set_live_data_returns_early_when_no_points_accumulated(model, make_curve):
    """set_live_data should return early and leave df empty when points_accumulated == 0."""
    curve = make_curve([], [])
    curve.points_accumulated = 0

    model.set_live_data(curve, (0.0, 1e10))

    assert model.df.empty


def test_set_live_data_returns_early_when_no_points_in_range(model, make_curve):
    """set_live_data should leave the existing df unchanged when no timestamps fall within x_range."""
    ts = [1_000_000.0, 1_000_001.0]
    curve = make_curve(ts, [1.0, 2.0])

    # Seed the model so we can confirm the df is not cleared on a miss
    model.set_live_data(curve, (ts[0], ts[-1]))
    assert model.df.shape[0] == 2

    # Range is completely outside the buffer timestamps — df must be unchanged
    model.set_live_data(curve, (2_000_000.0, 3_000_000.0))

    assert model.df.shape[0] == 2


# ---------------------------------------------------------------------------
# DataVisualizationModel — set_archive_data
# ---------------------------------------------------------------------------


def _make_archive_dict(timestamps_secs, values, severities=None):
    """Build a data_dict in the format returned by the Archiver Appliance."""
    if severities is None:
        severities = [0] * len(timestamps_secs)
    data = [
        {"secs": int(ts), "nanos": int((ts % 1) * 1e9), "val": v, "severity": s}
        for ts, v, s in zip(timestamps_secs, values, severities)
    ]
    return [{"data": data}]


def test_set_archive_data_populates_df(model):
    """set_archive_data should insert rows from the archive reply dict."""
    ts = [1_000_000.0, 1_000_001.0]
    data_dict = _make_archive_dict(ts, [10.0, 20.0])

    model.set_archive_data(data_dict)

    assert model.df.shape[0] == 2
    assert list(model.df["Source"]) == ["Archive", "Archive"]


def test_set_archive_data_converts_secs_nanos_to_datetime(model):
    """Datetime column must be built from secs + nanos * 1e-9 and converted to datetime."""
    ts = 1_000_000.5  # 0.5 s = 500_000_000 nanos
    data_dict = _make_archive_dict([ts], [99.0])

    model.set_archive_data(data_dict)

    dt_value = model.df["Datetime"].iloc[0]
    assert isinstance(dt_value, datetime)
    assert abs((dt_value - datetime.fromtimestamp(ts)).total_seconds()) < 1e-6


def test_set_archive_data_maps_severity(model):
    """Severity integers should be mapped through SEVERITY_MAP."""
    ts = [1_000_000.0, 1_000_001.0, 1_000_002.0, 1_000_003.0]
    severities = [0, 1, 2, 3]
    data_dict = _make_archive_dict(ts, [0.0] * 4, severities)

    model.set_archive_data(data_dict)

    assert list(model.df["Severity"]) == [SEVERITY_MAP[s] for s in severities]


def test_set_archive_data_concatenates_when_df_already_has_data(model, make_curve):
    """set_archive_data should concatenate to an existing df, not overwrite it."""
    # Pre-populate with live data
    ts_live = [1_000_003.0]
    curve = make_curve(ts_live, [5.0])
    model.set_live_data(curve, (ts_live[0], ts_live[0]))
    assert model.df.shape[0] == 1

    ts_arch = [1_000_000.0, 1_000_001.0]
    data_dict = _make_archive_dict(ts_arch, [1.0, 2.0])
    model.set_archive_data(data_dict)

    assert model.df.shape[0] == 3


def test_set_archive_data_with_empty_data_does_not_modify_df(model, make_curve):
    """set_archive_data with an empty data list should leave the df unchanged."""
    model.set_live_data(make_curve([1_000_000.0], [1.0]), (1_000_000.0, 1_000_000.0))
    assert model.df.shape[0] == 1

    model.set_archive_data([{"data": []}])

    assert model.df.shape[0] == 1


# ---------------------------------------------------------------------------
# DataVisualizationModel — set_all_data (reset before populating)
# ---------------------------------------------------------------------------


def test_set_all_data_resets_model_before_populating(model, make_curve):
    """set_all_data should clear any stale data before populating with new data.

    Pre-seeding the model with one row then calling set_all_data for a different
    time range should leave only the new data in the model.
    """
    # Seed the model with stale data outside the upcoming x_range
    model.set_live_data(make_curve([999_999.0], [0.0]), (999_999.0, 999_999.0))
    assert model.df.shape[0] == 1

    ts = [1_000_000.0, 1_000_001.0]
    curve = make_curve(ts, [1.0, 2.0])

    with patch.object(CAGetThread, "start"):
        model.set_all_data(curve, (ts[0], ts[-1]))

    # Only new live data should remain; stale row must be gone
    assert model.df.shape[0] == 2
    assert all(model.df["Source"] == "Live")


def test_set_all_data_emits_reply_received_when_no_archive_needed(model, make_curve, qtbot):
    """reply_recieved should be emitted when x_range[0] > curve_range[0] (no archive request)."""
    # curve_range: [1_000_000, 1_000_002]; shift x_range start past curve_range[0]
    # so the archive branch is skipped and reply_recieved is emitted directly.
    ts = [1_000_000.0, 1_000_001.0, 1_000_002.0]
    curve = make_curve(ts, [1.0, 2.0, 3.0])

    with patch.object(CAGetThread, "start"):
        with qtbot.waitSignal(model.reply_recieved, timeout=1000):
            model.set_all_data(curve, (1_000_001.0, 1_000_002.0))


def test_set_all_data_requests_archive_data_when_x_range_precedes_curve(model, make_curve):
    """set_all_data should call request_archive_data when x_range[0] <= curve_range[0]."""
    ts = [1_000_000.0, 1_000_002.0]
    curve = make_curve(ts, [1.0, 2.0])
    # x_range starts before the curve, so archive data should be requested
    x_range = (999_000.0, 1_000_002.0)
    # left_ts = max(x_range[0], curve_range[0]) = max(999_000, 1_000_000) = 1_000_000
    expected_archive_range = (x_range[0], max(x_range[0], curve.min_x.return_value))

    with patch.object(CAGetThread, "start"), patch.object(model, "request_archive_data") as mock_request:
        model.set_all_data(curve, x_range)

    mock_request.assert_called_once_with(curve.address, expected_archive_range)


# ---------------------------------------------------------------------------
# DataVisualizationModel — QAbstractTableModel interface
# ---------------------------------------------------------------------------


def test_rowcount_reflects_populated_data(model, make_curve):
    """rowCount() should return the number of rows in the df after population."""
    model.set_live_data(make_curve([1_000_000.0, 1_000_001.0], [1.0, 2.0]), (1_000_000.0, 1_000_001.0))

    assert model.rowCount() == 2


def test_data_returns_string_for_display_role(model, make_curve):
    """data() with DisplayRole should return a string representation of the cell value."""
    model.set_live_data(make_curve([1_000_000.0], [42.0]), (1_000_000.0, 1_000_000.0))

    value_index = model.index(0, 1)  # Value column
    assert model.data(value_index, Qt.DisplayRole) == "42.0"


def test_data_returns_none_for_invalid_index(model):
    """data() should return None when given an invalid QModelIndex."""
    assert model.data(QModelIndex()) is None


# ---------------------------------------------------------------------------
# DataInsightTool — show() first-open behaviour
# ---------------------------------------------------------------------------


def test_show_loads_data_on_first_open(dit):
    """show() should call get_data() when unopened is True and there is ≥1 PV."""
    with patch.object(dit, "get_data") as mock_get:
        # Add the item while get_data is already patched so the currentIndexChanged
        # signal that fires on addItem does not invoke the real get_data.
        dit.pv_select_box.addItem("FAKE:PV1")
        mock_get.reset_mock()
        dit.show()

    mock_get.assert_called_once()
    assert dit.unopened is False


def test_show_does_not_reload_on_subsequent_opens(dit):
    """show() should not call get_data() after the first open."""
    with patch.object(dit, "get_data") as mock_get:
        dit.pv_select_box.addItem("FAKE:PV1")
        dit.unopened = False
        mock_get.reset_mock()
        dit.show()

    mock_get.assert_not_called()


def test_show_does_not_load_data_when_no_pvs(dit):
    """show() should not call get_data() when pv_select_box is empty."""
    assert dit.pv_select_box.count() == 0

    with patch.object(dit, "get_data") as mock_get:
        dit.show()

    mock_get.assert_not_called()
    # unopened should remain True because no data was loaded
    assert dit.unopened is True


# ---------------------------------------------------------------------------
# DataInsightTool — update_pv_select_box signal-blocking fix
# ---------------------------------------------------------------------------


def test_update_pv_select_box_populates_items(dit):
    """update_pv_select_box should fill the combobox with all ArchivePlotCurveItem addresses."""
    from pydm.widgets.archiver_time_plot import ArchivePlotCurveItem

    mock_curve = MagicMock(spec=ArchivePlotCurveItem)
    mock_curve.address = "FAKE:PV1"
    dit._plot._curves = [mock_curve]

    dit.update_pv_select_box()

    assert dit.pv_select_box.count() == 1
    assert dit.pv_select_box.itemText(0) == "FAKE:PV1"


def test_update_pv_select_box_unblocks_signals_after_add(dit):
    """Signals must be unblocked after addItems so that currentIndexChanged fires normally."""
    from pydm.widgets.archiver_time_plot import ArchivePlotCurveItem

    mock_curve = MagicMock(spec=ArchivePlotCurveItem)
    mock_curve.address = "FAKE:PV1"
    dit._plot._curves = [mock_curve]

    dit.update_pv_select_box()

    assert not dit.pv_select_box.signalsBlocked()


def test_update_pv_select_box_skips_non_archive_curves(dit):
    """Non-ArchivePlotCurveItem curves should not appear in the combobox."""
    from pydm.widgets.archiver_time_plot import ArchivePlotCurveItem

    archive_curve = MagicMock(spec=ArchivePlotCurveItem)
    archive_curve.address = "ARCHIVE:PV"
    non_archive_curve = MagicMock()  # plain MagicMock, not spec=ArchivePlotCurveItem
    dit._plot._curves = [archive_curve, non_archive_curve]

    dit.update_pv_select_box()

    assert dit.pv_select_box.count() == 1
    assert dit.pv_select_box.itemText(0) == "ARCHIVE:PV"
