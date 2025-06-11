import re
import qtawesome as qta
from toggle import ToggleSwitch
from qtpy.QtCore import QTimer
from qtpy import QtGui, QtCore, QtWidgets
from pydm.widgets.archiver_time_plot import FormulaCurveItem, ArchivePlotCurveItem

from config import logger
from widgets import AxisSettingsModal, CurveSettingsModal
from widgets.table_widgets import ColorButton
from widgets.archive_search import ArchiveSearchWidget
from widgets.formula_dialog import FormulaDialog

from toggle import ToggleSwitch


class ControlPanel(QtWidgets.QWidget):
    curve_list_changed = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setStyleSheet("background-color: white;")

        self._curve_dict = {}
        self._next_var_number = 1

        pv_plotter_layout = QtWidgets.QHBoxLayout()
        self.layout().addLayout(pv_plotter_layout)
        self.search_button = QtWidgets.QPushButton()
        self.search_button.setIcon(qta.icon("fa5s.search"))
        self.search_button.setFlat(True)
        self.search_button.clicked.connect(self.search_pv)
        pv_plotter_layout.addWidget(self.search_button)

        self.calc_button = QtWidgets.QPushButton()
        self.calc_button.setIcon(qta.icon("fa6s.calculator"))
        self.calc_button.setFlat(True)
        self.calc_button.clicked.connect(self.add_formula)
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
        new_axis_button.clicked.connect(self.add_axis)
        self.layout().addWidget(new_axis_button)

        self.formula_dialog = FormulaDialog(self)
        self.formula_dialog.formula_accepted.connect(self.handle_formula_accepted)
        self.curve_list_changed.connect(self.formula_dialog.curve_model.refresh)

    def minimumSizeHint(self):
        inner_size = self.axis_list.minimumSize()
        buffer = self.pv_line_edit.font().pointSize() * 3
        return QtCore.QSize(inner_size.width() + buffer, inner_size.height())

    def add_curve_from_line_edit(self):
        pv = self.pv_line_edit.text()
        self.add_curve(pv)
        self.pv_line_edit.clear()

    @property
    def plot(self):
        if not self._plot:
            parent = self.parent()
            while not hasattr(parent, "plot"):
                parent = parent.parent()
            self._plot = parent.plot
        return self._plot

    @plot.setter
    def plot(self, plot):
        self._plot = plot

    def search_pv(self):
        if not hasattr(self, "archive_search") or not self.archive_search.isVisible():
            self.archive_search = ArchiveSearchWidget()
            self.archive_search.insert_button.clicked.connect(
                lambda: self.add_curves(self.archive_search.selectedPVs())
            )
            self.archive_search.show()
        else:
            self.archive_search.raise_()
            self.archive_search.activateWindow()

    def add_formula(self):
        if not hasattr(self, "formula_dialog") or not self.formula_dialog.isVisible():
            self.formula_dialog.show()
        else:
            self.formula_dialog.raise_()
            self.formula_dialog.activateWindow()

    @QtCore.Slot(str)
    def handle_formula_accepted(self, formula: str) -> None:
        """Handle the formula accepted from the formula dialog."""
        self.add_curve(formula)

    def add_curves(self, pvs: list[str]) -> None:
        for pv in pvs:
            self.add_curve(pv)

    def add_axis(self, name: str = ""):
        logger.debug("Adding new empty axis to the plot")
        if not name:
            counter = len(self.plot.plotItem.axes) - 2
            while (name := f"Y-Axis {counter}") in self.plot.plotItem.axes:
                counter += 1

        self.plot.addAxis(plot_data_item=None, name=name, orientation="left", label=name)
        new_axis = self.plot._axes[-1]
        new_axis.setLabel(name, color="black")

        axis_item = AxisItem(new_axis, control_panel=self)
        axis_item.curves_list_changed.connect(self.curve_list_changed.emit)
        self.axis_list.insertWidget(self.axis_list.count() - 1, axis_item)

        logger.debug(f"Added axis {new_axis.name} to plot")
        self.updateGeometry()

    @property
    def curve_dict(self):
        """Return dictionary of curves with PV keys"""
        return self._curve_dict

    def _generate_pv_key(self):
        """Generate a unique PV key (PV1, PV2, etc.)"""
        key = f"PV{self._next_var_number}"
        self._next_var_number += 1
        return key

    @QtCore.Slot()
    def add_curve(self, pv: str = None):
        if pv is None and self.sender():
            pv = self.sender().text()

        plot = self.plot
        
        # Determine which axis to use and handle different curve types
        if pv.startswith("f://"):
            # Formula curves - handle specially
            axis_name = "Formula"
            axis = self._find_or_create_axis(axis_name)
            axis.add_formula_curve(pv)
            
            # Get the curve that was just added
            new_curve = plot._curves[-1]
            key = self._generate_pv_key()
            self._curve_dict[key] = new_curve
        else:
            # Regular PV curves
            index = len(plot._curves)
            color = ColorButton.index_color(index)
            
            # Add the curve to the plot
            plot.addYChannel(
                y_channel=pv,
                name=pv,
                color=color,
                useArchiveData=True,
                yAxisName="",
            )
            
            plot_curve_item = plot._curves[-1]
            curve_item = CurveItem(plot_curve_item)
            
            # Determine axis based on units
            if hasattr(curve_item.source, 'units') and curve_item.source.units:
                axis_name = curve_item.source.units
                axis = self._find_or_create_axis(axis_name)
            else:
                # No units - use default axis
                if self.axis_list.count() == 1:  # Only the stretch item exists
                    axis_name = "Y-Axis 0"
                    axis = self._find_or_create_axis(axis_name)
                else:
                    # Use the last created axis
                    axis = self.axis_list.itemAt(self.axis_list.count() - 2).widget()
            
            # Attach regular curve to the axis
            axis.attach_curve(curve_item)

            # Add curve to the curve dictionary for formula references
            new_curve = plot._curves[-1]
            key = self._generate_pv_key()
            self._curve_dict[key] = new_curve

    def _find_or_create_axis(self, axis_name):
        """Find existing axis by name or create new one"""
        # Look for existing axis
        for i in range(self.axis_list.count() - 1):
            cur = self.axis_list.itemAt(i).widget()
            if cur.source.name == axis_name:
                return cur
        
        # Create new axis if not found
        self.add_axis(axis_name)
        return self.axis_list.itemAt(self.axis_list.count() - 2).widget()


    def closeEvent(self, a0: QtGui.QCloseEvent):
        for axis_item in range(self.axis_list.count()):
            axis_item.close()
        super().closeEvent(a0)

    def recursionCheck(self, target: str, rowHeaders: dict) -> bool:
        """Internal method that uses DFS to confirm there are not cyclical formula dependencies

        We are handling base case in the loop
        We are running this every single time formulaToPVDict is called,
        so our target is the only fail check

        Parameters
        --------------
        target: str
            The row header that initially called this check. If we find it, there is a cyclical dependency

        rowHeaders: dict()
            This contains rowHeader -> BasePlotCurveItem so we can find all of our dependencies
                From this we know which Formula we then have to traverse to confirm we are good
        """

        for rowHeader, curve in rowHeaders.items():
            if rowHeader == target:
                # We hit a dependency that is our target, fail
                return False
            if isinstance(curve, FormulaCurveItem):
                # If this dependency is a Formula, check its children
                if not self.recursionCheck(target, curve.pvs):
                    # One of the descendants is target, propagate upward
                    return False
        # If we are here, then none of the children failed
        return True

    def formulaToPVDict(self, rowName: str, formula: str) -> dict:
        """Take in a formula and return a dictionary with keys of row headers and values of the BasePlotCurveItems"""
        pvs = re.findall("{(.+?)}", formula)
        pvdict = dict()
        for pv in pvs:
            # Check if all of the requested rows actually exist
            if pv not in self._row_names:
                raise ValueError(f"{pv} is an invalid variable name")
            elif pv == rowName:
                raise ValueError(f"{pv} is recursive")

            # If the PV is good, add it to the dictionary of used PVs
            rindex = self._row_names.index(pv)
            pvdict[pv] = self._plot._curves[rindex]

        if not self.recursionCheck(rowName, pvdict):
            raise ValueError("There was a recursive dependency somewhere")
        if not pvdict:
            try:
                eval(formula[4:])
            except SyntaxError:
                raise SyntaxError("Invalid Input")
        return pvdict


