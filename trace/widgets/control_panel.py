import re

from qtpy import QtGui, QtCore, QtWidgets
from qtpy.QtCore import Qt, Slot, QTimer

from pydm.widgets.baseplot import BasePlotAxisItem
from pydm.widgets.archiver_time_plot import (
    FormulaCurveItem,
    ArchivePlotCurveItem,
    PyDMArchiverTimePlot,
)

from config import logger
from widgets import (
    ColorButton,
    ToggleSwitch,
    FormulaDialog,
    AxisSettingsModal,
    CurveSettingsModal,
    ArchiveSearchWidget,
)
from services import Theme, IconColors, ThemeManager
from utilities import validate_formula, sanitize_for_validation

PV_KEY_PREFIX = "x"
FORMULA_KEY_PREFIX = "fx"


class ControlPanel(QtWidgets.QWidget):
    """Main control panel widget for managing plot axes and curves.

    This widget provides the primary interface for adding, configuring, and
    managing plot axes and their associated curves. It includes functionality
    for PV search, formula creation, and curve management.
    """

    curve_list_changed = QtCore.Signal()

    def __init__(self, theme_manager: ThemeManager = None):
        """Initialize the control panel.

        Parameters
        ----------
        theme_manager : ThemeManager, optional
            The theme manager for handling UI theming
        """
        super().__init__()
        self.theme_manager = theme_manager
        self.setLayout(QtWidgets.QVBoxLayout())
        # self.setStyleSheet("background-color: white;")

        self._curve_dict = {}
        self.key_gen = self._generate_curve_key()
        next(self.key_gen)  # Prime the generator

        self.curve_palette = "default"
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.on_theme_changed)

        # Create pv plotter layout
        pv_plotter_layout = QtWidgets.QHBoxLayout()
        self.layout().addLayout(pv_plotter_layout)
        self.search_button = QtWidgets.QPushButton()
        self.search_button.setFlat(True)
        self.search_button.clicked.connect(self.search_pv)
        pv_plotter_layout.addWidget(self.search_button)

        self.calc_button = QtWidgets.QPushButton()
        self.calc_button.setFlat(True)
        self.calc_button.clicked.connect(self.show_formula_dialog)
        pv_plotter_layout.addWidget(self.calc_button)

        self.pv_line_edit = QtWidgets.QLineEdit()
        self.pv_line_edit.setPlaceholderText("Enter PV")
        self.pv_line_edit.returnPressed.connect(self.add_curve_from_line_edit)
        pv_plotter_layout.addWidget(self.pv_line_edit)
        pv_plot_button = QtWidgets.QPushButton("Plot")
        pv_plot_button.clicked.connect(self.add_curve_from_line_edit)
        pv_plotter_layout.addWidget(pv_plot_button)

        self.axis_list = QtWidgets.QVBoxLayout()
        frame = QtWidgets.QFrame()
        frame.setLayout(self.axis_list)
        scrollarea = QtWidgets.QScrollArea()
        scrollarea.setWidgetResizable(True)
        scrollarea.setWidget(frame)
        self.layout().addWidget(scrollarea)
        self.axis_list.addStretch()

        new_axis_button = QtWidgets.QPushButton("New Axis")
        new_axis_button.clicked.connect(self.add_empty_axis)
        self.layout().addWidget(new_axis_button)

        self.archive_search = ArchiveSearchWidget()
        self.archive_search.append_PVs_requested.connect(self.add_curves)

        self.formula_dialog = FormulaDialog(self)
        self.formula_dialog.formula_accepted.connect(self.handle_formula_accepted)
        self.curve_list_changed.connect(self.formula_dialog.curve_model.refresh)

        self.update_icons()

    def update_icons(self) -> None:
        """Update all icons based on current theme."""
        if self.theme_manager:
            calc_icon = self.theme_manager.create_icon("fa6s.calculator", IconColors.PRIMARY)
            if calc_icon:
                self.calc_button.setIcon(calc_icon)
            search_icon = self.theme_manager.create_icon("fa6s.magnifying-glass", IconColors.PRIMARY)
            if search_icon:
                self.search_button.setIcon(search_icon)

    def on_theme_changed(self, theme: Theme) -> None:
        """Handle theme changes by updating icons.

        Parameters
        ----------
        theme : Theme
            The new theme, unused
        """
        self.update_icons()

    def minimumSizeHint(self) -> QtCore.QSize:
        """Return the minimum size hint for the control panel."""
        inner_size = self.axis_list.minimumSize()
        buffer = self.pv_line_edit.font().pointSize() * 3
        return QtCore.QSize(inner_size.width() + buffer, inner_size.height())

    def add_curve_from_line_edit(self) -> None:
        """Add a curve from the PV line edit input."""
        pv = self.pv_line_edit.text()
        self.add_curve(pv)
        self.pv_line_edit.clear()

    @property
    def plot(self) -> PyDMArchiverTimePlot:
        """Get the associated plot widget."""
        if not self._plot:
            parent = self.parent()
            while not hasattr(parent, "plot"):
                parent = parent.parent()
            self._plot = parent.plot
        return self._plot

    @plot.setter
    def plot(self, plot: PyDMArchiverTimePlot) -> None:
        """Set the associated plot widget.

        Parameters
        ----------
        plot : PyDMArchiverTimePlot
            The plot widget to associate with this control panel
        """
        self._plot = plot

    def search_pv(self) -> None:
        """Show or activate the PV search widget."""
        if not self.archive_search.isVisible():
            self.archive_search.show()
        else:
            self.archive_search.raise_()
            self.archive_search.activateWindow()

    def show_formula_dialog(self):
        """Show the formula dialog pop-up."""
        if not hasattr(self, "formula_dialog") or not self.formula_dialog.isVisible():
            self.formula_dialog.show()
        else:
            self.formula_dialog.raise_()
            self.formula_dialog.activateWindow()

    @QtCore.Slot(str)
    def handle_formula_accepted(self, formula: str) -> None:
        """Handle the formula accepted from the formula dialog.

        Parameters
        ----------
        formula : str
            The accepted formula string
        """
        self.add_curve(formula)
        self.cleanup_duplicate_curves()

    def cleanup_duplicate_curves(self) -> None:
        """Remove duplicate entries in curve dictionary."""
        seen_curves = {}
        to_remove = []

        for key, curve in self._curve_dict.items():
            curve_id = id(curve)
            if curve_id in seen_curves:
                to_remove.append(key)
            else:
                seen_curves[curve_id] = key

        for key in to_remove:
            del self._curve_dict[key]

        if to_remove:
            self.curve_list_changed.emit()

    @property
    def curve_dict(self) -> dict:
        """Return dictionary of curves with PV keys."""
        return self._curve_dict

    def _generate_curve_key(self):
        """Generate a unique variable name for a curve, either pv or formula.

        Yields
        ------
        key : str
            The next unique key for the curve. Yielded when a curve is sent.
        """
        key = None
        next_pv_num = 1
        next_formula_num = 1
        while True:
            curve = yield key
            if isinstance(curve, ArchivePlotCurveItem):
                key = PV_KEY_PREFIX + str(next_pv_num)
                next_pv_num += 1
            elif isinstance(curve, FormulaCurveItem):
                key = FORMULA_KEY_PREFIX + str(next_formula_num)
                next_formula_num += 1
            else:
                key = None

    def add_curves(self, pvs: list[str]) -> None:
        """Add multiple curves from a list of PV names.

        Parameters
        ----------
        pvs : list[str]
            List of PV names to add as curves
        """
        for pv in pvs:
            self.add_curve(pv)

    def add_empty_axis(self, name: str = "") -> "AxisItem":
        logger.debug("Adding new empty axis to the plot")
        if not name:
            counter = len(self.plot.plotItem.axes) - 2
            while (name := f"Y-Axis {counter}") in self.plot.plotItem.axes:
                counter += 1

        self.plot.addAxis(plot_data_item=None, name=name, orientation="left", label=name)
        new_axis = self.plot._axes[-1]
        new_axis.setLabel(name, color=self.theme_manager.get_icon_color())

        return self.add_axis_item(new_axis)

    def add_axis_item(self, axis: BasePlotAxisItem) -> "AxisItem":
        """Add an existing AxisItem to the plot."""
        self.match_axis_tick_font(axis)
        axis_item = AxisItem(axis, control_panel=self, theme_manager=self.theme_manager)
        axis_item.curves_list_changed.connect(self.curve_list_changed.emit)
        self.axis_list.insertWidget(self.axis_list.count() - 1, axis_item)
        logger.debug(f"Added axis {axis.name} to plot")
        self.updateGeometry()

        return axis_item

    def match_axis_tick_font(self, axis: BasePlotAxisItem) -> None:
        """Matches the axis' tick font to the X-Axis of the plot. Only necessary
        if the user has changed the tick font of the plot's axes.

        Parameters
        ----------
        axis : BasePlotAxisItem
            The axis to match the tick font for."""
        x_axis = self.plot.getAxis("bottom")
        if x_axis is not None:
            axis.setTickFont(x_axis.style["tickFont"])

    def get_axis_item(self, axis_name: str) -> "AxisItem":
        """Get an AxisItem by its name."""
        for index in range(self.axis_list.count()):
            item = self.axis_list.itemAt(index).widget()
            if isinstance(item, AxisItem) and item.name == axis_name:
                return item
        return None

    def get_last_axis_item(self) -> "AxisItem":
        """Get the last AxisItem in the list."""
        if self.axis_list.count() > 1:  # the stretch makes count >= 1
            return self.axis_list.itemAt(self.axis_list.count() - 2).widget()
        else:
            logger.warning("No axes available to return the last AxisItem.")
            return None

    def set_curve_palette(self, palette_name: str, apply: bool = False) -> None:
        """
        Set the default palette for new curves.

        Parameters:
            palette_name (str): name of selected palette
            apply (bool): If true, apply palette to exiting curves
        """
        self.curve_palette = palette_name
        if apply:
            for index, curve in enumerate(self.curve_item_dict.keys()):
                color = ColorButton.index_color(index, palette=self.curve_palette)
                curve.color = color
                self.curve_item_dict[curve]["curveItem"].on_color_changed(color)

    @property
    def curve_item_dict(self):
        """
        Returns dictionary of curves on plot with associated pvname, axisItem, and curveItem
        """
        plot_curves = {}
        for i in range(self.axis_list.count() - 1):  # -1 for stretch
            axis_item = self.axis_list.itemAt(i).widget()
            if hasattr(axis_item, "layout"):
                for j in range(axis_item.layout().count()):
                    widget = axis_item.layout().itemAt(j).widget()
                    if hasattr(widget, "source"):
                        curve = widget.source
                        plot_curves[curve] = {}
                        plot_curves[curve]["name"] = curve.name()
                        plot_curves[curve]["axisItem"] = axis_item
                        plot_curves[curve]["curveItem"] = widget

        return plot_curves

    @QtCore.Slot()
    def add_curve(self, pv: str = None) -> "CurveItem":
        if pv is None and self.sender():
            pv = self.sender().text()

        last_axis = self.get_last_axis_item()
        if not last_axis:
            last_axis = self.add_empty_axis()

        if pv.startswith("f://"):
            return last_axis.add_formula_curve(pv)
        else:
            curve = last_axis.add_curve(pv)
            curve.move_to_axis_from_unit()  # Move to axis based on unit

            return curve

    def clear_all(self) -> None:
        """Clear all axes and curves from the plot and control panel."""
        logger.debug("Clearing all axes and curves from the plot")
        while self.axis_list.count() > 1:  # Keep the stretch at the end
            self.axis_list.itemAt(0).widget().close()
        self.plot.redrawPlot()

    def clear_curves(self) -> None:
        """Clear all curves from the plot and control panel."""
        logger.debug("Clearing all curves from the plot")
        for axis_item in self.axis_list:
            if isinstance(axis_item, AxisItem):
                axis_item.clear_curves()

    def set_axes(self, axes: list[dict] = None) -> None:
        """Given a list of dictionaries containing axis data, clear the
        plot's axes, and set all new axes based on the provided axis data.

        Parameters
        ----------
        axes : List[Dict]
            Axis properties to be set for all new axes on the plot
        """
        self.clear_all()
        for axis in axes:
            self.plot.addAxis(
                plot_data_item=None,
                name=axis["name"],
                orientation=axis.get("orientation", "left"),
                label=axis["name"],
                log_mode=axis.get("logMode", False),
            )
            # Convert axis properties to match BasePlotAxisItem
            new_axis = self.plot._axes[-1]
            new_axis.setLabel(axis["name"], color="black")

            new_axis_item = self.add_axis_item(new_axis)
            if "minRange" in axis:
                new_axis_item.set_min_range(axis["minRange"])
            if "maxRange" in axis:
                new_axis_item.set_max_range(axis["maxRange"])
            if "autoRange" in axis:
                new_axis_item.auto_range_checkbox.setChecked(axis["autoRange"])

    def set_curves(self, curves: list[dict] = None) -> None:
        """Given a list of dictionaries containing curve data, clear the
        plot's curves, and set all new curves based on the provided curve data.

        Parameters
        ----------
        curves : List[Dict]
            Curve properties to be set for all new curves on the plot
        """
        for curve_dict in curves:
            try:
                axis_name = curve_dict.get("yAxisName", "Y-Axis 0")
                axis_item = self.get_axis_item(axis_name)
            except KeyError:
                axis_item = self.get_last_axis_item()

            if axis_item is None:
                axis_item = self.add_empty_axis(axis_name)

            pv_name = curve_dict.get("channel", "")
            del curve_dict["channel"]  # Remove channel key to avoid conflicts with y_channel
            axis_item.add_curve(pv_name, curve_dict)
        self.plot.redrawPlot()
        self.axis_list.itemAt(self.axis_list.count() - 2).widget()

    def move_curve_to_axis(self, curve_item: "CurveItem", target_axis_name: str) -> None:
        """Remove a given CurveItem from its current AxisItem and add it to
        the AxisItem with the given target axis name. If no such AxisItem
        exists, a new one will be created. Intended to be used for Axes
        named after a curve's unit.

        Parameters
        ----------
        curve_item : CurveItem
            CurveItem to be moved to a new axis.
        target_axis_name : str
            Name of the target axis to move the CurveItem to.
        """
        axis_item = self.get_axis_item(target_axis_name)
        if axis_item is None:
            axis_item = self.add_empty_axis(target_axis_name)

        old_axis_item = curve_item.axis_item
        old_axis_item.remove_curve_item(curve_item)
        axis_item.add_curve_item(curve_item)

    def closeEvent(self, a0: QtGui.QCloseEvent):
        for axis_item in range(self.axis_list.count()):
            axis_item.close()
        super().closeEvent(a0)


