from typing import (Any, List, Dict, Optional)
from qtpy.QtGui import (QColor, QBrush)
from qtpy.QtCore import (QObject, QModelIndex, Qt, Signal, Slot)
from pydm.widgets.baseplot import BasePlot
from pydm.widgets.archiver_time_plot import ArchivePlotCurveItem
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

    invalid_index_signal = Signal(QModelIndex)

    def __init__(self, parent: Optional[QObject], plot: BasePlot, axis_model: ArchiverAxisModel) -> None:
        super(ArchiverCurveModel, self).__init__(plot, parent)
        # Remove columns for bar width, limits, and thresholds. Bar graph plot style is unused
        self._column_names = self._column_names[:6] + ("Style",) + self._column_names[6:10] + ("",)
        self._row_names = []
        self._axis_model = axis_model
        self._invalid_curves = set()
        self.append()

    def data(self, index: QModelIndex, role: Qt.ItemDataRole=Qt.DisplayRole) -> Any:
        """Get data from the model for a given index and a given data role. If
        the curve at the given index is invalid, the Channel column is turned red.

        Parameters
        ----------
        index : QModelIndex
            The index for the data requested
        role : Qt.ItemDataRole
            The role for the data requested, by default Qt.DisplayRole
        """
        if (index.column() == 0) and self._plot._curves:
            curve = self.curve_at_index(index)
            if curve in self._invalid_curves:
                if role == Qt.BackgroundRole:
                    return QBrush(QColor("#ffdddd"))
                if role == Qt.ForegroundRole:
                    return QBrush(QColor("red"))
                if role == Qt.ToolTipRole:
                    return f"{curve.address} is not a valid channel"
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
        return super(ArchiverCurveModel, self).get_data(column_name, curve)

    def set_data(self, column_name: str, curve: ArchivePlotCurveItem, value: Any) -> bool:
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
        logger.debug(f"Setting {column_name} data for curve {curve.address}")
        ret_code = False
        if column_name == "Channel":
            if value == curve.address:
                return True

            logger.debug(f"Disconnecting old channel(s): {curve.address}")
            curve.address = str(value)
            logger.debug(f"Connecting new channel(s): {curve.address}")

            if not curve.name():
                curve.setData(name=str(value))

            if value and self.curve_at_index(-1) is curve:
                self.append()

            self._invalid_curves.discard(curve)

            ret_code = True
        elif column_name == "Style":
            curve.stepMode = value
            ret_code = True
        else:
            ret_code = super(ArchiverCurveModel, self).set_data(column_name, curve, value)

        logger.debug("Finished setting curve data")
        return ret_code

    def append(self, address: Optional[str] = None, name: Optional[str] = None, color: Optional[QColor] = None) -> None:
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
        if self.rowCount() != 1:
            self._axis_model.append()
        y_axis = self._axis_model.get_axis(-1)
        if not color:
            color = ColorButton.index_color(self.rowCount())
        self._row_names.append(self.next_header())

        self.beginInsertRows(QModelIndex(), len(self._plot._curves), len(self._plot._curves))
        self._plot.addYChannel(y_channel=address, name=name, color=color, useArchiveData=True, yAxisName=y_axis.name)
        self.endInsertRows()
        logger.debug("Finished adding new empty curve to plot")

        curve = self.curve_at_index(-1)
        curve.archive_channel_connection.connect(self.archive_connection_slot)

    def set_model_curves(self, curves: List[Dict]) -> None:
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

        for c in curves:
            logger.debug(f"Adding curve: {c['channel']}")
            for k, v in c.items():
                if v is None:
                    del c[k]
            c['y_channel'] = c['channel']
            del c['channel']
            self._plot.addYChannel(**c)
            self._row_names.append(self.next_header())
        self.append()
        self.endResetModel()
        logger.debug("Finished setting curves model")

    def removeAtIndex(self, index: QModelIndex) -> None:
        """Removes the curve at the given table index.

        Parameters
        ----------
        index : QModelIndex
            An index in the row to be removed.
        """
        logger.debug(f"Removing curve at index {index.row()}")
        if not index.isValid() or index.row() == (self.rowCount() - 1):
            return False
        del self._row_names[index.row()]
        ret = super(ArchiverCurveModel, self).removeAtIndex(index)

        if not self._plot._curves:
            self.append()
        logger.debug(f"Finished removing curve previously at index {index.row()}")
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
            self._invalid_curves.discard(curve)
        else:
            self._invalid_curves.add(curve)

        print(connection, curve)

        ind = self.index(self._plot._curves.index(curve), 0)
        self.invalid_index_signal.emit(ind)
