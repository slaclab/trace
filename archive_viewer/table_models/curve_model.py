from typing import (Any, Optional)
from qtpy.QtCore import (QObject, QModelIndex, Qt)
from pydm.widgets.baseplot import BasePlot, BasePlotCurveItem
from pydm.widgets.archiver_time_plot import ArchivePlotCurveItem, FormulaCurveItem
from pydm.widgets.archiver_time_plot_editor import PyDMArchiverTimePlotCurvesModel
from qtpy.QtGui import QColor
from functools import partial
import re
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

    def __init__(self, parent: Optional[QObject], plot: BasePlot, axis_model: ArchiverAxisModel) -> None:
        super(ArchiverCurveModel, self).__init__(plot, parent)
        self._column_names = self._column_names[:6] + ("Style",) + self._column_names[6:] + ("",)
        self._row_names = []
        self._axis_model = axis_model

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
            return curve.plot_style
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
        ret_code = False
        if column_name == "Channel":
            if value.startswith("f://"):
                index = self.index(self._plot._curves.index(curve),0)
                replaced = self.replaceToFormula(index = index, formula = value)
                return replaced
            else:
                if isinstance(curve,ArchivePlotCurveItem):
                    if value == curve.address:
                        return True
                    [ch.disconnect() for ch in curve.channels() if ch]
                    curve.address = str(value)
                    [ch.connect() for ch in curve.channels() if ch]
                    y_axis = self._axis_model.get_axis(-1)
                    self.plot.linkDataToAxis(curve, y_axis.name)
                else:
                    self.replaceToArchivePlot(curve)
            if not curve.name():
                curve.setData(name=str(value))

            if value and self._plot._curves[-1] is curve:
                if self.rowCount() != 1:
                    self._axis_model.append()
                y_axis = self._axis_model.get_axis(-1)
                row = self.rowCount()
                col = self._column_names.index("Y-Axis Name")
                index = self.index(row, col)
                self.setData(index, y_axis.name)
                self.plot.linkDataToAxis(curve, y_axis.name)
                self.append()
            ret_code = True
        elif column_name == "Style":
            curve.plot_style = str(value)
            ret_code = True
        else:
            ret_code = super(ArchiverCurveModel, self).set_data(column_name, curve, value)
        
        return ret_code

    def append(self, address: Optional[str] = None, name: Optional[str] = None, color: Optional[QColor] = None) -> None:
        """Add a new curve item to plot and the data model.

        Parameters
        ----------
        address : str, optional
            The PV address that the curve should gather data from.
        name : str, optional
            The display name for the curve.
        color : Optional[QColor], optional
            The curve's color on the plot.
        """
        if self.rowCount() == 0:
            self._axis_model.append()        
        y_axis = self._axis_model.get_axis(-1)
        if not color:
            color = ColorButton.index_color(self.rowCount())
        self._row_names.append(self.next_header())
        #          KLYS:LI22:31:KVAC
        self.beginInsertRows(QModelIndex(), len(self._plot._curves), len(self._plot._curves))
        self._plot.addYChannel(y_channel=address, name=name, color=color, useArchiveData=True, yAxisName=y_axis.name)
        self.endInsertRows()
    def replaceToArchivePlot(curve: BasePlotCurveItem):
        print('moo')
    def replaceToFormula(self, index: QModelIndex, formula:str, color: Optional[QColor] = None) -> bool:
        """Add a new curve item to plot and the data model.

        Parameters
        ----------
        address : str, optional
            The PV address that the curve should gather data from.
        name : str, optional
            The display name for the curve.
        color : Optional[QColor], optional
            The curve's color on the plot.
        """
        
        pvs = re.findall("{(.+?)}", formula)
        pvdict = dict()
        rowName = self._row_names[index.row()]
        for pv in pvs:
            if pv not in self._row_names:
                print("Error, " + pv + " is an invalid variable name.")
                return False
            elif pv == rowName:
                print("Error, formula is recursive")
                return False
            else:
                rindex = self._row_names.index(pv)
                pvdict[pv] = self._plot._curves[rindex]
        print("accepted formula")
        curve = self._plot._curves[index.row()] 
        if not color:
            color = ColorButton.index_color(index.row())
        #          KLYS:LI22:31:KVAC
        if isinstance(curve, ArchivePlotCurveItem):
            if index.row() == self.rowCount() - 1:
                self._axis_model.append()
                self.append()
            y_axis = self._axis_model.get_axis(index.row())
            self._plot._curves[index.row()] = self._plot.addFormulaChannel(formula=formula, pvs=pvdict,color=color, useArchiveData=True, yAxisName=y_axis.name)
            self._plot._curves[index.row()].formula_invalid_signal.connect(partial(self.invalidFormula, header = self._row_names[index.row()]))
        else:
            curve.formula = formula
            curve.pvs = pvdict
        return True
    
    def invalidFormula(self, header):
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

    def removeAtIndex(self, index: QModelIndex) -> None:
        """Removes the curve at the given table index.

        Parameters
        ----------
        index : QModelIndex
            An index in the row to be removed.
        """
        if isinstance(self._plot._curves[index.row()], FormulaCurveItem):
            self.invalidFormula(self._row_names[index.row()])
            return
        if not index.isValid() or index.row() == (self.rowCount() - 1):
            return False
        del self._row_names[index.row()]
        ret = super(ArchiverCurveModel, self).removeAtIndex(index)
        if not self._plot._curves:
            self.append()
        self._plot.archive_data_received()
        self._plot.set_needs_redraw()
        self._plot.redrawPlot()
        return ret

    def headerData(self, section, orientation, role=Qt.DisplayRole) -> Any:
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

    def curve_at_index(self, index: QModelIndex) -> ArchivePlotCurveItem:
        """Return the curve item at the given index.

        Parameters
        ----------
        index : QModelIndex
            The table index of the requested curve.

        Returns
        -------
        ArchivePlotCurveItem
            The requested curve.
        """
        return self._plot.curveAtIndex(index)
