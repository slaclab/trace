import re
from typing import (Any, List, Dict, Optional)
from functools import partial
from qtpy.QtGui import QColor
from qtpy.QtCore import (QObject, QModelIndex, Qt, Slot, Signal)
from qtpy import sip
from pydm.widgets.baseplot import BasePlot, BasePlotCurveItem
from pydm.widgets.archiver_time_plot import ArchivePlotCurveItem, FormulaCurveItem
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

    def __init__(self, parent: Optional[QObject], plot: BasePlot, axis_model: ArchiverAxisModel) -> None:
        super(ArchiverCurveModel, self).__init__(plot, parent)
        # Remove columns for bar width, limits, and thresholds. Bar graph plot style is unused
        self._column_names = self._column_names[:6] + ("Style",) + self._column_names[6:10] + ("Hidden", "",)
        self._row_names = []
        self._axis_model = axis_model
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
            if hasattr(curve, "channel"):
                if curve.address == key:
                    return True
            elif curve.formula == key:
                return True
        return False

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
            return str(int(curve.symbolSize))  + "px"
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
        index = self.index(self._plot._curves.index(curve),0)
        if sip.isdeleted(curve):
            return False
        if column_name == "Channel":
            if re.search('[\s,]', value):
                self.multiplePVInsert.emit(value)
                return False
            curve.show()
            # If we are changing the channel, then we need to check the current type, and the type we're going to
            index = self.index(self._plot._curves.index(curve),0)
            value_is_formula = value.startswith("f://")
            curve_is_formula = isinstance(curve, FormulaCurveItem)
            if value_is_formula and not curve_is_formula:
                # Regardless of starting point, going to a formula is handled in this one function
                try:
                    ret_code = self.replaceToFormula(index = index, formula = value)
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
                # Check if this thing already in curves model
                if value in self:
                    logger.warning("You can only have one of each PV")
                    return False
                if not curve_is_formula:
                    logger.debug(f"Disconnecting old channel(s): {curve.address}")
                    [ch.disconnect() for ch in curve.channels() if ch]
                    curve.address = str(value)
                    logger.debug(f"Connecting new channel(s): {curve.address}")
                    [ch.connect() for ch in curve.channels() if ch]
                else:
                    self.replaceToArchivePlot(curve=curve, index=index, address=value, color=curve.color)
            if value and self._plot._curves[-1] is curve:
                self.append()
            curve.setData(name=str(value))
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

    def append(self, address: Optional[str] = None, name: Optional[str] = None, color: Optional[QColor] = None, addAxis=True) -> None:
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
        self._plot._curves[-1].hide()
        if self.rowCount() != 1:
            logger.debug("Hide blank Y-axis")
            self._axis_model.plot.plotItem.axes[y_axis.name]["item"].hide()
        logger.debug("Finished adding new empty curve to plot")

    def set_model_curves(self, curves: List[Dict] = []) -> None:
        """Reset model curves to given list of curve properties.

        Parameters
        ----------
        curves : List[Dict]
            List of curve properties.
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
            if 'channel' in c:
                logger.debug(f"Adding curve: {c['channel']}")
                c['y_channel'] = c['channel']
                del c['channel']
                self._plot.addYChannel(**c)
                self._row_names.append(self.next_header())
            else:
                logger.debug(f"Adding formula: {c['formula']}")
                self.append()
                headers = re.findall("{(.+?)}", c['formula'])
                splitFormula = re.split("{.+?}", c['formula'])
                newFormula = splitFormula.pop(0)
                for header in headers:
                    # For every header referenced in our formula
                    if header not in c['curveDict'].keys():
                        continue
                    # Confirmed the header is in our curves list
                    name = c['curveDict'][header]
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
                index = self.index(-1,0)
                del c['formula']
                del c['curveDict']
                self.replaceToFormula(index=index, formula=newFormula, **c)
        self.append()
        self._plot.set_needs_redraw()
        self._plot.redrawPlot()
        self.endResetModel()
        logger.debug("Finished setting curves model")

    def replaceToArchivePlot(self, curve: BasePlotCurveItem, index: QModelIndex, address: str, color: Optional[QColor] = None):
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
            else:
                # If it's good, add it to the dictionary of curves. rindex = row index (int) as opposed to index, which is a QModelIndex
                rindex = self._row_names.index(pv)
                pvdict[pv] = self._plot._curves[rindex]
        if not self.recursionCheck(rowName, pvdict):
            raise ValueError(f"There was a recursive dependency somewhere")
        if not pvdict:
            try:
                eval(formula[4:])
            except SyntaxError:
                raise SyntaxError("Invalid Input")
        return pvdict

    def replaceToFormula(self, index: QModelIndex, formula: str, color: Optional[str] = None, yAxisName: Optional[str] = None, **kwargs) -> bool:
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
        # Find row headers using regex
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
        FormulaCurve =  self._plot.addFormulaChannel(formula=formula, name=formula, pvs=pvdict,color=color, useArchiveData=True, yAxisName=yAxisName)
        self._plot._curves[index.row()] = FormulaCurve
        FormulaCurve.formula_invalid_signal.connect(partial(self.invalidFormula, header = rowName))
        # Need to check if Formula is referencing a dead row
        self.plot.plotItem.unlinkDataFromAxis(curve)
        self.plot.removeItem(curve)
        # Disconnect everything and delete it, create a new Formula with the dictionary of curve
        [ch.disconnect() for ch in curve.channels() if ch]
        del curve
        return True

    def invalidFormula(self, header):
        """Handling row deletion if the formula is no longer valid"""
        rindex = self._row_names.index(header)
        index = self.index(rindex,0)
        if not index.isValid() or index.row() == (self.rowCount() - 1):
            return False
        del self._row_names[index.row()]
        curve = self._plot._curves[rindex]
        self.beginRemoveRows(QModelIndex(), index.row(), index.row())
        if curve.y_axis_name in self._plot.plotItem.axes:
            self.plot.plotItem.unlinkDataFromAxis(curve.y_axis_name)
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
            return 'A'

        prev_header = self._row_names[-1]
        next_header = ""

        if prev_header == 'Z' * len(prev_header):
            return 'A' * (len(prev_header) + 1)

        inc = 1
        for i in range(len(prev_header) - 1, -1, -1):
            old_val = ord(prev_header[i]) - ord('A') + inc
            new_val = chr(old_val % 26 + ord('A'))
            next_header = new_val + next_header
            inc = 1 if prev_header[i] == 'Z' else 0

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
