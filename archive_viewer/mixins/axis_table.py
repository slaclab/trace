from qtpy.QtCore import Slot
from qtpy.QtWidgets import QHeaderView
from table_models import ArchiverAxisModel
from widgets import ComboBoxDelegate, ScientificNotationDelegate


class AxisTableMixin:
    """Mixins class for the Axes tab of the settings section."""
    def axis_table_init(self) -> None:
        """Initializer for the Axis Table Model and Table View."""
        self.axis_table_model = ArchiverAxisModel(self.ui.archiver_plot, self)

        self.ui.time_axis_tbl.setModel(self.axis_table_model)

        hdr = self.ui.time_axis_tbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)

        self.ui.add_axis_row_btn.clicked.connect(self.addAxis)
        self.ui.del_axis_row_btn.clicked.connect(self.removeSelectedAxis)

    def axis_delegates_init(self) -> None:
        orientation_col = self.axis_table_model.getColumnIndex("Y-Axis Orientation")
        orientation_map = {"Left": "left", "Right": "right"}
        orientation_del = ComboBoxDelegate(self.ui.time_axis_tbl, orientation_map)
        self.ui.time_axis_tbl.setItemDelegateForColumn(orientation_col, orientation_del)

        min_range_col = self.axis_table_model.getColumnIndex("Min Y Range")
        min_range_del = ScientificNotationDelegate(self.ui.time_axis_tbl)
        self.ui.time_axis_tbl.setItemDelegateForColumn(min_range_col, min_range_del)

        max_range_col = self.axis_table_model.getColumnIndex("Max Y Range")
        max_range_del = ScientificNotationDelegate(self.ui.time_axis_tbl)
        self.ui.time_axis_tbl.setItemDelegateForColumn(max_range_col, max_range_del)

    @Slot()
    def addAxis(self) -> None:
        self.axis_table_model.append()

    @Slot()
    def removeSelectedAxis(self) -> None:
        self.axis_table_model.removeAtIndex(self.ui.time_axis_tbl.currentIndex())
