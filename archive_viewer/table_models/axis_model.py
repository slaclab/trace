from typing import Any
from qtpy.QtCore import (Qt, QVariant, QPersistentModelIndex, QModelIndex, Signal)
from pydm.widgets.baseplot import BasePlot, BasePlotAxisItem
from pydm.widgets.axis_table_model import BasePlotAxesModel


class ArchiverAxisModel(BasePlotAxesModel):
    """The data model for the axes tab in the properties section. Acts
    as a go-between for the axes in a plot, and QTableView items.

    Parameters
    ----------
    plot : BasePlot
        The model's associated plot widget
    parent : QObject, optional
        The model's parent, by default None
    """
    remove_curve = Signal(object)
    def __init__(self, plot: BasePlot, parent=None) -> None:
        super().__init__(plot, parent)
        self._column_names = self._column_names + ("Hidden","",)
        self.axis_count = 0
        self.checkable_col = {self.getColumnIndex("Enable Auto Range"),
                              self.getColumnIndex("Log Mode"),
                              self.getColumnIndex("Hidden")}

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Return flags that determine how users can interact with the items in the table"""
        flags = super().flags(index)
        if index.column() in self.checkable_col:
            flags = Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable
        return flags

    def data(self, index: QModelIndex, role=Qt.DisplayRole) -> Any:
        """Retrieve the data from the model for a given index using the
        defined role.

        Parameters
        ----------
        index : QModelIndex
            The model's index for the data being retrieved.
        role : Qt.ItemDataRole, optional
            The role used by the view to indicate which type of data it
            needs, by default Qt.DisplayRole
        """
        if not index.isValid():
            return QVariant()
        elif role == Qt.CheckStateRole and index.column() in self.checkable_col:
            value = super().data(index, Qt.DisplayRole)
            return Qt.Checked if value else Qt.Unchecked
        elif index.column() not in self.checkable_col:
            return super().data(index, role)
        return None

    def setData(self, index: QModelIndex, value: Any, role=Qt.EditRole) -> bool:
        """Sets the model data for a given index using the defined role.

        Parameters
        ----------
        index : QModelIndex
            The model's index for the data being set.
        value : Any
            The new value for the model to store.
        role : Qt.ItemDataRole, optional
            The role used by the view to indicate if the model is being editted,
            by default Qt.EditRole
        """
        if not index.isValid():
            return QVariant()
        # Specifically the Hidden column must be affected in axis_model as opposed to elsewhere
        elif role == Qt.CheckStateRole and self._column_names[index.column()] == "Hidden":
            axis = self.plot._axes[index.row()]
            self.setHidden(axis, bool(value))
            return True
        elif role == Qt.CheckStateRole and index.column() in self.checkable_col:
            return super().setData(index, value, Qt.EditRole)
        elif index.column() not in self.checkable_col:
            return super().setData(index, value, role)
        return None

    def append(self, name: str = "") -> None:
        """Add an empty row to the end of the table model.

        Parameters
        ----------
        name : str
            The name for the new axis item. If none is passed in, the
            axis is named "Axis <row_count>".
        """
        self.axis_count += 1
        if not name:
            name = f"Axis {self.axis_count}"
        super().append(name)
        new_axis = self.get_axis(-1)
        new_axis.setLabel(name, color="black")
        row = self.rowCount() - 1
        self.attach_range_changed(row, new_axis)

    def removeAtIndex(self, index: QModelIndex) -> None:
        """Removes the axis at the given table index.

        Parameters
        ----------
        index : QModelIndex
            An index in the row to be removed.
        """
        # if self.rowCount() <= 1:
        #     self.append()
        axis = self.get_axis(index.row())
        if hasattr(axis, "_curves"):
            for i in range(len(axis._curves)):
                curve = axis._curves[0]
                self.remove_curve.emit(curve)
        super().removeAtIndex(index)

    def setHidden(self, axis: BasePlotAxisItem, hidden: bool) -> None:
        """Hides the axis at the given table index.

        Parameters
        ----------
        index : QModelIndex
            An index in the row to be hidde.
        """
        # Hide all curves
        if hasattr(axis, "_curves"):
            for curve in axis._curves:
                if hidden:
                    curve.hidden = True
                    curve.hide()
                else:
                    curve.hidden = False
                    curve.show()
        # Hide the axis
        axis.setHidden(shouldHide=hidden)

    def get_axis(self, index: int) -> BasePlotAxisItem:
        """Return the BasePlotAxisItem for a given row number.

        Parameters
        ----------
        index : int
            The row number of the axis item.
        """
        try:
            return self.plot._axes[index]
        except IndexError:
            return None

    def attach_range_changed(self, row: int, axis: BasePlotAxisItem) -> None:
        """Attach an axis' sigYRangeChanged signal to the model's dataChanged
        signal. This will notify the model to update to reflect new data.

        Parameters
        ----------
        row : int
            The row number of the axis. (0 based)
        axis : BasePlotAxisItem
            The axis item to be connected to the dataChanged signal.
        """
        min_col = self.getColumnIndex("Min Y Range")
        min_index = QPersistentModelIndex(self.index(row, min_col))

        max_col = self.getColumnIndex("Max Y Range")
        max_index = QPersistentModelIndex(self.index(row, max_col))

        axis.sigYRangeChanged.connect(
            lambda *_: self.dataChanged.emit(
                QModelIndex(min_index), QModelIndex(max_index)
            )
        )
