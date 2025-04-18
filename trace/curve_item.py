import qtawesome as qta
from qtpy import QtCore, QtWidgets


class CurveItem(QtWidgets.QWidget):
    def __init__(self, plot_curve_item):
        super().__init__()
        self.source = plot_curve_item
        self.setLayout(QtWidgets.QHBoxLayout())

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

        self.label = QtWidgets.QLabel(self.source.name())
        pv_settings_layout.addWidget(self.label)
        self.pv_settings_button = QtWidgets.QPushButton()
        self.pv_settings_button.setIcon(qta.icon("msc.settings-gear"))
        self.pv_settings_button.setFlat(True)
        pv_settings_layout.addWidget(self.pv_settings_button)
        self.delete_button = QtWidgets.QPushButton()
        self.delete_button.setIcon(qta.icon("msc.trash"))
        self.delete_button.setFlat(True)
        self.delete_button.clicked.connect(self.close)
        pv_settings_layout.addWidget(self.delete_button)

        self.live_toggle = QtWidgets.QCheckBox("Live")
        data_type_layout.addWidget(self.live_toggle)
        self.archive_toggle = QtWidgets.QCheckBox("Archive")
        data_type_layout.addWidget(self.archive_toggle)

    def set_active(self, state: QtCore.Qt.CheckState):
        if state == QtCore.Qt.Unchecked:
            self.source.hide()
        else:
            self.source.show()

    def close(self) -> bool:
        self.parent().parent().plot.removeCurve(self.source)
        self.setParent(None)
        self.deleteLater()
        return super().close()
