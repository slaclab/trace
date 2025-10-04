from qtpy.QtCore import Qt, Slot, Signal
from qtpy.QtWidgets import QWidget, QCheckBox, QComboBox, QPushButton, QVBoxLayout

from pydm.display import Display
from pydm.widgets import PyDMArchiverTimePlot
from pydm.widgets.baseplot import BasePlotAxisItem

from config import logger
from widgets import SettingsTitle, SettingsRowItem, CurveColorPaletteModal


class AxisSettingsModal(QWidget):
    """Modal widget for configuring individual axis settings including orientation,
    log mode, and gridline visibility.

    This widget provides an interface for customizing the appearance and behavior
    of a single axis on the plot.
    """

    sig_curve_palette_changed = Signal(str, bool)

    def __init__(self, parent: QWidget, plot: PyDMArchiverTimePlot, axis: BasePlotAxisItem):
        """Initialize the axis settings modal.

        Parameters
        ----------
        parent : QWidget
            The parent widget
        plot : PyDMArchiverTimePlot
            The plot widget containing the axis
        axis : BasePlotAxisItem
            The axis to configure
        """
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
        log_checkbox.stateChanged.connect(self.set_axis_log_mode)
        log_mode_row = SettingsRowItem(self, "Log Mode", log_checkbox)
        main_layout.addLayout(log_mode_row)

        self.grid_checkbox = QCheckBox(self)
        self.grid_checkbox.setChecked(bool(self.axis.grid))
        self.grid_checkbox.stateChanged.connect(self.show_grid)
        y_grid_row = SettingsRowItem(self, "Y Axis Gridline", self.grid_checkbox)
        main_layout.addLayout(y_grid_row)

        self.palette_modal = CurveColorPaletteModal(self)
        self.curve_palette_button = QPushButton("Select")
        self.curve_palette_button.clicked.connect(self.palette_modal.show)
        self.palette_modal.sig_palette_changed.connect(self.sig_curve_palette_changed.emit)
        palette_row = SettingsRowItem(self, "Curve Palette", self.curve_palette_button)
        main_layout.addLayout(palette_row)

        self.trace_display = self.parent()
        while self.trace_display is not None and not isinstance(self.trace_display, Display):
            self.trace_display = self.trace_display.parent()
        if self.trace_display is not None:
            self.trace_display.gridline_opacity_change.connect(self.change_gridline_opacity)
            self.trace_display.set_all_y_axis_gridlines.connect(self.grid_checkbox.setChecked)

    @property
    def grid_visible(self) -> bool:
        """Check if gridlines are visible for this axis."""
        return self.grid_checkbox.isChecked()

    def show(self) -> None:
        """Show the modal positioned relative to its parent widget."""
        parent_pos = self.parent().rect().bottomRight()
        global_pos = self.parent().mapToGlobal(parent_pos)
        self.move(global_pos)
        super().show()

    @Slot(str)
    def set_axis_orientation(self, orientation: str) -> None:
        """Set the axis orientation (Left or Right).

        Parameters
        ----------
        orientation : str
            The orientation string ("Left" or "Right")
        """
        if orientation not in ["Left", "Right"]:
            return
        self.axis.orientation = orientation.lower()
        self.plot.plotItem.rebuildLayout()
        if self.axis.isVisible():
            self.axis.show()

    @Slot(int)
    @Slot(Qt.CheckState)
    def set_axis_log_mode(self, state: int | Qt.CheckState) -> None:
        """Enable or disable logarithmic scale for the axis.

        Parameters
        ----------
        state : int or Qt.CheckState
            The checkbox state
        """
        checked = Qt.CheckState(state) == Qt.Checked
        self.axis.log_mode = checked

    @Slot(int)
    @Slot(Qt.CheckState)
    def show_grid(self, state: int | Qt.CheckState) -> None:
        """Show or hide gridlines for the axis.

        Parameters
        ----------
        state : int or Qt.CheckState
            The checkbox state
        """
        checked = Qt.CheckState(state) == Qt.Checked
        if not checked:
            self.axis.setGrid(False)
        else:
            try:
                opacity = self.trace_display.gridline_opacity
            except AttributeError:
                logger.debug("No trace display found, defaulting to full opacity")
                opacity = 255
            self.axis.setGrid(opacity)

    @Slot(int)
    def change_gridline_opacity(self, opacity: int) -> None:
        """Change the opacity of gridlines for this axis.

        Parameters
        ----------
        opacity : int
            The opacity value (0-255)
        """
        if not self.grid_visible:
            return
        self.axis.setGrid(opacity)
