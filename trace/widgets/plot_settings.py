from qtpy.QtGui import QFont
from qtpy.QtCore import Qt, Slot, Signal
from qtpy.QtWidgets import (
    QSlider,
    QWidget,
    QSpinBox,
    QCheckBox,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
)

from pydm.widgets import PyDMArchiverTimePlot

from widgets import ColorButton, SettingsTitle, SettingsRowItem


class PlotSettingsModal(QWidget):
    auto_scroll_interval_change = Signal(int)

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
        self.as_interval_spinbox.setSuffix(" s")
        self.as_interval_spinbox.valueChanged.connect(self.auto_scroll_interval_change.emit)
        as_interval_row = SettingsRowItem(self, "Autoscroll Interval", self.as_interval_spinbox)
        main_layout.addLayout(as_interval_row)

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

        self.y_grid_checkbox = QCheckBox(self)
        self.y_grid_checkbox.stateChanged.connect(self.show_y_grid)
        y_grid_row = SettingsRowItem(self, "  Y Axis Gridline", self.y_grid_checkbox)
        main_layout.addLayout(y_grid_row)

        self.x_grid_checkbox = QCheckBox(self)
        self.x_grid_checkbox.stateChanged.connect(self.show_x_grid)
        x_grid_row = SettingsRowItem(self, "  X Axis Gridline", self.x_grid_checkbox)
        main_layout.addLayout(x_grid_row)

        self.grid_opacity_slider = QSlider(self)
        self.grid_opacity_slider.setOrientation(Qt.Horizontal)
        self.grid_opacity_slider.setValue(50)
        self.grid_opacity_slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.grid_opacity_slider.valueChanged.connect(self.change_gridline_opacity)
        grid_opacity_row = SettingsRowItem(self, "  Gridline Opacity", self.grid_opacity_slider)
        main_layout.addLayout(grid_opacity_row)

    @property
    def auto_scroll_interval(self):
        return self.as_interval_spinbox.value()

    @property
    def y_grid_visible(self):
        return self.y_grid_checkbox.isChecked()

    @property
    def x_grid_visible(self):
        return self.x_grid_checkbox.isChecked()

    @property
    def gridline_opacity(self):
        opacity = self.grid_opacity_slider.value()
        opacity /= 100
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

    @Slot(int)
    def show_y_grid(self, visible: int):
        self.plot.setShowYGrid(bool(visible), self.gridline_opacity)

    @Slot(int)
    def show_x_grid(self, visible: int):
        self.plot.setShowXGrid(bool(visible), self.gridline_opacity)

    @Slot(int)
    def change_gridline_opacity(self, opacity: int):
        opacity /= 100
        self.plot.setShowYGrid(self.y_grid_visible, opacity)
        self.plot.setShowXGrid(self.x_grid_visible, opacity)
