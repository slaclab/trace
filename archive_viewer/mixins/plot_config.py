from widgets import ColorButton
from pyqtgraph import ViewBox


class PlotConfigMixin:
    def plot_config_init(self):
        """Load the widgets of the plot config tab programmatically
        All of the other functions in this class are not really going to be called, they are simply the slots
        for each of these widgets to connect to internally.
        """

        self.plot = self.ui.archiver_plot
        self.ui.plot_title_edit.textChanged.connect(self.plot.setPlotTitle)

        self.ui.x_grid_chckbx.clicked.connect(self.show_x_grid)

        self.ui.y_grid_chckbx.clicked.connect(self.show_y_grid)

        self.ui.opacity_sldr.valueChanged.connect(self.change_opacity)

        background_color_button = ColorButton(color="white")
        self.ui.background_color_lyt.insertWidget(1, background_color_button)
        background_color_button.color_changed.connect(self.plot.setBackgroundColor)

        self.ui.refresh_interval_spnbx.setValue(5)
        self.ui.refresh_interval_spnbx.valueChanged.connect(lambda interval: self.autoScroll(enable=True))

        self.ui.legend_chckbx.clicked.connect(self.plot.setShowLegend)

        self.ui.crosshair_chckbx.clicked.connect(lambda show: self.plot.enableCrosshair(show, 100, 100))

        self.ui.mouse_mode_cmbbx.currentIndexChanged.connect(self.changeMouseMode)

    def changeMouseMode(self, mode:int):
        """If the user wants to have their mouse in PAN or RECT mode"""
        mouse_mode = ViewBox.RectMode
        if mode == 1:
            mouse_mode = ViewBox.PanMode
        self.plot.plotItem.getViewBox().setMouseMode(mouse_mode)

    def autoScroll(self, enable: bool = False):
        """Set the autoscroll to the given timespan and selected refresh interval"""
        refresh_interval = int(self.ui.refresh_interval_spnbx.value() * 1000)
        self.plot.setAutoScroll(enable=enable, timespan=self.timespan, refresh_rate=refresh_interval)

    def change_opacity(self, opacity: int):
        """Set opacity of gridLines via slider"""
        x_visible = self.ui.x_grid_chckbx.isChecked()
        y_visible = self.ui.y_grid_chckbx.isChecked()

        opacity /= 100.0
        self.plot.setShowXGrid(x_visible, opacity)
        self.plot.setShowYGrid(y_visible, opacity)

    def show_x_grid(self, visible: bool):
        """Set the x grid visible or not based on user checking the corresponding box"""
        opacity = self.ui.opacity_sldr.value() / 100.0
        self.plot.setShowXGrid(visible, opacity)

    def show_y_grid(self, visible: bool):
        """Set the y grid visible or not based on user checking the corresponding box"""
        opacity = self.ui.opacity_sldr.value() / 100.0
        self.plot.setShowYGrid(visible, opacity)
