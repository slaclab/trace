from widgets import ColorButton
from pyqtgraph import ViewBox
class PlotConfigMixin:
    def plot_config_init(self):
        self.plot = self.ui.archiver_plot
        self.timespan = 60

        self.plot_title_edit = self.ui.plot_title_edit
        self.plot_title_edit.textChanged.connect(lambda text: self.plot.setPlotTitle(text))
        self.grid_opacity = self.ui.opacity_sldr

        self.x_grid_checkbox = self.ui.x_grid_chckbx
        self.x_grid_checkbox.clicked.connect(lambda visible: self.showXGrid(visible, self.grid_opacity.value()/100))

        self.y_grid_checkbox = self.ui.y_grid_chckbx
        self.y_grid_checkbox.clicked.connect(lambda visible: self.showYGrid(visible, self.grid_opacity.value()/100))

        self.grid_opacity = self.ui.opacity_sldr
        self.grid_opacity.valueChanged.connect(lambda opacity:
                                                self.showBothGrids(
                                                    xvisible=self.x_grid_checkbox.isChecked(),
                                                    yvisible=self.y_grid_checkbox.isChecked(),
                                                    opacity=opacity
                                                ))

        self.background_color_button = ColorButton(color="white")
        self.ui.background_color_lyt.insertWidget(1, self.background_color_button)
        self.background_color_button.color_changed.connect(lambda color: self.plot.setBackgroundColor(color))

        self.refresh_rate_spinbox = self.ui.refresh_rate_spnbx
        self.refresh_rate_spinbox.valueChanged.connect(lambda rate: self.autoScroll(enable=True, timespan=self.timespan, refresh_rate=rate))

        self.legend = self.ui.legend_chckbx
        self.legend.clicked.connect(lambda show: self.plot.setShowLegend(show))

        self.crosshair = self.ui.crosshair_chckbx
        self.crosshair.clicked.connect(lambda show: self.plot.enableCrosshair(show, 100, 100))

        self.mouse_mode = self.ui.mouse_mode_cmbbx
        self.mouse_mode.currentIndexChanged.connect(lambda mode: self.changeMouseMode(mode))

    def changeMouseMode(self, mode:int):
        if mode == 1:
            self.plot.plotItem.getViewBox().setMouseMode(ViewBox.PanMode)
        elif mode == 0:
            self.plot.plotItem.getViewBox().setMouseMode(ViewBox.RectMode)

    def autoScroll(self, enable: bool = False, timespan: int = 60, refresh_rate: float = 5):
        waitTime = int(1000/refresh_rate)
        self.plot.setAutoScroll(enable=enable, timespan=timespan, refresh_rate=waitTime)

    def showBothGrids(self, xvisible: bool, yvisible: bool, opacity: int):
        self.showXGrid(xvisible, opacity=opacity/100)
        self.showYGrid(yvisible, opacity=opacity/100)

    def showXGrid(self, visible: bool, opacity: float):
        self.plot.setShowXGrid(visible, opacity)

    def showYGrid(self, visible: bool, opacity: float):
        self.plot.setShowYGrid(visible, opacity)