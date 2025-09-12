from datetime import datetime

from pyqtgraph import ViewBox
from qtpy.QtGui import QFont, QColor
from qtpy.QtCore import Qt, Slot, Signal, QDateTime
from qtpy.QtWidgets import (
    QSlider,
    QWidget,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QDateTimeEdit,
)

from pydm.widgets import PyDMArchiverTimePlot

from config import logger
from widgets import ColorButton, SettingsTitle, SettingsRowItem
from widgets.curve_color_palette_modal import CurveColorPaletteModal


class PlotSettingsModal(QWidget):
    auto_scroll_interval_change = Signal(int)
    grid_alpha_change = Signal(int)
    set_all_y_axis_gridlines = Signal(bool)
    disable_autoscroll = Signal()
    sig_curve_palette_changed = Signal(str, bool)

    def __init__(self, parent: QWidget, plot: PyDMArchiverTimePlot):
        super().__init__(parent)
        self.setWindowFlag(Qt.Popup)

        self.plot = plot
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        title_label = SettingsTitle(self, "Plot Settings", size=14)
        main_layout.addWidget(title_label)

        self.plot_title_line_edit = QLineEdit()
        self.plot_title_line_edit.setPlaceholderText("Enter Title")
        self.plot_title_line_edit.textChanged.connect(self.plot.setPlotTitle)
        self.plot.plotItem.titleLabel.anchor((0.5, 0), (0.5, 0))  # Center title
        plot_title_row = SettingsRowItem(self, "Title", self.plot_title_line_edit)
        main_layout.addLayout(plot_title_row)

        self.legend_checkbox = QCheckBox(self)
        self.legend_checkbox.checkStateChanged.connect(lambda check: self.plot.setShowLegend(bool(check)))
        self.legend_checkbox.setChecked(True)  # legend on by default
        legend_row = SettingsRowItem(self, "Show Legend", self.legend_checkbox)
        main_layout.addLayout(legend_row)

        self.mouse_mode_combo = QComboBox(self)
        self.mouse_mode_combo.addItems(["Rect", "Pan"])
        self.mouse_mode_combo.currentTextChanged.connect(self.plot.plotItem.changeMouseMode)
        mouse_mode_row = SettingsRowItem(self, "Mouse Mode", self.mouse_mode_combo)
        main_layout.addLayout(mouse_mode_row)

        self.as_interval_spinbox = QSpinBox(self)
        self.as_interval_spinbox.setValue(5)
        self.as_interval_spinbox.setMinimum(1)
        self.as_interval_spinbox.setMaximum(60)
        self.as_interval_spinbox.setSuffix(" s")
        self.as_interval_spinbox.valueChanged.connect(self.auto_scroll_interval_change.emit)
        as_interval_row = SettingsRowItem(self, "Autoscroll Interval", self.as_interval_spinbox)
        main_layout.addLayout(as_interval_row)

        self.start_datetime = QDateTimeEdit(self)
        self.start_datetime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.start_datetime.setCalendarPopup(True)
        self.start_datetime.dateTimeChanged.connect(lambda qdt: self.set_time_axis_range((qdt, None)))
        start_dt_row = SettingsRowItem(self, "Start Time", self.start_datetime)
        main_layout.addLayout(start_dt_row)

        self.end_datetime = QDateTimeEdit(self)
        self.end_datetime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.end_datetime.setCalendarPopup(True)
        self.end_datetime.dateTimeChanged.connect(lambda qdt: self.set_time_axis_range((None, qdt)))
        end_dt_row = SettingsRowItem(self, "End Time", self.end_datetime)
        main_layout.addLayout(end_dt_row)

        self.crosshair_checkbox = QCheckBox(self)
        self.crosshair_checkbox.checkStateChanged.connect(lambda check: self.plot.enableCrosshair(check, 100, 100))
        crosshair_row = SettingsRowItem(self, "Show Crosshair", self.crosshair_checkbox)
        main_layout.addLayout(crosshair_row)

        appearance_label = SettingsTitle(self, "Appearance")
        main_layout.addWidget(appearance_label)

        self.background_button = ColorButton(parent=self, color="white")
        self.background_button.color_changed.connect(self.plot.setBackgroundColor)
        background_row = SettingsRowItem(self, "  Background Color", self.background_button)
        main_layout.addLayout(background_row)

        self.palette_modal = CurveColorPaletteModal(self)
        self.curve_palette_button = QPushButton("Select")
        self.curve_palette_button.clicked.connect(self.palette_modal.show)
        self.palette_modal.sig_palette_changed.connect(self.sig_curve_palette_changed.emit)
        palette_row = SettingsRowItem(self, "  Curve Palette", self.curve_palette_button)
        main_layout.addLayout(palette_row)

        axis_tick_font_size_spinbox = QSpinBox(self)
        axis_tick_font_size_spinbox.setValue(12)
        axis_tick_font_size_spinbox.setSuffix(" pt")
        axis_tick_font_size_spinbox.valueChanged.connect(self.set_axis_tick_font_size)
        axis_tick_font_size_row = SettingsRowItem(self, "  Axis Tick Font Size", axis_tick_font_size_spinbox)
        main_layout.addLayout(axis_tick_font_size_row)

        self.x_grid_checkbox = QCheckBox(self)
        self.x_grid_checkbox.checkStateChanged.connect(self.show_x_grid)
        x_grid_row = SettingsRowItem(self, "  X Axis Gridline", self.x_grid_checkbox)
        main_layout.addLayout(x_grid_row)

        self.y_grid_checkbox = QCheckBox(self)
        self.y_grid_checkbox.checkStateChanged.connect(self.show_y_grid)
        y_grid_row = SettingsRowItem(self, "  All Y Axis Gridlines", self.y_grid_checkbox)
        main_layout.addLayout(y_grid_row)

        self.grid_opacity_slider = QSlider(self)
        self.grid_opacity_slider.setOrientation(Qt.Horizontal)
        self.grid_opacity_slider.setMaximum(255)
        self.grid_opacity_slider.setValue(127)
        self.grid_opacity_slider.setSingleStep(32)
        self.grid_opacity_slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.grid_opacity_slider.valueChanged.connect(self.change_gridline_opacity)
        grid_opacity_row = SettingsRowItem(self, "  Gridline Opacity", self.grid_opacity_slider)
        main_layout.addLayout(grid_opacity_row)

        plot_viewbox = self.plot.plotItem.vb
        plot_viewbox.sigXRangeChanged.connect(self.set_axis_datetimes)
        plot_viewbox.sigRangeChangedManually.connect(lambda *_: self.set_axis_datetimes())

    def set_default_curve_palette(self):
        self.sig_curve_palette_changed.emit(self.curve_palette_button.currentText())

    @property
    def auto_scroll_interval(self):
        interval = self.as_interval_spinbox.value()
        interval *= 1000  # Convert to milliseconds
        return interval

    @property
    def x_grid_visible(self):
        return self.x_grid_checkbox.isChecked()

    @property
    def gridline_opacity(self):
        opacity = self.grid_opacity_slider.value()
        return opacity

    def show(self):
        parent_pos = self.parent().rect().bottomRight()
        global_pos = self.parent().mapToGlobal(parent_pos)
        self.move(global_pos)
        super().show()

    @Slot(int)
    def set_axis_tick_font_size(self, size: int) -> None:
        font = QFont()
        font.setPixelSize(size)

        all_axes = self.plot.plotItem.getAxes()
        for axis in all_axes:
            axis.setStyle(tickFont=font)

    @Slot(object)
    def set_time_axis_range(self, raw_range: tuple[QDateTime, QDateTime] = (None, None)) -> None:
        """PyQT Slot to set the plot's X-Axis range. This slot should be
        triggered on QDateTimeEdit value change.

        Parameters
        ----------
        raw_range : tuple[QDateTime, QDateTime], optional
            Takes in a tuple of 2 values, where one is a QDateTime and
            the other is None. The positioning changes either the plot's
            min or max range value. By default (None, None)
        """
        # Disable Autoscroll if enabled
        # self.ui.cursor_scale_btn.click()
        self.disable_autoscroll.emit()

        proc_range = [None, None]
        for ind, val in enumerate(raw_range):
            # Values that are QDateTime are converted to a float timestamp
            if isinstance(val, QDateTime):
                proc_range[ind] = val.toSecsSinceEpoch()
            # Values that are None use the existing range value
            elif not val:
                proc_range[ind] = self.plot.getXAxis().range[ind]
        proc_range.sort()

        logger.debug(f"Setting plot's X-Axis range to {proc_range}")
        self.plot.plotItem.vb.blockSignals(True)
        self.plot.plotItem.setXRange(*proc_range, padding=0)
        self.plot.plotItem.vb.blockSignals(False)

    @Slot(object, object)
    def set_axis_datetimes(self, _: ViewBox = None, time_range: tuple[float, float] = None) -> None:
        """Slot used to update the QDateTimeEdits on the Axis tab. This
        slot is called when the plot's X-Axis range changes values.

        Parameters
        ----------
        _ : ViewBox, optional
            The ViewBox on which the range is changing. This is unused
        time_range : Tuple[float, float], optional
            The new range values for the QDateTimeEdits, by default None
        """
        if not time_range:
            time_range = self.plot.getXAxis().range
        if min(time_range) <= 0:
            return

        time_range = [datetime.fromtimestamp(f) for f in time_range]

        edits = (self.start_datetime, self.end_datetime)
        for ind, qdt in enumerate(edits):
            if qdt.hasFocus():
                continue
            qdt.blockSignals(True)
            qdt.setDateTime(QDateTime(time_range[ind]))
            qdt.blockSignals(False)

    @Slot(int)
    def show_x_grid(self, visible: int):
        """Slot to show or hide the X-Axis gridlines."""
        opacity = self.gridline_opacity
        self.set_plot_gridlines(bool(visible), opacity)

    @Slot(int)
    def show_y_grid(self, visible: int):
        visible = bool(visible)
        self.set_all_y_axis_gridlines.emit(visible)

    @Slot(int)
    def change_gridline_opacity(self, opacity: int):
        """Slot to change the opacity of the gridlines for both X and Y axes."""
        visible = self.x_grid_visible
        self.set_plot_gridlines(visible, opacity)

    def set_plot_gridlines(self, visible: bool, opacity: int):
        """Helper function to set the plot's gridlines visibility and opacity. Updates both X and Y axes."""
        normalized_opacity = opacity / 255
        self.plot.setShowXGrid(visible, normalized_opacity)
        self.grid_alpha_change.emit(opacity)

    @Slot(dict)
    def plot_setup(self, config: dict):
        """Read in the full config dictionary. For each config preset, set the widgets to match the value, which will
        send signals out that will actually cause the plot to change."""
        if "title" in config:
            self.plot_title_line_edit.setText(str(config["title"]))
        if "legend" in config:
            self.legend_checkbox.setChecked(bool(config["legend"]))
        if "mouseMode" in config:
            mouse_mode_index = int(config["mouseMode"] / 3)
            self.mouse_mode_combo.setCurrentIndex(mouse_mode_index)
        if "refreshInterval" in config:
            self.as_interval_spinbox.setValue(int(config["refreshInterval"] / 1000))
        if "crosshair" in config:
            self.crosshair_checkbox.setChecked(bool(config["crosshair"]))
        if "backgroundColor" in config:
            self.background_button.color = QColor(config["backgroundColor"])
        if "xGrid" in config:
            self.x_grid_checkbox.setChecked(bool(config["xGrid"]))
        if "yGrid" in config:
            self.y_grid_checkbox.setChecked(bool(config["yGrid"]))
        if "gridOpacity" in config:
            self.grid_opacity_slider.setValue(int(config["gridOpacity"]))