class AxisItem(QtWidgets.QWidget):
    """Widget for managing a single plot axis and its associated curves.

    This widget provides controls for axis configuration including name, range,
    auto-scaling, and curve management. It supports drag-and-drop for curve
    reordering and moving curves between axes.
    """

    curves_list_changed = QtCore.Signal()

    def __init__(
        self, plot_axis_item: BasePlotAxisItem, control_panel: ControlPanel = None, theme_manager: ThemeManager = None
    ):
        """Initialize the axis item widget.

        Parameters
        ----------
        plot_axis_item : BasePlotAxisItem
            The plot axis item to manage
        control_panel : ControlPanel, optional
            Reference to the parent control panel
        theme_manager : ThemeManager, optional
            The theme manager for UI theming
        """
        super().__init__()
        self.source = plot_axis_item
        self.control_panel_ref = control_panel
        self.theme_manager = theme_manager
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setAcceptDrops(True)

        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.on_theme_changed)

        self.header_layout = QtWidgets.QHBoxLayout()
        self.layout().addLayout(self.header_layout)

        self._expanded = False
        self.expand_button = QtWidgets.QPushButton()
        self.expand_button.setFlat(True)
        self.expand_button.clicked.connect(self.toggle_expand)
        self.header_layout.addWidget(self.expand_button)

        layout = QtWidgets.QVBoxLayout()
        self.header_layout.addLayout(layout)
        self.top_settings_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(self.top_settings_layout)
        self.axis_label = QtWidgets.QLineEdit()
        self.axis_label.setText(self.source.name)
        self.axis_label.editingFinished.connect(self.set_axis_name)
        self.axis_label.returnPressed.connect(self.axis_label.clearFocus)
        self.top_settings_layout.addWidget(self.axis_label)
        self.settings_button = QtWidgets.QPushButton()
        self.settings_button.setFlat(True)
        self.settings_modal = None
        self.settings_button.clicked.connect(self.show_settings_modal)
        self.top_settings_layout.addWidget(self.settings_button)
        self.delete_button = QtWidgets.QPushButton()
        self.delete_button.setFlat(True)
        self.delete_button.clicked.connect(self.close)
        self.top_settings_layout.addWidget(self.delete_button)
        self.bottom_settings_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(self.bottom_settings_layout)
        self.auto_range_checkbox = QtWidgets.QCheckBox("Auto")
        self.auto_range_checkbox.setCheckState(QtCore.Qt.Checked if self.source.auto_range else QtCore.Qt.Unchecked)
        self.auto_range_checkbox.stateChanged.connect(self.set_auto_range)
        self.source.linkedView().sigRangeChangedManually.connect(self.disable_auto_range)
        self.bottom_settings_layout.addWidget(self.auto_range_checkbox)
        self.bottom_settings_layout.addWidget(QtWidgets.QLabel("min, max"))
        self.min_range_line_edit = QtWidgets.QLineEdit()
        self.min_range_line_edit.editingFinished.connect(self.set_min_range)
        self.min_range_line_edit.editingFinished.connect(self.disable_auto_range)
        self.min_range_line_edit.setMinimumWidth(self.min_range_line_edit.font().pointSize() * 8)
        self.bottom_settings_layout.addWidget(self.min_range_line_edit)
        self.bottom_settings_layout.addWidget(QtWidgets.QLabel(","))
        self.max_range_line_edit = QtWidgets.QLineEdit()
        self.max_range_line_edit.editingFinished.connect(self.set_max_range)
        self.max_range_line_edit.editingFinished.connect(self.disable_auto_range)
        self.max_range_line_edit.setMinimumWidth(self.max_range_line_edit.font().pointSize() * 8)
        self.bottom_settings_layout.addWidget(self.max_range_line_edit)
        self.source.sigYRangeChanged.connect(self.handle_range_change)

        self.active_toggle = ToggleSwitch("Active")
        self.active_toggle.setCheckState(QtCore.Qt.Checked if self.source.isVisible() else QtCore.Qt.Unchecked)
        self.active_toggle.stateChanged.connect(self.set_active)
        self.header_layout.addWidget(self.active_toggle)

        self.placeholder = QtWidgets.QWidget(self)
        self.placeholder.hide()
        self.placeholder.setStyleSheet("background-color: lightgrey;")

        self.update_icons()

    def update_icons(self):
        """Update all icons based on current theme"""
        if self.theme_manager:
            if self._expanded:
                expand_icon = self.theme_manager.create_icon("msc.chevron-down", IconColors.PRIMARY)
            else:
                expand_icon = self.theme_manager.create_icon("msc.chevron-right", IconColors.PRIMARY)

            if expand_icon:
                self.expand_button.setIcon(expand_icon)

            settings_icon = self.theme_manager.create_icon("msc.settings-gear", IconColors.PRIMARY)
            if settings_icon:
                self.settings_button.setIcon(settings_icon)

            delete_icon = self.theme_manager.create_icon("msc.trash", IconColors.PRIMARY)
            if delete_icon:
                self.delete_button.setIcon(delete_icon)

    def on_theme_changed(self, theme: Theme):
        """Handle theme changes by updating icons"""
        self.update_icons()

        # Change axis label color to match theme
        label_text = self.source.labelText
        self.source.setLabel(label_text, color=self.theme_manager.get_icon_color())

    @property
    def plot(self):
        return self.parent().parent().parent().parent().plot

    @property
    def name(self) -> str:
        """Get the name of the axis."""
        return self.source.name

    def make_curve_widget(self, plot_curve_item: ArchivePlotCurveItem | FormulaCurveItem) -> "CurveItem":
        """Create a CurveItem widget for the given plot curve item and add
        it to this AxisItem.

        Parameters
        ----------
        plot_curve_item : ArchivePlotCurveItem | FormulaCurveItem
            The plot curve item to create a CurveItem for.

        Returns
        -------
        CurveItem
            The created CurveItem widget.
        """
        curve_item = CurveItem(self, plot_curve_item)
        curve_item.curve_deleted.connect(lambda curve: self.handle_curve_deleted(curve))
        curve_item.active_toggle.setCheckState(self.active_toggle.checkState())

        self.layout().addWidget(curve_item)
        self.curves_list_changed.emit()

        if not self._expanded:
            self.toggle_expand()

        return curve_item

    def add_curve(self, pv: str, channel_args: dict = None) -> "CurveItem":
        """Create a new ArchivePlotCurveItem for the given PV and add it
        to this AxisItem. Also creates a CurveItem widget for it.

        Parameters
        ----------
        pv : str
            The process variable name to create the curve for.
        channel_args : dict, optional
            The arguments to pass to the ArchivePlotCurveItem constructor,
            by default None

        Returns
        -------
        CurveItem
            The created CurveItem widget.
        """
        palette = self.control_panel.curve_palette
        color = ColorButton.index_color(len(self.plot._curves), palette=palette)
        args = {
            "y_channel": pv,
            "name": pv,
            "color": color,
            "useArchiveData": True,
            "yAxisName": self.source.name,
        }
        if channel_args is not None:
            args.update(channel_args)

        plot_curve_item = self.plot.addYChannel(**args)

        return self.make_curve_widget(plot_curve_item)

    def add_formula_curve(self, formula: str) -> "CurveItem":
        """Create a new FormulaCurveItem for the given formula and add it
        to this AxisItem. Also creates a CurveItem widget for it.

        Parameters
        ----------
        formula : str
            The formula to create the curve for. Must start with "f://".

        Returns
        -------
        CurveItem
            The created CurveItem widget.
        """
        var_names = re.findall(r"{(.+?)}", formula)
        var_dict = {}

        for var_name in var_names:
            if var_name not in self.control_panel._curve_dict:
                available_vars = list(self.control_panel._curve_dict.keys())
                raise ValueError(f"{var_name} is an invalid variable name. Available: {available_vars}")
            var_dict[var_name] = self.control_panel._curve_dict[var_name]

        expr_body = formula[4:]
        python_expr, allowed = sanitize_for_validation(expr_body)
        try:
            validate_formula(python_expr, allowed_symbols=allowed)
        except ValueError as e:
            logger.error(f"Invalid formula '{formula}': {e}")
            raise

        color = ColorButton.index_color((len(self.plot._curves)), palette=self.control_panel.curve_palette)
        formula_curve_item = self.plot.addFormulaChannel(
            formula=formula, name=formula, pvs=var_dict, color=color, useArchiveData=True, yAxisName=self.source.name
        )
        formula_curve_item.formula_invalid_signal.connect(self.auto_hide_invalid_formula)

        return self.make_curve_widget(formula_curve_item)

    @Slot()
    @Slot(FormulaCurveItem)
    def auto_hide_invalid_formula(self, formula_curve: FormulaCurveItem = None) -> None:
        """Automatically hide a formula when it becomes invalid"""
        if formula_curve is None:
            formula_curve = self.sender()

        curve_item = self.find_curve_item_for_curve(formula_curve)
        if curve_item and hasattr(curve_item, "active_toggle"):
            curve_item.active_toggle.setChecked(False)
            if hasattr(curve_item, "show_invalid_icon"):
                curve_item.show_invalid_icon(True)

    def toggle_expand(self):
        if self._expanded:
            for index in range(1, self.layout().count()):
                self.layout().itemAt(index).widget().hide()
        else:
            for index in range(1, self.layout().count()):
                self.layout().itemAt(index).widget().show()
        self._expanded = not self._expanded

    @Slot(int)
    @Slot(Qt.CheckState)
    def set_active(self, state: int | Qt.CheckState):
        checked = Qt.CheckState(state) == Qt.Checked
        self.source.setVisible(checked)
        for i in range(1, self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, CurveItem):
                widget.active_toggle.setCheckState(state)

    @Slot(int)
    @Slot(Qt.CheckState)
    def set_auto_range(self, state: int | Qt.CheckState):
        checked = Qt.CheckState(state) == Qt.Checked
        self.source.auto_range = checked

    def disable_auto_range(self):
        self.auto_range_checkbox.setCheckState(QtCore.Qt.Unchecked)

    def handle_range_change(self, _, range):
        self.min_range_line_edit.setText(f"{range[0]:.3g}")
        self.max_range_line_edit.setText(f"{range[1]:.3g}")

    def handle_curve_deleted(self, curve):
        self.curves_list_changed.emit()
        curve_key_to_delete = None

        for key, value in self.control_panel.curve_dict.items():
            if value == curve:
                curve_key_to_delete = key
                break

        if curve_key_to_delete:
            dependent_formulas = []

            for key, other_curve in self.control_panel.curve_dict.items():
                if hasattr(other_curve, "pvs") and curve_key_to_delete in other_curve.pvs:
                    dependent_formulas.append(key)

                    other_curve.setVisible(False)

                    curve_item = self.find_curve_item_for_curve(other_curve)
                    if curve_item and hasattr(curve_item, "active_toggle"):
                        curve_item.active_toggle.setChecked(False)

                    logger.debug(f"Hiding invalid formula: {key} (depends on deleted {curve_key_to_delete})")

                    if hasattr(curve_item, "show_invalid_icon") and curve_item is not None:
                        curve_item.show_invalid_icon(True)

            if dependent_formulas:
                logger.debug(f"Hidden {len(dependent_formulas)} formulas that depended on {curve_key_to_delete}")

            del self.control_panel.curve_dict[curve_key_to_delete]

    def find_curve_item_for_curve(self, target_curve):
        """Find the CurveItem widget that corresponds to a given curve"""
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if hasattr(widget, "source") and widget.source == target_curve:
                return widget

        for i in range(self.control_panel.axis_list.count() - 1):  # -1 for stretch
            axis_item = self.control_panel.axis_list.itemAt(i).widget()
            if hasattr(axis_item, "layout"):
                for j in range(axis_item.layout().count()):
                    widget = axis_item.layout().itemAt(j).widget()
                    if hasattr(widget, "source") and widget.source == target_curve:
                        return widget

        return None

    @QtCore.Slot()
    def set_min_range(self, value: float = None):
        if value is None:
            value = float(self.sender().text())
        else:
            self.min_range_line_edit.setText(f"{value:.3g}")
        logger.debug(f"Setting min range for axis {self.source.name}: {value}")
        self.source.min_range = value

    @QtCore.Slot()
    def set_max_range(self, value: float = None):
        if value is None:
            value = float(self.sender().text())
        else:
            self.max_range_line_edit.setText(f"{value:.3g}")
        logger.debug(f"Setting max range for axis {self.source.name}: {value}")
        self.source.max_range = value

    @QtCore.Slot()
    def set_axis_name(self, name: str = None):
        if name is None and self.sender():
            name = self.sender().text()
        self.source.name = name
        self.source.label_text = name

    @QtCore.Slot()
    def show_settings_modal(self):
        if self.settings_modal is None:
            self.settings_modal = AxisSettingsModal(self.settings_button, self.plot, self.source)
            self.settings_modal.sig_curve_palette_changed.connect(self.set_curve_palette)
        self.settings_modal.show()

    def set_curve_palette(self, palette_name: str, apply: bool = True):
        """Set colors of all curves on this axisItem according to selected palette"""
        if apply:
            for j in range(self.layout().count()):
                widget = self.layout().itemAt(j).widget()
                if hasattr(widget, "source"):
                    curve = widget.source
                    color = ColorButton.index_color(j - 1, palette=palette_name)
                    curve.color = color
                    self.find_curve_item_for_curve(curve).on_color_changed(color)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.possibleActions() & QtCore.Qt.MoveAction:
            event.acceptProposedAction()
            self.placeholder.setMinimumSize(event.source().size())
            self.placeholder.show()
            if not self._expanded:
                self.toggle_expand()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        item = self.childAt(event.position().toPoint())
        if item != self.placeholder:
            index = self.layout().indexOf(item) + 1  # drop below target row
            index = max(1, index)  # don't drop above axis detail row
            self.layout().insertWidget(index, self.placeholder)

    def dragLeaveEvent(self, event: QtGui.QDragLeaveEvent):
        event.accept()
        self.placeholder.hide()

    def dropEvent(self, event: QtGui.QDropEvent):
        event.accept()
        curve_item = event.source()
        self.control_panel.move_curve_to_axis(curve_item, self.source.name)
        self.placeholder.hide()
        if not self._expanded:
            self.toggle_expand()
        self.curves_list_changed.emit()

    def remove_curve_item(self, curve_item: "CurveItem", delete_curve: bool = False) -> None:
        """Removes the given CurveItem from the AxisItem and plot's axis.
        This is required for moving a CurveItem to a new AxisItem. Can
        delete the CurveItem and curve if specified. This will remove it
        from the plot.

        Parameters
        ----------
        curve_item : CurveItem
            The CurveItem to be removed from the axis.
        delete_curve : bool, optional
            If True, the CurveItem will be deleted and the curve removed
            from the plot entirely. If False, it will just be unlinked
            from this axis., by default False.
        """
        curve_item.curve_deleted.disconnect()
        self.layout().removeWidget(curve_item)
        self.plot.plotItem.unlinkDataFromAxis(curve_item.source)

        if delete_curve:
            curve_item.close()
        self.curves_list_changed.emit()

    def add_curve_item(self, curve_item: "CurveItem") -> None:
        """Add an existing CurveItem to this AxisItem.

        Parameters
        ----------
        curve_item : CurveItem
            The CurveItem to be added to this axis.
        """
        # Need to link curve to axis before setting y_axis_name on curve
        self.plot.plotItem.linkDataToAxis(curve_item.source, self.name)
        curve_item.source.y_axis_name = self.name

        curve_item.curve_deleted.connect(lambda curve: self.handle_curve_deleted(curve))
        curve_item.active_toggle.setCheckState(self.active_toggle.checkState())

        if self.layout().indexOf(curve_item) != -1:
            self.layout().removeWidget(curve_item)

        idx = self.layout().indexOf(self.placeholder)
        self.layout().insertWidget(idx, curve_item)

        if not self._expanded:
            self.toggle_expand()
        self.curves_list_changed.emit()

    def clear_curves(self) -> None:
        """Clear all curves from this axis item."""
        for i in range(self.layout().count() - 1, -1, -1):
            item = self.layout().itemAt(i).widget()
            if isinstance(item, CurveItem):
                self.remove_curve_item(item, delete_curve=True)

    def close(self) -> bool:
        # Pop up confirming axis delete
        dialog = QtWidgets.QMessageBox(
            text=str("Are you sure you want to delete the axis?"),
            parent=self,
        )
        dialog.setIcon(QtWidgets.QMessageBox.Information)
        dialog.setWindowTitle("Delete Axis")
        dialog.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        result = dialog.exec_()

        if result == QtWidgets.QMessageBox.Cancel:
            return

        self.clear_curves()
        self.source.sigYRangeChanged.disconnect(self.handle_range_change)
        self.source.linkedView().sigRangeChangedManually.disconnect(self.disable_auto_range)
        index = self.plot._axes.index(self.source)
        self.plot.removeAxisAtIndex(index)
        self.setParent(None)
        self.deleteLater()
        return super().close()

    @property
    def control_panel(self):
        if self.control_panel_ref is None:
            parent = self.parent().parent().parent().parent()
            while parent and not isinstance(parent, ControlPanel):
                parent = parent.parent()
            self.control_panel_ref = parent.control_panel
        return self.control_panel_ref


