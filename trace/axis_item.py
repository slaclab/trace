import qtawesome as qta
from qtpy import QtCore, QtWidgets
from curve_item import CurveItem

from widgets.table_widgets import ColorButton


class AxisItem(QtWidgets.QWidget):
    def __init__(self, plot_axis_item):
        super().__init__()
        self.source = plot_axis_item
        self.setLayout(QtWidgets.QVBoxLayout())

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
        self.axis_label = QtWidgets.QLabel(self.source.name)
        self.top_settings_layout.addWidget(self.axis_label)
        self.settings_button = QtWidgets.QPushButton()
        self.settings_button.setIcon(qta.icon("msc.settings-gear"))
        self.settings_button.setFlat(True)
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
        self.bottom_settings_layout.addWidget(self.min_range_line_edit)
        self.bottom_settings_layout.addWidget(QtWidgets.QLabel(","))
        self.max_range_line_edit = QtWidgets.QLineEdit()
        self.max_range_line_edit.editingFinished.connect(self.set_max_range)
        self.max_range_line_edit.editingFinished.connect(self.disable_auto_range)
        self.bottom_settings_layout.addWidget(self.max_range_line_edit)
        self.source.sigYRangeChanged.connect(self.handle_range_change)

        self.active_toggle = QtWidgets.QCheckBox("Active")
        self.active_toggle.setCheckState(QtCore.Qt.Checked if self.source.isVisible() else QtCore.Qt.Unchecked)
        self.active_toggle.stateChanged.connect(self.set_active)
        self.header_layout.addWidget(self.active_toggle)

    def add_curve(self, pv):
        index = len(self.parent().plot._curves)
        color = ColorButton.index_color(index)
        self.parent().plot.addYChannel(
            y_channel=pv,
            name=pv,
            color=color,
            useArchiveData=True,
            yAxisName=self.source.name,
        )

        plot_curve_item = self.parent().plot._curves[-1]
        curve_item = CurveItem(plot_curve_item)
        self.layout().addWidget(curve_item)
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

    def close(self) -> bool:
        self.source.sigYRangeChanged.disconnect(self.handle_range_change)
        self.source.linkedView().sigRangeChangedManually.disconnect(self.disable_auto_range)
        for i in range(1, self.layout().count()):
            self.layout().itemAt(i).widget().close()
        index = self.parent().plot._axes.index(self.source)
        self.parent().plot.removeAxisAtIndex(index)
        self.setParent(None)
        self.deleteLater()
        return super().close()
