from typing import Dict

from pyqtgraph import ViewBox
from qtpy.QtGui import QFont, QColor
from qtpy.QtCore import Slot

from widgets import ColorButton


class PlotConfigMixin:
    def plot_config_init(self):
        """Load the widgets of the plot config tab programmatically
        All of the other functions in this class are not really going to be called, they are simply the slots
        for each of these widgets to connect to internally.
        """

        self.plot = self.ui.main_plot
        self.ui.plot_title_edit.textChanged.connect(self.plot.setPlotTitle)

        self.ui.x_grid_chckbx.stateChanged.connect(self.show_x_grid)

        self.ui.y_grid_chckbx.stateChanged.connect(self.show_y_grid)

        self.ui.opacity_sldr.valueChanged.connect(self.change_opacity)
        self.ui.xafs_spnbx.setValue(12)
        self.ui.xafs_spnbx.valueChanged.connect(self.set_font_size)
        self.background_color_button = ColorButton(color="white")
        self.ui.background_color_lyt.insertWidget(1, self.background_color_button)
        self.background_color_button.color_changed.connect(self.plot.setBackgroundColor)

        self.ui.refresh_interval_spnbx.setValue(5)
        self.ui.refresh_interval_spnbx.valueChanged.connect(lambda interval: self.autoScroll(enable=True))

        self.ui.legend_chckbx.stateChanged.connect(self.plot.setShowLegend)

        self.ui.crosshair_chckbx.stateChanged.connect(lambda show: self.plot.enableCrosshair(show, 100, 100))

        self.ui.mouse_mode_cmbbx.currentIndexChanged.connect(self.changeMouseMode)

    def plot_setup(self, config: Dict):
        """Read in the full config dictionary, making sure not to fail if a user manually typed
        the import file out. For each config preset, set the widgets to match the value, which will
        send signals out that will actually cause the plot to change"""
        if "title" in config:
            self.ui.plot_title_edit.setText(config["title"])
        if "xGrid" in config:
            self.ui.x_grid_chckbx.setChecked(bool(config["xGrid"]))
        if "yGrid" in config:
            self.ui.y_grid_chckbx.setChecked(bool(config["yGrid"]))
        if "opacity" in config:
            self.ui.opacity_sldr.setValue(config["opacity"])
        if "backgroundColor" in config:
            self.background_color_button.color = QColor(config["backgroundColor"])
        if "legend" in config:
            self.ui.legend_chckbx.setChecked(bool(config["legend"]))
        if "mouseMode" in config:
            self.ui.mouse_mode_cmbbx.setCurrentIndex(int(config["mouseMode"] / 3))
        if "crosshair" in config:
            self.ui.crosshair_chckbx.setChecked(bool(config["crosshair"]))
        if "refreshInterval" in config:
            self.ui.refresh_interval_spnbx.setValue(config["refreshInterval"])

    @Slot(int)
    def set_font_size(self, size: int):
        font = QFont()
        font.setPixelSize(size)
        self.plot.getAxis("bottom").setStyle(tickFont=font)

    @Slot(int)
    def changeMouseMode(self, mode: int):
        """If the user wants to have their mouse in PAN or RECT mode"""
        mouse_mode = ViewBox.RectMode
        if mode == 1:
            mouse_mode = ViewBox.PanMode
        self.plot.plotItem.getViewBox().setMouseMode(mouse_mode)

    @Slot()
    def autoScroll(self, enable: bool = False):
        """Set the autoscroll to the given timespan and selected refresh interval"""
        refresh_interval = int(self.ui.refresh_interval_spnbx.value() * 1000)
        self.plot.setAutoScroll(enable=enable, timespan=self.timespan, refresh_rate=refresh_interval)

    @Slot(int)
    def change_opacity(self, opacity: int):
        """Set opacity of gridLines via slider"""
        x_visible = self.ui.x_grid_chckbx.isChecked()
        y_visible = self.ui.y_grid_chckbx.isChecked()

        opacity /= 100.0
        self.plot.setShowXGrid(x_visible, opacity)
        self.plot.setShowYGrid(y_visible, opacity)

    @Slot(int)
    def show_x_grid(self, visible: bool):
        """Set the x grid visible or not based on user checking the corresponding box"""
        opacity = self.ui.opacity_sldr.value() / 100.0
        self.plot.setShowXGrid(visible, opacity)

    @Slot(int)
    def show_y_grid(self, visible: bool):
        """Set the y grid visible or not based on user checking the corresponding box"""
        opacity = self.ui.opacity_sldr.value() / 100.0
        self.plot.setShowYGrid(visible, opacity)
