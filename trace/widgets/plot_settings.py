from datetime import datetime

from pyqtgraph import ViewBox
from qtpy.QtGui import QFont
from qtpy.QtCore import Qt, Slot, Signal, QDateTime
from qtpy.QtWidgets import (
    QSlider,
    QWidget,
    QSpinBox,
    QCheckBox,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QDateTimeEdit,
)

from pydm.widgets import PyDMArchiverTimePlot

from config import logger
from widgets import ColorButton, SettingsTitle, SettingsRowItem


class PlotSettingsModal(QWidget):
    auto_scroll_interval_change = Signal(int)
    grid_alpha_change = Signal(int)

    def __init__(self, parent: QWidget, plot: PyDMArchiverTimePlot):
        super().__init__(parent)
        self.setWindowFlag(Qt.Popup)

        self.plot = plot
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        title_label = SettingsTitle(self, "Plot Settings", size=14)
        main_layout.addWidget(title_label)

        plot_title_line_edit = QLineEdit()
        plot_title_line_edit.setPlaceholderText("Enter Title")
        plot_title_line_edit.textChanged.connect(self.plot.setPlotTitle)
        plot_title_row = SettingsRowItem(self, "Title", plot_title_line_edit)
        main_layout.addLayout(plot_title_row)

        legend_checkbox = QCheckBox(self)
        legend_checkbox.stateChanged.connect(lambda check: self.plot.setShowLegend(bool(check)))
        legend_row = SettingsRowItem(self, "Show Legend", legend_checkbox)
        main_layout.addLayout(legend_row)

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

        appearance_label = SettingsTitle(self, "Appearance")
        main_layout.addWidget(appearance_label)

        background_button = ColorButton(parent=self, color="white")
        background_button.color_changed.connect(self.plot.setBackgroundColor)
        background_row = SettingsRowItem(self, "  Background Color", background_button)
        main_layout.addLayout(background_row)

        x_axis_font_size_spinbox = QSpinBox(self)
        x_axis_font_size_spinbox.setValue(12)
        x_axis_font_size_spinbox.setSuffix(" pt")
        x_axis_font_size_spinbox.valueChanged.connect(self.set_x_axis_font_size)
        x_axis_font_size_row = SettingsRowItem(self, "  X Axis Font Size", x_axis_font_size_spinbox)
        main_layout.addLayout(x_axis_font_size_row)

        self.x_grid_checkbox = QCheckBox(self)
        self.x_grid_checkbox.stateChanged.connect(self.show_x_grid)
        x_grid_row = SettingsRowItem(self, "  X Axis Gridline", self.x_grid_checkbox)
        main_layout.addLayout(x_grid_row)

        self.grid_opacity_slider = QSlider(self)
        self.grid_opacity_slider.setOrientation(Qt.Horizontal)
        self.grid_opacity_slider.setMaximum(255)
        self.grid_opacity_slider.setValue(127)
        self.grid_opacity_slider.setSingleStep(32)
        self.grid_opacity_slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.grid_opacity_slider.valueChanged.connect(self.change_gridline_opacity)
        grid_opacity_row = SettingsRowItem(self, "  Gridline Opacity", self.grid_opacity_slider)
        main_layout.addLayout(grid_opacity_row)

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
    def set_x_axis_font_size(self, size: int) -> None:
        font = QFont()
        font.setPixelSize(size)
        x_axis = self.plot.getAxis("bottom")
        x_axis.setStyle(tickFont=font)

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
    def show_y_grid(self, visible: int):
        self.plot.setShowYGrid(bool(visible), self.gridline_opacity)

    @Slot(int)
    def show_x_grid(self, visible: int):
        opacity = self.gridline_opacity / 255
        self.plot.setShowXGrid(bool(visible), opacity)

    @Slot(int)
    def change_gridline_opacity(self, opacity: int):
        normalized_opacity = opacity / 255
        self.plot.setShowXGrid(self.x_grid_visible, normalized_opacity)
        self.grid_alpha_change.emit(opacity)
