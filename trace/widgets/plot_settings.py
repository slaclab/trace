from qtpy.QtGui import QFont
from qtpy.QtCore import Qt, Slot, Signal
from qtpy.QtWidgets import (
    QLabel,
    QSlider,
    QWidget,
    QSpinBox,
    QCheckBox,
    QLineEdit,
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from pydm.widgets import PyDMArchiverTimePlot

from widgets import ColorButton


class PlotSettingsModal(QWidget):
    auto_scroll_interval_change = Signal(int)

    def __init__(self, parent: QWidget, plot: PyDMArchiverTimePlot):
        super().__init__(parent)
        self.setWindowFlag(Qt.Popup)

        self.plot = plot
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        bold_font = QFont()
        bold_font.setBold(True)
        bold_font.setPixelSize(14)
        title_label = QLabel("Plot Settings", self)
        title_label.setFont(bold_font)
        main_layout.addWidget(title_label)

        plot_title_layout = QHBoxLayout()
        plot_title_label = QLabel("Title", self)
        plot_title_layout.addWidget(plot_title_label)
        plot_title_spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        plot_title_layout.addSpacerItem(plot_title_spacer)
        plot_title_line_edit = QLineEdit()
        plot_title_line_edit.setPlaceholderText("Enter Title")
        plot_title_line_edit.textChanged.connect(self.plot.setPlotTitle)
        plot_title_layout.addWidget(plot_title_line_edit)
        main_layout.addLayout(plot_title_layout)

        legend_layout = QHBoxLayout()
        legend_label = QLabel("Legend", self)
        legend_layout.addWidget(legend_label)
        legend_spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        legend_layout.addSpacerItem(legend_spacer)
        legend_checkbox = QCheckBox(self)
        legend_checkbox.stateChanged.connect(lambda check: self.plot.setShowLegend(bool(check)))
        legend_layout.addWidget(legend_checkbox)
        main_layout.addLayout(legend_layout)

        as_interval_layout = QHBoxLayout()
        as_interval_label = QLabel("Autoscroll Interval", self)
        as_interval_layout.addWidget(as_interval_label)
        as_interval_spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        as_interval_layout.addSpacerItem(as_interval_spacer)
        self.as_interval_spinbox = QSpinBox(self)
        self.as_interval_spinbox.setValue(5)
        self.as_interval_spinbox.setSuffix(" s")
        self.as_interval_spinbox.valueChanged.connect(self.auto_scroll_interval_change.emit)
        as_interval_layout.addWidget(self.as_interval_spinbox)
        main_layout.addLayout(as_interval_layout)

        bold_font = QFont()
        bold_font.setBold(True)
        appearance_label = QLabel("Appearance", self)
        appearance_label.setFont(bold_font)
        main_layout.addWidget(appearance_label)

        background_layout = QHBoxLayout()
        background_label = QLabel("  Background Color", self)
        background_layout.addWidget(background_label)
        as_interval_spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        background_layout.addSpacerItem(as_interval_spacer)
        background_button = ColorButton(parent=self, color="white")
        background_button.color_changed.connect(self.plot.setBackgroundColor)
        background_layout.addWidget(background_button)
        main_layout.addLayout(background_layout)

        x_axis_font_size_layout = QHBoxLayout()
        x_axis_font_size_label = QLabel("  X Axis Font Size", self)
        x_axis_font_size_layout.addWidget(x_axis_font_size_label)
        x_axis_font_size_spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        x_axis_font_size_layout.addSpacerItem(x_axis_font_size_spacer)
        x_axis_font_size_spinbox = QSpinBox(self)
        x_axis_font_size_spinbox.setValue(12)
        x_axis_font_size_spinbox.setSuffix(" pt")
        x_axis_font_size_spinbox.valueChanged.connect(self.set_x_axis_font_size)
        x_axis_font_size_layout.addWidget(x_axis_font_size_spinbox)
        main_layout.addLayout(x_axis_font_size_layout)

        y_grid_layout = QHBoxLayout()
        y_grid_label = QLabel("  Y Axis Gridline", self)
        y_grid_layout.addWidget(y_grid_label)
        y_grid_spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        y_grid_layout.addSpacerItem(y_grid_spacer)
        self.y_grid_checkbox = QCheckBox(self)
        self.y_grid_checkbox.stateChanged.connect(self.show_y_grid)
        y_grid_layout.addWidget(self.y_grid_checkbox)
        main_layout.addLayout(y_grid_layout)

        x_grid_layout = QHBoxLayout()
        x_grid_label = QLabel("  X Axis Gridline", self)
        x_grid_layout.addWidget(x_grid_label)
        x_grid_spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        x_grid_layout.addSpacerItem(x_grid_spacer)
        self.x_grid_checkbox = QCheckBox(self)
        self.x_grid_checkbox.stateChanged.connect(self.show_x_grid)
        x_grid_layout.addWidget(self.x_grid_checkbox)
        main_layout.addLayout(x_grid_layout)

        grid_opacity_layout = QHBoxLayout()
        grid_opacity_label = QLabel("  Gridline Opacity", self)
        grid_opacity_layout.addWidget(grid_opacity_label)
        grid_opacity_spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        grid_opacity_layout.addSpacerItem(grid_opacity_spacer)
        self.grid_opacity_slider = QSlider(self)
        self.grid_opacity_slider.setOrientation(Qt.Horizontal)
        self.grid_opacity_slider.setValue(50)
        self.grid_opacity_slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.grid_opacity_slider.valueChanged.connect(self.change_gridline_opacity)
        grid_opacity_layout.addWidget(self.grid_opacity_slider)
        main_layout.addLayout(grid_opacity_layout)

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