class AxisItem(QtWidgets.QWidget):
    curves_list_changed = QtCore.Signal()

    def __init__(self, plot_axis_item, control_panel=None):
        super().__init__()
        self.source = plot_axis_item
        self.control_panel_ref = control_panel
        self.setLayout(QtWidgets.QVBoxLayout())
        self.setAcceptDrops(True)

        self.header_layout = QtWidgets.QHBoxLayout()
        self.layout().addLayout(self.header_layout)

        self._expanded = False
        self.expand_button = QtWidgets.QPushButton()
        self.expand_button.setIcon(qta.icon("msc.chevron-right"))
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
        self.settings_button.setIcon(qta.icon("msc.settings-gear"))
        self.settings_button.setFlat(True)
        self.settings_modal = None
        self.settings_button.clicked.connect(self.show_settings_modal)
        self.top_settings_layout.addWidget(self.settings_button)
        self.delete_button = QtWidgets.QPushButton()
        self.delete_button.setIcon(qta.icon("msc.trash"))
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

    @property
    def plot(self):
        return self.parent().parent().parent().parent().plot

    def attach_curve(self, curve_item):
        try:
            curve_item.curve_deleted.disconnect()
        except TypeError:
            pass
        #curve_item.curve_deleted.connect(self.curves_list_changed.emit)
        curve_item.active_toggle.setCheckState(self.active_toggle.checkState())
        self.plot.plotItem.unlinkDataFromAxis(curve_item.source)
        self.plot.plotItem.linkDataToAxis(curve_item.source, self.source.name)
        curve_item.source.y_axis_name = self.source.name
        curve_item.curve_deleted.connect(lambda curve: self.handle_curve_deleted(curve))
        self.layout().addWidget(curve_item)
        self.curves_list_changed.emit()
        if not self._expanded:
            self.toggle_expand()


    def add_formula_curve(self, formula):
        # Find ControlPanel by traversing up the widget hierarchy
        control_panel = self.parent()
        while control_panel and not hasattr(control_panel, '_curve_dict'):
            control_panel = control_panel.parent()
        
        if not control_panel:
            raise RuntimeError("Could not find ControlPanel")
        
        plot = control_panel.plot
        print(f"Available curves: {list(control_panel._curve_dict.keys())}")
        print(f"Formula: {formula}")

        var_names = re.findall(r"{(.+?)}", formula)
        var_dict = {}

        # Handle formulas with variables
        for var_name in var_names:
            if var_name not in control_panel._curve_dict:
                raise ValueError(f"{var_name} is an invalid variable name")
            var_dict[var_name] = control_panel._curve_dict[var_name]

        # For constant formulas (no variables), validate the expression
        if not var_dict:
            expression = formula[4:]  # Remove "f://" prefix
            try:
                eval(expression)
            except Exception as e:
                raise ValueError(f"Invalid mathematical expression: {expression}. Error: {str(e)}")

        formula_curve_item = None
        
        try:
            # Use plot's addFormulaChannel method
            if hasattr(plot, 'addFormulaChannel'):
                print("Trying plot.addFormulaChannel...")
                index = len(plot._curves)
                color = ColorButton.index_color(index)
                
                formula_curve_item = plot.addFormulaChannel(
                    formula=formula,
                    name=formula,
                    pvs=var_dict,
                    color=color,
                    useArchiveData=True,
                    yAxisName=self.source.name
                )
                print(f"addFormulaChannel successful: {type(formula_curve_item)}")
                
                # Try to force the formula curve to update/redraw
                try:
                    if hasattr(formula_curve_item, 'redrawCurve'):
                        formula_curve_item.redrawCurve()
                        print("Called redrawCurve()")
                    
                    if hasattr(formula_curve_item, 'update'):
                        formula_curve_item.update()
                        print("Called update()")
                    
                    # Force the plot to update
                    plot.plotItem.update()
                    plot.update()
                    print("Called plot updates")
                    
                    # Check if the curve has data - be more careful with array comparisons
                    try:
                        if hasattr(formula_curve_item, 'data_buffer'):
                            buffer = formula_curve_item.data_buffer
                            if buffer is not None:
                                print(f"Formula curve data buffer size: {len(buffer)}")
                            else:
                                print("Formula curve data buffer is None")
                        
                        if hasattr(formula_curve_item, 'xData') and hasattr(formula_curve_item, 'yData'):
                            x_data = formula_curve_item.xData
                            y_data = formula_curve_item.yData
                            x_len = len(x_data) if x_data is not None else 0
                            y_len = len(y_data) if y_data is not None else 0
                            print(f"Formula curve data points: x={x_len}, y={y_len}")
                            
                            # Show some sample data if available
                            if x_len > 0 and y_len > 0:
                                print(f"Sample data - x: {x_data[:min(3, x_len)]}, y: {y_data[:min(3, y_len)]}")
                    
                    except Exception as data_error:
                        print(f"Error checking curve data: {data_error}")
                    
                except Exception as update_error:
                    print(f"Error during curve update: {update_error}")
                
        except Exception as e1:
            print(f"addFormulaChannel failed: {e1}")
            raise

        if not formula_curve_item:
            raise RuntimeError("Failed to create formula curve")
        
        # Create the CurveItem widget for the control panel
        curve_item = CurveItem(formula_curve_item)
        curve_item.curve_deleted.connect(self.curves_list_changed.emit)
        curve_item.active_toggle.setCheckState(self.active_toggle.checkState())
        
        # Add the curve item widget to this axis
        self.layout().addWidget(curve_item)
        
        # Emit signal that curves have changed
        self.curves_list_changed.emit()
        
        # Expand the axis if it's not already expanded
        if not self._expanded:
            self.toggle_expand()
        
        print(f"Formula curve added to control panel. Total curves: {len(plot._curves)}")
        
        # Final attempt to make sure everything is visible
        try:
            plot.plotItem.getViewBox().autoRange()
            print("Called autoRange()")
        except Exception as range_error:
            print(f"Error in autoRange: {range_error}")
        
        # Try to trigger a plot refresh after a short delay
        try:
            from PyQt5.QtCore import QTimer
            def delayed_refresh():
                try:
                    if hasattr(formula_curve_item, 'redrawCurve'):
                        formula_curve_item.redrawCurve()
                    plot.plotItem.update()
                    plot.update()
                    print("Delayed refresh completed")
                except Exception as e:
                    print(f"Delayed refresh failed: {e}")
            
            QTimer.singleShot(100, delayed_refresh)  # Refresh after 100ms
            print("Scheduled delayed refresh")
        except Exception as timer_error:
            print(f"Could not schedule delayed refresh: {timer_error}")

    def attach_curve(self, curve_item):
        try:
            curve_item.curve_deleted.disconnect()
        except TypeError:
            pass
        curve_item.curve_deleted.connect(self.curves_list_changed.emit)
        curve_item.active_toggle.setCheckState(self.active_toggle.checkState())
        self.plot.plotItem.unlinkDataFromAxis(curve_item.source)
        self.plot.plotItem.linkDataToAxis(curve_item.source, self.source.name)
        curve_item.source.y_axis_name = self.source.name

        self.layout().addWidget(curve_item)
        self.curves_list_changed.emit()
        if not self._expanded:
            self.toggle_expand()

    def toggle_expand(self):
        if self._expanded:
            for index in range(1, self.layout().count()):
                self.layout().itemAt(index).widget().hide()
            self.expand_button.setIcon(qta.icon("msc.chevron-right"))
        else:
            for index in range(1, self.layout().count()):
                self.layout().itemAt(index).widget().show()
            self.expand_button.setIcon(qta.icon("msc.chevron-down"))
        self._expanded = not self._expanded

    def set_active(self, state: QtCore.Qt.CheckState):
        if state == QtCore.Qt.Unchecked:
            self.source.hide()
        else:
            self.source.show()
        for i in range(1, self.layout().count()):
            self.layout().itemAt(i).widget().active_toggle.setCheckState(state)

    def set_auto_range(self, state: QtCore.Qt.CheckState):
        self.source.auto_range = state == QtCore.Qt.Checked

    def disable_auto_range(self):
        self.auto_range_checkbox.setCheckState(QtCore.Qt.Unchecked)

    def handle_range_change(self, _, range):
        self.min_range_line_edit.setText(f"{range[0]:.3g}")
        self.max_range_line_edit.setText(f"{range[1]:.3g}")

    def handle_curve_deleted(self, curve):
        self.curves_list_changed.emit()

        control_panel = self.parent().parent().parent().parent()

        for key, value in list(control_panel.curve_dict.items()):
            if value == curve:
                del control_panel.curve_dict[key]
                break

    @QtCore.Slot()
    def set_min_range(self, value: float = None):
        if value is None:
            value = float(self.sender().text())
        else:
            self.min_range_line_edit.setText(f"{value:.3g}")
        self.source.min_range = value

    @QtCore.Slot()
    def set_max_range(self, value: float = None):
        if value is None:
            value = float(self.sender().text())
        else:
            self.max_range_line_edit.setText(f"{value:.3g}")
        self.source.min_range = value

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
        self.settings_modal.show()

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
            self.layout().removeWidget(self.placeholder)
            index = self.layout().indexOf(item) + 1  # drop below target row
            index = max(1, index)  # don't drop above axis detail row
            self.layout().insertWidget(index, self.placeholder)

    def dragLeaveEvent(self, event: QtGui.QDragLeaveEvent):
        event.accept()
        self.layout().removeWidget(self.placeholder)
        self.placeholder.hide()

    def dropEvent(self, event: QtGui.QDropEvent):
        event.accept()
        curve_item = event.source()
        curve_item.curve_deleted.disconnect()
        curve_item.curve_deleted.connect(self.curves_list_changed.emit)
        curve_item.active_toggle.setCheckState(self.active_toggle.checkState())
        self.plot.plotItem.unlinkDataFromAxis(curve_item.source)
        self.plot.plotItem.linkDataToAxis(curve_item.source, self.source.name)
        curve_item.source.y_axis_name = self.source.name

        self.layout().removeWidget(curve_item)  # in case we're reordering within an AxisItem
        self.layout().replaceWidget(self.placeholder, curve_item)
        self.placeholder.hide()
        if not self._expanded:
            self.toggle_expand()
        self.curves_list_changed.emit()

    def close(self) -> bool:
        while self.layout().count() > 1:
            self.layout().itemAt(1).widget().close()
        self.source.sigYRangeChanged.disconnect(self.handle_range_change)
        self.source.linkedView().sigRangeChangedManually.disconnect(self.disable_auto_range)
        index = self.plot._axes.index(self.source)
        self.plot.removeAxisAtIndex(index)
        self.setParent(None)
        self.deleteLater()
        return super().close()


