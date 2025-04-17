import qtawesome as qta
from qtpy import QtWidgets


class CurveItem(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setLayout(QtWidgets.QHBoxLayout())

        self.active_toggle = QtWidgets.QCheckBox("Active")
        self.layout().addWidget(self.active_toggle)

        second_layout = QtWidgets.QVBoxLayout()
        self.layout().addLayout(second_layout)
        pv_settings_layout = QtWidgets.QHBoxLayout()
        second_layout.addLayout(pv_settings_layout)
        data_type_layout = QtWidgets.QHBoxLayout()
        second_layout.addLayout(data_type_layout)

        self.label = QtWidgets.QLabel()
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

    def close(self) -> bool:
        self.setParent(None)
        self.deleteLater()
        return super().close()