class DragHandle(QtWidgets.QPushButton):
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        event.ignore()


class CurveItem(QtWidgets.QWidget):
    """Widget for managing a single curve on the plot.

    This widget provides controls for curve configuration including name, color,
    visibility, and connection status. It supports drag-and-drop for moving
    curves between axes and formula editing for formula curves.
    """

    curve_deleted = QtCore.Signal(object)
    unit_changed = QtCore.Signal(str)

    def __init__(self, axis_item: AxisItem, source: ArchivePlotCurveItem | FormulaCurveItem):
        """Initialize the curve item widget.

        Parameters
        ----------
        axis_item : AxisItem
            The parent axis item
        source : ArchivePlotCurveItem or FormulaCurveItem
            The plot curve item to manage
        """
        super().__init__()
        self._axis_item = axis_item
        self.source = source
        self.control_panel = axis_item.control_panel

        self.theme_manager = axis_item.theme_manager
        self.theme_manager.theme_changed.connect(lambda _: self.update_icons())

        self.variable_name = self.control_panel.key_gen.send(self.source)
        self.control_panel.curve_dict[self.variable_name] = self.source

        self.setup_layout()

    def move_to_axis_from_unit(self):
        """Automatically move curve to axis based on unit"""
        if not self.is_formula_curve():
            unit = self.source.units
            if unit:
                self.control_panel.move_curve_to_axis(self, unit)
            else:
                self.source.unitSignal.connect(lambda unit: self.control_panel.move_curve_to_axis(self, unit))

    @property
    def plot(self):
        """Get the PlotWidget that this CurveItem belongs to."""
        return self.control_panel.plot

    @property
    def axis_item(self):
        """Get the AxisItem that this CurveItem belongs to."""
        parent = self.parent()
        while not isinstance(parent, AxisItem):
            parent = parent.parent()
        return parent

    def setup_layout(self):
        """Setup the layout and widgets for the CurveItem."""
        curve_layout = QtWidgets.QHBoxLayout()
        self.setLayout(curve_layout)

        self.handle = DragHandle()
        self.handle.setFlat(True)
        self.handle.setStyleSheet("border: None;")
        self.handle.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))
        curve_layout.addWidget(self.handle)

        self.active_toggle = ToggleSwitch("Active", color=self.source.color_string)
        self.active_toggle.setCheckState(QtCore.Qt.Checked if self.source.isVisible() else QtCore.Qt.Unchecked)
        self.active_toggle.stateChanged.connect(self.set_active)
        curve_layout.addWidget(self.active_toggle)

        second_layout = QtWidgets.QVBoxLayout()
        curve_layout.addLayout(second_layout)

        pv_settings_layout = QtWidgets.QHBoxLayout()
        second_layout.addLayout(pv_settings_layout)

        self.invalid_action = None
        self.variable_name_label = QtWidgets.QLabel()
        self.variable_name_label.setMinimumWidth(40)
        self.variable_name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.variable_name_label.setText(self.variable_name)
        self.variable_name_label.setToolTip("Variable name of the curve")
        pv_settings_layout.addWidget(self.variable_name_label)

        self.label = QtWidgets.QLineEdit()
        self.setup_line_edit()
        pv_settings_layout.addWidget(self.label)

        self.pv_settings_modal = None
        self.pv_settings_button = QtWidgets.QPushButton()
        self.pv_settings_button.setFlat(True)
        self.pv_settings_button.clicked.connect(self.show_settings_modal)
        pv_settings_layout.addWidget(self.pv_settings_button)

        self.live_connection_status = QtWidgets.QLabel()
        self.live_connection_status.setToolTip("Not connected to live data")
        self.source.live_channel_connection.connect(self.update_live_icon)
        pv_settings_layout.addWidget(self.live_connection_status)

        self.archive_connection_status = QtWidgets.QLabel()
        self.archive_connection_status.setToolTip("Not connected to archive data")
        self.source.archive_channel_connection.connect(self.update_archive_icon)
        pv_settings_layout.addWidget(self.archive_connection_status)

        self.delete_button = QtWidgets.QPushButton()
        self.delete_button.setFlat(True)
        self.delete_button.clicked.connect(self.close)
        pv_settings_layout.addWidget(self.delete_button)

        self.update_icons()

    def setup_line_edit(self):
        """Set up the line edit with appropriate behavior for formula vs regular curves"""
        if self.is_formula_curve():
            text = self.source.formula
            placeholder = "Edit formula (f://...)"
            self.label.editingFinished.connect(self.update_formula)
        else:
            text = self.source.name()
            placeholder = "PV Name"
            self.label.editingFinished.connect(self.set_curve_pv)

        self.label.setText(text)
        self.label.setPlaceholderText(placeholder)
        self.label.returnPressed.connect(self.label.clearFocus)

    @Slot()
    def update_icons(self):
        """Update all icons based on current theme"""
        handle_icon = self.theme_manager.create_icon("ph.dots-six-vertical", scale_factor=1.5)
        self.handle.setIcon(handle_icon)

        settings_icon = self.theme_manager.create_icon("msc.settings-gear")
        self.pv_settings_button.setIcon(settings_icon)

        delete_icon = self.theme_manager.create_icon("msc.trash")
        self.delete_button.setIcon(delete_icon)

        icon_disconnected = self.theme_manager.create_icon("msc.debug-disconnect")
        self.live_connection_status.setPixmap(icon_disconnected.pixmap(16, 16))
        self.archive_connection_status.setPixmap(icon_disconnected.pixmap(16, 16))

    def show_invalid_icon(self, show=True):
        """Show or hide the invalid formula icon overlaid on the line edit"""
        if not self.is_formula_curve():
            return

        if show:
            if self.invalid_action is None:
                icon = self.theme_manager.create_icon("fa6s.triangle-exclamation", IconColors.ERROR)
                self.invalid_action = self.label.addAction(icon, QtWidgets.QLineEdit.TrailingPosition)
                self.invalid_action.setToolTip("Formula is invalid")

            self.label.setStyleSheet(
                """
                QLineEdit {
                    border: 2px solid #d32f2f;
                    border-radius: 4px;
                    padding: 4px;
                }
                """
            )
        else:
            if self.invalid_action is not None:
                self.label.removeAction(self.invalid_action)
                self.invalid_action = None

            self.label.setStyleSheet("")

            if self.label.toolTip() == "Formula is invalid":
                self.label.setToolTip("")

    @Slot(int)
    @Slot(Qt.CheckState)
    def set_active(self, state: int | Qt.CheckState):
        checked = Qt.CheckState(state) == Qt.Checked
        self.source.setVisible(checked)

    def update_live_icon(self, connected: bool) -> None:
        self.live_connection_status.setVisible(not connected)

    def update_archive_icon(self, connected: bool) -> None:
        self.archive_connection_status.setVisible(not connected)

    @QtCore.Slot()
    def show_settings_modal(self):
        if self.pv_settings_modal is None:
            self.pv_settings_modal = CurveSettingsModal(self.pv_settings_button, self.plot, self.source)
            self.pv_settings_modal.color_changed.connect(self.on_color_changed)
        self.pv_settings_modal.show()

    @QtCore.Slot(object)
    def on_color_changed(self, color):
        """Handle color change from settings modal"""
        self.update_color_toggle()

    def update_color_toggle(self):
        """Update the color toggle when the curve color changes"""
        if hasattr(self, "active_toggle"):
            curve_color = getattr(self.source, "color_string", None)
            self.active_toggle.setColor(curve_color)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton and self.handle.geometry().contains(event.position().toPoint()):
            self.hide()  # hide actual widget so it doesn't conflict with pixmap on cursor
            drag = QtGui.QDrag(self)
            drag.setMimeData(QtCore.QMimeData())
            drag.setPixmap(self.grab())
            drag.setHotSpot(self.handle.geometry().center())
            drag.exec()
            self.show()  # show curve after drag, even if it ended outside of an axis

    def is_formula_curve(self) -> bool:
        """Check if this is a formula curve.

        Returns
        -------
        bool
            True if this is a formula curve, False otherwise
        """
        return isinstance(self.source, FormulaCurveItem)

    def update_formula(self) -> None:
        """Handle formula updates when user edits the formula text."""
        if hasattr(self, "_updating_formula") and self._updating_formula:
            return

        self.show_invalid_icon(False)

        new_formula = self.label.text().strip()

        if not new_formula.startswith("f://"):
            QtWidgets.QMessageBox.warning(
                self, "Invalid Formula", "Formula must start with 'f://'.\nExample: f://{PV1}+2"
            )
            if hasattr(self.source, "formula"):
                self.label.setText(self.source.formula)
            return

        current_formula = getattr(self.source, "formula", "") if hasattr(self.source, "formula") else ""
        if new_formula == current_formula:
            return

        self._updating_formula = True

        try:
            var_names = re.findall(r"{(.+?)}", new_formula)

            for var_name in var_names:
                if var_name not in self.control_panel._curve_dict:
                    raise ValueError(
                        f"Variable '{var_name}' not found. Available: {list(self.control_panel._curve_dict.keys())}"
                    )

            expr_body = new_formula[4:]
            if var_names:
                python_expr, allowed = sanitize_for_validation(expr_body)
                validate_formula(python_expr, allowed_symbols=allowed)
            else:
                validate_formula(expr_body, allowed_symbols=set())

            def delayed_update():
                try:
                    self._perform_formula_update(new_formula)
                    self.show_invalid_icon(False)
                except ValueError as e:
                    QtWidgets.QMessageBox.critical(None, "Formula Update Failed", f"Failed to update formula: {str(e)}")
                    if hasattr(self.source, "formula"):
                        self.label.setText(self.source.formula)
                    else:
                        self.show_invalid_icon(True)
                finally:
                    if hasattr(self, "_updating_formula"):
                        self._updating_formula = False

            QTimer.singleShot(10, delayed_update)

        except Exception as e:
            self._updating_formula = False
            QtWidgets.QMessageBox.critical(self, "Formula Update Failed", f"Failed to update formula: {str(e)}")
            if hasattr(self.source, "formula"):
                self.label.setText(self.source.formula)
            else:
                self.show_invalid_icon(True)

    def _perform_formula_update(self, new_formula):
        """
        Perform the actual formula update with complete cleanup of the old curve.

        This method is called asynchronously to avoid Qt segmentation faults during
        formula curve replacement. It handles the complete lifecycle of replacing
        an existing formula curve with a new one, including signal disconnection,
        plot removal, dictionary cleanup, and garbage collection.

        Parameters
        ----------
        new_formula : str
            The new formula string starting with 'f://' (e.g., 'f://{x1}+{x2}').
        """

        var_names = re.findall(r"{(.+?)}", new_formula)
        var_dict = {}
        for var_name in var_names:
            if var_name not in self.control_panel._curve_dict:
                raise ValueError(
                    f"Variable '{var_name}' not found. Available: {list(self.control_panel._curve_dict.keys())}"
                )
            var_dict[var_name] = self.control_panel._curve_dict[var_name]

        new_formula_curve = self.plot.addFormulaChannel(
            formula=new_formula,
            name=new_formula,
            pvs=var_dict,
            color=self.source.color,
            useArchiveData=self.source.use_archive_data,
            yAxisName=self.axis_item.source.name,
        )

        if hasattr(self.source, "formula_invalid_signal"):
            self.source.formula_invalid_signal.disconnect()

        self.plot.removeCurve(self.source)
        self.source.deleteLater()
        del self.control_panel._curve_dict[self.variable_name]
        self.plot.set_needs_redraw()

        self.source = new_formula_curve
        self.label.setText(new_formula)

        if not self.variable_name.startswith(FORMULA_KEY_PREFIX):
            self.variable_name = self.control_panel.key_gen.send(new_formula_curve)
        self.control_panel._curve_dict[self.variable_name] = new_formula_curve

        self.axis_item.curves_list_changed.emit()
        self.control_panel.cleanup_duplicate_curves()

    @QtCore.Slot()
    def set_curve_pv(self, pv: str = None):
        if pv is None and self.sender():
            pv = self.sender().text()

        if self.is_formula_curve():
            self.update_formula()
            return

        self.source.address = pv

    def close(self) -> bool:
        curve = self.source
        [ch.disconnect() for ch in curve.channels() if ch]

        try:
            self.plot.removeCurve(curve)
            self.plot.set_needs_redraw()

        except ValueError as e:
            logger.debug(f"Warning: Curve already removed: {e}")
        except Exception as e:
            logger.warning(f"Error removing curve from plot: {e}")

        del self.control_panel._curve_dict[self.variable_name]

        self.curve_deleted.emit(curve)
        self.deleteLater()

        return super().close()
