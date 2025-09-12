from qtpy.QtCore import Qt, Slot, Signal
from qtpy.QtWidgets import QWidget, QCheckBox, QComboBox, QVBoxLayout, QPushButton

from pydm.display import Display
from pydm.widgets import PyDMArchiverTimePlot
from pydm.widgets.baseplot import BasePlotAxisItem

from config import logger
from widgets import SettingsTitle, SettingsRowItem
from widgets.curve_color_palette_modal import CurveColorPaletteModal


class AxisSettingsModal(QWidget):
    sig_curve_palette_changed = Signal(str, bool)
    def __init__(self, parent: QWidget, plot: PyDMArchiverTimePlot, axis: BasePlotAxisItem):
        super().__init__(parent)
        self.setWindowFlag(Qt.Popup)

        self.plot = plot
        self.axis = axis
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        title_label = SettingsTitle(self, "Axis Settings", size=14)
        main_layout.addWidget(title_label)

        orientation_combo = QComboBox(self)
        orientation_combo.addItems(["Left", "Right"])
        orientation_combo.currentTextChanged.connect(self.set_axis_orientation)
        orientation_combo.setCurrentText("Right" if self.axis.orientation == "right" else "Left")
        orientation_row = SettingsRowItem(self, "Orientation", orientation_combo)
        main_layout.addLayout(orientation_row)

        log_checkbox = QCheckBox(self)
        log_checkbox.setChecked(self.axis.log_mode)
        log_checkbox.checkStateChanged.connect(self.set_axis_log_mode)
        log_mode_row = SettingsRowItem(self, "Log Mode", log_checkbox)
        main_layout.addLayout(log_mode_row)

        self.grid_checkbox = QCheckBox(self)
        self.grid_checkbox.setChecked(bool(self.axis.grid))
        self.grid_checkbox.checkStateChanged.connect(self.show_grid)
        y_grid_row = SettingsRowItem(self, "Y Axis Gridline", self.grid_checkbox)
        main_layout.addLayout(y_grid_row)

        self.palette_modal = CurveColorPaletteModal(self)
        self.curve_palette_button = QPushButton("Select")
        self.curve_palette_button.clicked.connect(self.palette_modal.show)
        self.palette_modal.sig_palette_changed.connect(self.sig_curve_palette_changed.emit)
        palette_row = SettingsRowItem(self, "  Curve Palette", self.curve_palette_button)
        main_layout.addLayout(palette_row)

        self.trace_display = self.parent()
        while self.trace_display is not None and not isinstance(self.trace_display, Display):
            self.trace_display = self.trace_display.parent()
        if self.trace_display is not None:
            self.trace_display.gridline_opacity_change.connect(self.change_gridline_opacity)
            self.trace_display.set_all_y_axis_gridlines.connect(self.grid_checkbox.setChecked)

    @property
    def grid_visible(self):
        return self.grid_checkbox.isChecked()

    def show(self):
        parent_pos = self.parent().rect().bottomRight()
        global_pos = self.parent().mapToGlobal(parent_pos)
        self.move(global_pos)
        super().show()

    @Slot(str)
    def set_axis_orientation(self, orientation: str):
        if orientation not in ["Left", "Right"]:
            return
        self.axis.orientation = orientation.lower()
        self.plot.plotItem.rebuildLayout()
        if self.axis.isVisible():
            self.axis.show()

    @Slot(int)
    def set_axis_log_mode(self, checked: int):
        self.axis.log_mode = bool(checked)

    @Slot(int)
    def show_grid(self, visible: int):
        if not visible:
            self.axis.setGrid(False)
        else:
            try:
                opacity = self.trace_display.gridline_opacity
            except AttributeError:
                logger.debug("No trace display found, defaulting to full opacity")
                opacity = 255
            self.axis.setGrid(opacity)

    @Slot(int)
    def change_gridline_opacity(self, opacity: int):
        if not self.grid_visible:
            return
        self.axis.setGrid(opacity)
