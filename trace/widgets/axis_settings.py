from qtpy.QtGui import QFont
from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import (
    QLabel,
    QWidget,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from pydm.widgets import PyDMArchiverTimePlot
from pydm.widgets.baseplot import BasePlotAxisItem


class AxisSettingsModal(QWidget):
    def __init__(self, parent: QWidget, plot: PyDMArchiverTimePlot, axis: BasePlotAxisItem):
        super().__init__(parent)
        self.setWindowFlag(Qt.Popup)

        self.plot = plot
        self.axis = axis
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        bold_font = QFont()
        bold_font.setBold(True)
        bold_font.setPixelSize(14)
        title_label = QLabel("Axis Settings", self)
        title_label.setFont(bold_font)
        main_layout.addWidget(title_label)

        orientation_layout = QHBoxLayout()
        orientation_label = QLabel("Orientation", self)
        orientation_layout.addWidget(orientation_label)
        orientation_spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        orientation_layout.addSpacerItem(orientation_spacer)
        orientation_combo = QComboBox(self)
        orientation_combo.addItems(["Left", "Right"])
        orientation_combo.currentTextChanged.connect(self.set_axis_orientation)
        orientation_combo.setCurrentText("Right" if self.axis.orientation == "right" else "Left")
        orientation_layout.addWidget(orientation_combo)
        main_layout.addLayout(orientation_layout)

        log_layout = QHBoxLayout()
        log_label = QLabel("Log Mode", self)
        log_layout.addWidget(log_label)
        log_spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        log_layout.addSpacerItem(log_spacer)
        log_checkbox = QCheckBox(self)
        log_checkbox.setChecked(self.axis.log_mode)
        log_checkbox.stateChanged.connect(self.set_axis_log_mode)
        log_layout.addWidget(log_checkbox)
        main_layout.addLayout(log_layout)

    def show(self):
        parent_pos = self.parent().rect().bottomRight()
        global_pos = self.parent().mapToGlobal(parent_pos)
        self.move(global_pos)
        super().show()

    @Slot(str)
    def set_axis_orientation(self, orientation: str):
        if orientation not in ["Left", "Right"]:
            return
        self.axis.orientation = orientation.lower()
        self.plot.plotItem.rebuildLayout()
        if self.axis.isVisible():
            self.axis.show()

    @Slot(bool)
    def set_axis_log_mode(self, checked: bool):
        self.axis.log_mode = checked