class DragHandle(QtWidgets.QPushButton):
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        event.ignore()


class CurveItem(QtWidgets.QWidget):
    curve_deleted = QtCore.Signal(object)

    icon_disconnected = qta.icon("msc.debug-disconnect")

    def __init__(self, plot_curve_item: ArchivePlotCurveItem):
        super().__init__()
        self.source = plot_curve_item
        self.is_formula = self._is_formula_curve()
        
        self.setLayout(QtWidgets.QHBoxLayout())

        self.active_toggle = ToggleSwitch("Active")
        self.handle = DragHandle()
        self.handle.setFlat(True)
        self.handle.setIcon(qta.icon("ph.dots-six-vertical", scale_factor=1.5))
        self.handle.setStyleSheet("border: None;")
        self.handle.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))
        self.layout().addWidget(self.handle)

        self.active_toggle = QtWidgets.QCheckBox("Active")
        self.active_toggle.setCheckState(QtCore.Qt.Checked if self.source.isVisible() else QtCore.Qt.Unchecked)
        self.active_toggle.stateChanged.connect(self.set_active)
        self.layout().addWidget(self.active_toggle)

        second_layout = QtWidgets.QVBoxLayout()
        self.layout().addLayout(second_layout)
        pv_settings_layout = QtWidgets.QHBoxLayout()
        second_layout.addLayout(pv_settings_layout)
        data_type_layout = QtWidgets.QHBoxLayout()
        second_layout.addLayout(data_type_layout)

        self.label = QtWidgets.QLineEdit()
        self.label.setText(self.source.name())
        self.label.editingFinished.connect(self.set_curve_pv)
        self.label.returnPressed.connect(self.label.clearFocus)
        pv_settings_layout.addWidget(self.label)
        self.pv_settings_button = QtWidgets.QPushButton()
        self.pv_settings_button.setIcon(qta.icon("msc.settings-gear", color="#444444"))
        self.pv_settings_button.setFlat(True)
        self.pv_settings_modal = None
        self.pv_settings_button.clicked.connect(self.show_settings_modal)
        pv_settings_layout.addWidget(self.pv_settings_button)
        self.delete_button = QtWidgets.QPushButton()
        self.delete_button.setIcon(qta.icon("msc.trash"))
        self.delete_button.setFlat(True)
        self.delete_button.clicked.connect(self.close)
        pv_settings_layout.addWidget(self.delete_button)

        self.setup_line_edit()

        self.live_toggle = QtWidgets.QCheckBox("Live")
        self.live_toggle.setCheckState(QtCore.Qt.Checked if self.source.liveData else QtCore.Qt.Unchecked)
        self.live_toggle.stateChanged.connect(self.set_live_data_connection)
        data_type_layout.addWidget(self.live_toggle)
        self.live_connection_status = QtWidgets.QLabel()
        self.live_connection_status.setPixmap(self.icon_disconnected.pixmap(16, 16))
        self.live_connection_status.setToolTip("Not connected to live data")
        self.source.live_channel_connection.connect(self.update_live_icon)
        data_type_layout.addWidget(self.live_connection_status)

        self.archive_toggle = QtWidgets.QCheckBox("Archive")
        self.archive_toggle.setCheckState(QtCore.Qt.Checked if self.source.use_archive_data else QtCore.Qt.Unchecked)
        self.archive_toggle.stateChanged.connect(self.set_archive_data_connection)
        data_type_layout.addWidget(self.archive_toggle)
        self.archive_connection_status = QtWidgets.QLabel()
        self.archive_connection_status.setPixmap(self.icon_disconnected.pixmap(16, 16))
        self.archive_connection_status.setToolTip("Not connected to archive data")
        self.source.archive_channel_connection.connect(self.update_archive_icon)
        data_type_layout.addWidget(self.archive_connection_status)

        data_type_layout.addStretch()

    @property
    def plot(self):
        return self.parent().plot

    def set_active(self, state: QtCore.Qt.CheckState):
        if state == QtCore.Qt.Unchecked:
            self.source.hide()
        else:
            self.source.show()

    def set_live_data_connection(self, state: QtCore.Qt.CheckState) -> None:
        self.source.liveData = state == QtCore.Qt.Checked

    def set_archive_data_connection(self, state: QtCore.Qt.CheckState) -> None:
        self.source.use_archive_data = state == QtCore.Qt.Checked

    def update_live_icon(self, connected: bool) -> None:
        self.live_connection_status.setVisible(not connected)

    def update_archive_icon(self, connected: bool) -> None:
        self.archive_connection_status.setVisible(not connected)

    @QtCore.Slot()
    def show_settings_modal(self):
        if self.pv_settings_modal is None:
            self.pv_settings_modal = CurveSettingsModal(self.pv_settings_button, self.plot, self.source)
        self.pv_settings_modal.show()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.LeftButton and self.handle.geometry().contains(event.position().toPoint()):
            self.hide()  # hide actual widget so it doesn't conflict with pixmap on cursor
            drag = QtGui.QDrag(self)
            drag.setMimeData(QtCore.QMimeData())
            drag.setPixmap(self.grab())
            drag.setHotSpot(self.handle.geometry().center())
            drag.exec()
            self.show()  # show curve after drag, even if it ended outside of an axis

    def close(self) -> bool:
        curve = self.source
        control_panel = self.parent().parent().parent().parent()

        try:
            control_panel.plot.removeCurve(self.source)
        except ValueError as e:
            logger.debug(f"Warning: Curve already removed: {e}")

        for key, value in list(control_panel._curve_dict.items()):
            if value == curve:
                del control_panel._curve_dict[key]
                control_panel.curve_list_changed.emit()
                break

        self.setParent(None)
        self.deleteLater()

        if self.parent():
            self.curve_deleted.emit(curve)

        return super().close()

    def _is_formula_curve(self):
        """Check if this is a formula curve"""
        return isinstance(self.source, FormulaCurveItem)

    def setup_line_edit(self):
        """Set up the line edit with appropriate behavior for formula vs regular curves"""
        if self.is_formula:
            # For formula curves, show the formula and allow editing
            if hasattr(self.source, 'formula'):
                self.label.setText(self.source.formula)
            elif hasattr(self.source, 'name'):
                self.label.setText(self.source.name())
            
            self.label.setPlaceholderText("Edit formula (f://...)")
            # Disconnect existing connections to avoid conflicts
            try:
                self.label.editingFinished.disconnect()
                self.label.returnPressed.disconnect()
            except:
                pass
            
            # Only connect to returnPressed to avoid duplicate triggers
            self.label.returnPressed.connect(self.update_formula)
            self.label.returnPressed.connect(self.label.clearFocus)
        else:
            # For regular curves, use existing behavior
            self.label.setText(self.source.name())
            self.label.setPlaceholderText("PV Name")
            # Make sure regular PV connections are set up
            try:
                self.label.editingFinished.disconnect()
                self.label.returnPressed.disconnect()
            except:
                pass
            self.label.editingFinished.connect(self.set_curve_pv)
            self.label.returnPressed.connect(self.label.clearFocus)

    def update_formula(self):
        """Handle formula updates when user edits the formula text"""
        # Prevent multiple simultaneous updates
        if hasattr(self, '_updating_formula') and self._updating_formula:
            return
        
        new_formula = self.label.text().strip()
        
        if not new_formula.startswith("f://"):
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Formula",
                "Formula must start with 'f://'.\nExample: f://{PV1}+2"
            )
            # Revert to original formula
            if hasattr(self.source, 'formula'):
                self.label.setText(self.source.formula)
            return
        
        # Don't update if the formula hasn't actually changed
        current_formula = getattr(self.source, 'formula', '') if hasattr(self.source, 'formula') else ''
        if new_formula == current_formula:
            return
        
        # Set flag to prevent duplicate updates
        self._updating_formula = True
        
        try:
            # Find the parent AxisItem and ControlPanel
            axis_item = self.get_parent_axis()
            if not axis_item:
                raise RuntimeError("Could not find parent AxisItem")
            
            # Get the control panel
            control_panel = axis_item.control_panel_ref
            if not control_panel:
                # Try traversal method as fallback
                widget = axis_item
                while widget and not hasattr(widget, '_curve_dict'):
                    widget = widget.parent()
                control_panel = widget
            
            if not control_panel:
                raise RuntimeError("Could not find ControlPanel")
            
            # Validate the new formula
            var_names = re.findall(r"{(.+?)}", new_formula)
            
            # Check if all variables exist
            for var_name in var_names:
                if var_name not in control_panel._curve_dict:
                    raise ValueError(f"Variable '{var_name}' not found. Available: {list(control_panel._curve_dict.keys())}")
            
            # For constants, validate the expression
            if not var_names:
                expression = new_formula[4:]  # Remove "f://" prefix
                try:
                    eval(expression)
                except Exception as e:
                    raise ValueError(f"Invalid expression: {expression}")
            
            def delayed_update():
                try:
                    self._perform_formula_update(new_formula, axis_item, control_panel)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(
                        None,  # Use None as parent since self might be deleted
                        "Formula Update Failed",
                        f"Failed to update formula: {str(e)}"
                    )
                finally:
                    # Reset the flag regardless of success/failure
                    if hasattr(self, '_updating_formula'):
                        self._updating_formula = False
            
            QTimer.singleShot(10, delayed_update)  # Small delay to ensure single execution
            
            print(f"Scheduled formula update from '{current_formula}' to '{new_formula}'")
            
        except Exception as e:
            # Reset flag on error
            self._updating_formula = False
            QtWidgets.QMessageBox.critical(
                self,
                "Formula Update Failed",
                f"Failed to update formula: {str(e)}"
            )
            # Revert to original formula
            if hasattr(self.source, 'formula'):
                self.label.setText(self.source.formula)

    def _perform_formula_update(self, new_formula, axis_item, control_panel):
        """Perform the actual formula update - called asynchronously to avoid segfault"""
        try:
            plot = control_panel.plot
            
            # Remove the old curve from the plot
            if self.source in plot._curves:
                plot._curves.remove(self.source)
            plot.plotItem.removeItem(self.source)
            
            # Update the curve dictionary to remove the old reference
            for key, value in list(control_panel._curve_dict.items()):
                if value == self.source:
                    del control_panel._curve_dict[key]
                    break
            
            # Create the new formula curve using PyDM
            var_names = re.findall(r"{(.+?)}", new_formula)
            var_dict = {}
            for var_name in var_names:
                var_dict[var_name] = control_panel._curve_dict[var_name]
            
            # Create new formula curve
            index = len(plot._curves)
            color = ColorButton.index_color(index)
            
            new_formula_curve = plot.addFormulaChannel(
                formula=new_formula,
                name=new_formula,
                pvs=var_dict,
                color=color,
                useArchiveData=True,
                yAxisName=axis_item.source.name
            )
            
            # Force update
            if hasattr(new_formula_curve, 'redrawCurve'):
                new_formula_curve.redrawCurve()
            
            # Update this CurveItem to point to the new formula curve
            self.source = new_formula_curve
            self.is_formula = True
            
            # Update the label to show the new formula
            self.label.setText(new_formula)
            
            # Add the new curve to the curve dictionary
            key = control_panel._generate_pv_key()
            control_panel._curve_dict[key] = new_formula_curve
            
            # Emit the signal that curves changed
            axis_item.curves_list_changed.emit()
            
            print(f"Formula update completed: {new_formula}")
            
        finally:
            # Always reset the updating flag
            if hasattr(self, '_updating_formula'):
                self._updating_formula = False

    def get_parent_axis(self):
        """Find the parent AxisItem by traversing up the widget hierarchy"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'add_formula_curve'):  
                return parent
            parent = parent.parent()
        return None

    @QtCore.Slot()
    def set_curve_pv(self, pv: str = None):
        if pv is None and self.sender():
            pv = self.sender().text()
        
        if self.is_formula:
            self.update_formula()
            return
        
        self.source.address = pv