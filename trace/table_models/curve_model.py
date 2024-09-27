import re
from typing import Any, Dict, List, Optional
from functools import partial

from qtpy import sip
from qtpy.QtGui import QBrush, QColor
from qtpy.QtCore import Qt, Slot, Signal, QObject, QModelIndex

from pydm.widgets.baseplot import BasePlot, BasePlotCurveItem
from pydm.widgets.archiver_time_plot import FormulaCurveItem, ArchivePlotCurveItem
from pydm.widgets.archiver_time_plot_editor import PyDMArchiverTimePlotCurvesModel

from config import logger
from widgets import ColorButton
from table_models import ArchiverAxisModel


class ArchiverCurveModel(PyDMArchiverTimePlotCurvesModel):
    """Model used for storing and editing archiver time plot curves.

    Parameters
    ----------
    parent (optional) : QObject
        The parent object for the table model.
    plot : BasePlot
        The plotting widget that the curves will be displayed on.
    axis_model : ArchiverAxisModel
        The table model that stores the axes for the plot.
    """

    multiplePVInsert = Signal(str)
    invalid_index_signal = Signal(QModelIndex)

    def __init__(self, parent: Optional[QObject], plot: BasePlot, axis_model: ArchiverAxisModel) -> None:
        super(ArchiverCurveModel, self).__init__(plot, parent)
        # Remove columns for bar width, limits, and thresholds. Bar graph plot style is unused
        self._column_names = (
            self._column_names[:6]
            + ("Style",)
            + self._column_names[6:10]
            + (
                "Hidden",
                "",
            )
        )
        self._row_names = []
        self._axis_model = axis_model
        self._invalid_live_channels = set()
        self._invalid_arch_channels = set()

        self._axis_model.remove_curve.connect(self.remove_curve)
        self.checkable_cols.add(self.getColumnIndex("Hidden"))
        self.defaultColorIndex = 0
        self.append()

    def __contains__(self, key: str) -> bool:
        """Check if the given key is a channel that already exists in the model.
        Allows for the use of the 'in' keyword.

        Parameters
        ----------
        key : str
            Channel to check existence of

        Returns
        -------
        bool
            If the channel already exists in the model
        """
        for curve in self._plot._curves:
            if hasattr(curve, "address") and curve.address == key:
                return True
            elif hasattr(curve, "formula") and curve.formula == key:
                return True
        return False

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole) -> Any:
        """Get data from the model for a given index and a given data role. If
        the curve at the given index is invalid, the Channel column is turned red.

        Parameters
        ----------
        index : QModelIndex
            The index for the data requested
        role : Qt.ItemDataRole
            The role for the data requested, by default Qt.DisplayRole
        """
        col_name = self._column_names[index.column()]
        if not self._plot._curves or (col_name not in ("Live Data", "Archive Data")):
            return super().data(index, role)
        elif role not in (Qt.BackgroundRole, Qt.ToolTipRole):
            return super().data(index, role)

        curve = self.curve_at_index(index)
        invalid_cell = col_name == "Live Data" and curve in self._invalid_live_channels
        invalid_cell |= col_name == "Archive Data" and curve in self._invalid_arch_channels

        if role == Qt.BackgroundRole and invalid_cell:
            return QBrush(QColor("#ffdddd"))
        elif role == Qt.ToolTipRole and invalid_cell:
            if col_name == "Live Data":
                return f"{curve.name()} has no live connection"
            if col_name == "Archive Data":
                return f"{curve.name()} has no archiver connection"

        return super().data(index, role)

    def get_data(self, column_name: str, curve: ArchivePlotCurveItem) -> Any:
        """Get data from the model based on column name.

        Parameters
        ----------
        column_name : str
            The type of data that should be returned. Should be a name
            of one of the model's columns.
        curve : ArchivePlotCurveItem
            The curve that data should be returned for.
        """
        if column_name == "Style":
            if curve.stepMode in ["right", "left", "center"]:
                return "Step"
            elif not curve.stepMode:
                return "Direct"
        if column_name == "Hidden":
            return not curve.isVisible()
        if column_name == "Line Width":
            return str(int(curve.lineWidth)) + "px"
        if column_name == "Symbol Size":
            return str(int(curve.symbolSize)) + "px"
        return super(ArchiverCurveModel, self).get_data(column_name, curve)

    def set_data(self, column_name: str, curve: BasePlotCurveItem, value: Any) -> bool:
        """Set data on the input curve for the given name and value.

        Parameters
        ----------
        column_name : str
            The type of data that should be returned. Should be a name
            of one of the model's columns.
        curve : ArchivePlotCurveItem
            The curve that data should be returned for.
        value : Any
            The new value that the curve's data should be set to.

        Returns
        -------
        bool
            If the data was successfully set.
        """
        logger.debug(f"Setting {column_name} data for curve {curve.name}")
        ret_code = False
        if sip.isdeleted(curve):
            return False
        if column_name == "Channel":
            if re.search(r"[\n\r,]", value):
                self.multiplePVInsert.emit(value)
                return False
            # Check if this thing already in curves model
            if value in self:
                logger.warning("Duplicate channels not allowed")
                return False

            curve.show()
            # If we are changing the channel, then we need to check the current type, and the type we're going to
            value_is_formula = value.startswith("f://")
            curve_is_formula = isinstance(curve, FormulaCurveItem)
            index = self.index(self._plot._curves.index(curve), 0)

            if value_is_formula and not curve_is_formula:
                # Regardless of starting point, going to a formula is handled in this one function
                try:
                    ret_code = self.replaceToFormula(index=index, formula=value)
                except (SyntaxError, ValueError) as e:
                    logger.error(e)
                    return False
            elif value_is_formula and curve_is_formula:
                try:
                    pv_dict = self.formulaToPVDict(self._row_names[index.row()], value)
                    curve.formula = value
                    curve.pvs = pv_dict
                except (SyntaxError, ValueError) as e:
                    logger.error(e)
                    return False
            elif not value_is_formula:
                if not curve_is_formula:
                    logger.debug(f"Disconnecting old channel(s): {curve.address}")
                    curve.address = str(value)
                    logger.debug(f"Connecting new channel(s): {curve.address}")
                else:
                    self.replaceToArchivePlot(curve=curve, index=index, address=value, color=curve.color)
            curve.setData(name=str(value))

            self._invalid_live_channels.discard(curve)
            self._invalid_arch_channels.discard(curve)

            if value and self.curve_at_index(-1) is curve:
                self.append()
        elif column_name == "Y-Axis Name":
            # If we change the Y-Axis, unlink from previous and link to new
            if value == curve.y_axis_name:
                return True
            self.plot.plotItem.unlinkDataFromAxis(curve)
            self.plot.linkDataToAxis(curve, value)
            ret_code = super(ArchiverCurveModel, self).set_data(column_name, curve, value)
            # Link to correct axis and unhide if necessary
            if curve.isVisible():
                self.plot.plotItem.axes[curve.y_axis_name]["item"].show()
        elif column_name == "Style":
            curve.stepMode = value
            ret_code = True
        elif column_name == "Hidden":
            # Handle toggling hidden
            hidden = bool(value)
            if hidden:
                curve.hide()
                self._axis_model.plot.plotItem.autoVisible(curve.y_axis_name)
            else:
                curve.show()
                self._axis_model.plot.plotItem.axes[curve.y_axis_name]["item"].show()
            ret_code = True
        else:
            ret_code = super(ArchiverCurveModel, self).set_data(column_name, curve, value)
        self.plot.plotItem.autoVisible(curve.y_axis_name)
        logger.debug("Finished setting curve data")
        return ret_code

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Return flags that determine how users can interact with the items
        in the table. Disables checkboxes for invalid channels.

        Parameters
        ----------
        index : QModelIndex
            The index in the model that flags are being returned for

        Returns
        -------
        Qt.ItemFlags
            Returns the model's default flags, and if the column is Live Data or
            Archive Data, then may also disable the index depending on channel status.
        """
        flags = super().flags(index)

        col_name = self._column_names[index.column()]
        if col_name in ("Live Data", "Archive Data"):
            curve = self.curve_at_index(index)
            if col_name == "Live Data" and curve in self._invalid_live_channels:
                flags &= not Qt.ItemIsEnabled
            elif col_name == "Archive Data" and curve in self._invalid_arch_channels:
                flags &= not Qt.ItemIsEnabled

        return flags

    def append(
        self, address: Optional[str] = None, name: Optional[str] = None, color: Optional[QColor] = None, addAxis=True
    ) -> None:
        """Add a new curve item to plot and the data model.

        Parameters
        ----------
        address : str, optional
            The PV address that the curve should gather data from.
        name : str, optional
            The display name for the curve.
        color : QColor, optional
            The curve's color on the plot.
        """
        logger.debug("Adding new empty curve to plot")
        if addAxis:
            self._axis_model.append()
        y_axis = self._axis_model.get_axis(-1)
        if not color:
            color = ColorButton.index_color(self.defaultColorIndex)
            self.defaultColorIndex += 1
        self._row_names.append(self.next_header())

        self.beginInsertRows(QModelIndex(), len(self._plot._curves), len(self._plot._curves))
        # By default, add a blank archivePlotCurveItem such that there's an empty row to add PVs or formulas to.
        self._plot.addYChannel(y_channel=address, name=name, color=color, useArchiveData=True, yAxisName=y_axis.name)
        self.endInsertRows()

        new_curve = self._plot._curves[-1]
        new_curve.hide()
        if self.rowCount() != 1:
            logger.debug("Hide blank Y-axis")
            self._axis_model.plot.plotItem.axes[y_axis.name]["item"].hide()
        new_curve.unitSignal.connect(self.setAxis)
        logger.debug("Finished adding new empty curve to plot")

        curve = self.curve_at_index(-1)
        curve.live_channel_connection.connect(self.live_connection_slot)
        curve.archive_channel_connection.connect(self.archive_connection_slot)

    def set_model_curves(self, curves: List[Dict] = []) -> None:
        """Reset the model to only contain the list of given curves.

        Parameters
        ----------
        curves : List[Dict]
            The list of curves to set the model to use. Formatted as a list of
            key-value pairs.
        """
        logger.debug("Clearing curves model.")
        self.beginResetModel()
        self._plot.clearCurves()
        self._row_names = []
        self.defaultColorIndex = 0
        for c in curves:
            for k, v in c.items():
                if v is None:
                    del c[k]
            if "channel" in c:
                logger.debug(f"Adding curve: {c['channel']}")
                c["y_channel"] = c["channel"]
                del c["channel"]
                self._plot.addYChannel(**c)
                self._row_names.append(self.next_header())
            else:
                logger.debug(f"Adding formula: {c['formula']}")
                self.append()
                headers = re.findall("{(.+?)}", c["formula"])
                splitFormula = re.split("{.+?}", c["formula"])
                newFormula = splitFormula.pop(0)
                for header in headers:
                    # For every header referenced in our formula
                    if header not in c["curveDict"].keys():
                        continue
                    # Confirmed the header is in our curves list
                    name = c["curveDict"][header]
                    if name not in self:
                        continue
                    # Manually find it and replace the header in the formula
                    for i in range(len(self.plot.curves)):
                        curve = self._plot._curves[i]
                        found_curve = hasattr(curve, "address") and curve.address == name
                        found_curve |= hasattr(curve, "formula") and curve.formula == name
                        if found_curve:
                            newFormula += "{" + self._row_names[i] + "}" + splitFormula.pop(0)
                            break
                # change formula to match new stuff
                index = self.index(-1, 0)
                del c["formula"]
                del c["curveDict"]
                self.replaceToFormula(index=index, formula=newFormula, **c)
        self.append()
        self._plot.set_needs_redraw()
        self._plot.redrawPlot()
        self.endResetModel()
        logger.debug("Finished setting curves model")

    def replaceToArchivePlot(
        self, curve: BasePlotCurveItem, index: QModelIndex, address: str, color: Optional[QColor] = None
    ):
        """Replace the existing curve with a new ArchivePlotCurveItem"""
        self.append(address=address, name=address, color=color)
        self._plot._curves[index.row()] = self._plot._curves[-1]
        self.beginRemoveRows(QModelIndex(), self.rowCount() - 1, self.rowCount() - 1)
        self.plot._curves = self.plot._curves[:-1]
        self.plot.removeItem(curve)
        self.endRemoveRows()

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

    def replaceToFormula(
        self, index: QModelIndex, formula: str, color: Optional[str] = None, yAxisName: Optional[str] = None, **kwargs
    ) -> bool:
        """Replaces existing ArchivePlotCurveItem with a new FormulaCurveItem

        Parameters
        ----------
        formula : str
            The Formula we want to graph
        name : str, optional
            The display name for the curve.
        color : Optional[QColor], optional
            The curve's color on the plot.
        """
        rowName = self._row_names[index.row()]
        pvdict = self.formulaToPVDict(rowName, formula)
        curve = self._plot._curves[index.row()]
        if not color:
            color = curve.color

        # Handle Archives and formulas differently
        if index.row() == self.rowCount() - 1:
            self.append()
        if not yAxisName:
            yAxisName = curve.y_axis_name
        FormulaCurve = self._plot.addFormulaChannel(
            formula=formula, name=formula, pvs=pvdict, color=color, useArchiveData=True, yAxisName=yAxisName
        )
        self._plot._curves[index.row()] = FormulaCurve
        FormulaCurve.formula_invalid_signal.connect(partial(self.invalidFormula, header=rowName))
        # Need to check if Formula is referencing a dead row
        self.plot.plotItem.unlinkDataFromAxis(curve)
        self.plot.removeItem(curve)
        # Disconnect everything and delete it, create a new Formula with the dictionary of curve
        [ch.disconnect() for ch in curve.channels() if ch]
        del curve

        FormulaCurve.formula_invalid_signal.connect(partial(self.invalidFormula, header=rowName))
        FormulaCurve.live_channel_connection.connect(self.live_connection_slot)
        FormulaCurve.archive_channel_connection.connect(self.archive_connection_slot)
        FormulaCurve.connection_status_check()
        return True

    def invalidFormula(self, header):
        """Handling row deletion if the formula is no longer valid"""
        rindex = self._row_names.index(header)
        index = self.index(rindex, 0)
        if not index.isValid() or index.row() == (self.rowCount() - 1):
            return False
        del self._row_names[index.row()]
        curve = self._plot._curves[rindex]
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        if curve.y_axis_name in self._plot.plotItem.axes:
            self.plot.plotItem.unlinkDataFromAxis(curve)
        self.plot.removeItem(curve)
        self.plot._curves.remove(curve)
        self.endRemoveRows()
        if not self._plot._curves:
            self.append()
        del curve
        # Prompt a redraw top cascade and delete any consequential formulas
        self._plot.archive_data_received()
        self._plot.set_needs_redraw()
        self._plot.redrawPlot()

    def removeAtIndex(self, index: QModelIndex) -> None:
        """Removes the curve at the given table index.

        Parameters
        ----------
        index : QModelIndex
            An index in the row to be removed.
        """
        logger.debug(f"Removing curve at index {index.row()}")
        if isinstance(self._plot._curves[index.row()], FormulaCurveItem):
            # Formula Curves don't have channel data so we should just remove it as if it were no longer valid
            self.invalidFormula(self._row_names[index.row()])
            return False

        if not index.isValid() or index.row() == (self.rowCount() - 1):
            return False
        del self._row_names[index.row()]
        curve = self._plot._curves[index.row()]
        [ch.disconnect() for ch in curve.channels() if ch]
        ret = super(ArchiverCurveModel, self).removeAtIndex(index)
        if not self._plot._curves:
            self.append()
        self._plot.archive_data_received()
        self._plot.set_needs_redraw()
        self._plot.redrawPlot()
        logger.debug(f"Finished removing curve previously at index {index.row()}")
        self._plot.archive_data_received()
        self._plot.set_needs_redraw()
        self._plot.redrawPlot()
        return ret

    def headerData(self, section, orientation, role=Qt.DisplayRole) -> Any:
        """Return row header for given index"""
        if role == Qt.DisplayRole and orientation == Qt.Vertical and section < self.rowCount():
            return self._row_names[section]
        return super().headerData(section, orientation, role)

    def next_header(self) -> str:
        """Construct the string for the next row in the table based on
        the current last row.

        Returns
        -------
        str
            The string for the header for the next row.
        """
        if not self._row_names:
            return "A"

        prev_header = self._row_names[-1]
        next_header = ""

        if prev_header == "Z" * len(prev_header):
            return "A" * (len(prev_header) + 1)

        inc = 1
        for i in range(len(prev_header) - 1, -1, -1):
            old_val = ord(prev_header[i]) - ord("A") + inc
            new_val = chr(old_val % 26 + ord("A"))
            next_header = new_val + next_header
            inc = 1 if prev_header[i] == "Z" else 0

        return next_header

    def curve_at_index(self, index: int | QModelIndex) -> ArchivePlotCurveItem:
        """Return the curve item at the given index.

        Parameters
        ----------
        index : int | QModelIndex
            The table index of the requested curve.

        Returns
        -------
        ArchivePlotCurveItem
            The requested curve.
        """
        if isinstance(index, QModelIndex):
            index = index.row()
        return self._plot.curveAtIndex(index)

    @Slot(str)
    def setAxis(self, units: str):
        """When we receive a unit of the curve, we will connect it to the correct axis"""
        curve = self.sender()

        row = self._plot._curves.index(curve)
        col = self._column_names.index("Y-Axis Name")
        index = self.index(row, col)

        self.parent().update()
        if units not in self.plot.plotItem.axes:
            self._axis_model.append(name=units)

        oldYAxis = curve.y_axis_name
        self.setData(index, units, Qt.EditRole)
        if not self.plot.plotItem.axes[oldYAxis]["item"]._curves:
            self._axis_model.removeAxis(oldYAxis)

    @Slot(object)
    def remove_curve(self, curve: BasePlotCurveItem) -> None:
        """Necessary specifically for when an axis is deleted
        To properly delete all of its connected curves

        Parameters
        ----------

        curve: BasePlotCurveItem
            The curve we want to delete from the model"""
        ind = self._plot._curves.index(curve)
        ind = self.index(ind, 0)
        self.removeAtIndex(ind)

    @Slot(bool)
    def live_connection_slot(self, connection: bool) -> None:
        """Slot connected to curve's live connection signal. Updates
        the model's associated views to reflect connection changes.

        Parameters
        ----------
        connection : bool
            The curve's live connection status.
        """
        curve = self.sender()

        if connection:
            self._invalid_live_channels.discard(curve)
        else:
            self._invalid_live_channels.add(curve)
            inter = self._invalid_live_channels & self._invalid_arch_channels
            if curve in inter:
                curve.hide()
                self._axis_model.plot.plotItem.autoVisible(curve.y_axis_name)

        row = self._plot._curves.index(curve)
        col = self._column_names.index("Live Data")
        ind = self.index(row, col)
        self.invalid_index_signal.emit(ind)

    @Slot(bool)
    def archive_connection_slot(self, connection: bool) -> None:
        """Slot connected to curve's archive connection signal. Updates
        the model's associated views to reflect connection changes.

        Parameters
        ----------
        connection : bool
            The curve's archive connection status.
        """
        curve = self.sender()

        if connection:
            self._invalid_arch_channels.discard(curve)
        else:
            self._invalid_arch_channels.add(curve)
            inter = self._invalid_live_channels & self._invalid_arch_channels
            if curve in inter:
                curve.hide()
                self._axis_model.plot.plotItem.autoVisible(curve.y_axis_name)

        row = self._plot._curves.index(curve)
        col = self._column_names.index("Archive Data")
        ind = self.index(row, col)
        self.invalid_index_signal.emit(ind)
