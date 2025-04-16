import qtawesome as qta
from qtpy import QtWidgets
from curve_item import CurveItem


class AxisItem(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QtWidgets.QVBoxLayout())

        self.header_layout = QtWidgets.QHBoxLayout()
        self.layout().addLayout(self.header_layout)

        self.expand_button = QtWidgets.QPushButton()
        self.header_layout.addWidget(self.expand_button)

        layout = QtWidgets.QVBoxLayout()
        self.header_layout.addLayout(layout)
        self.top_settings_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(self.top_settings_layout)
        self.axis_label = QtWidgets.QLabel()
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
        self.autorange_checkbox = QtWidgets.QCheckBox("Auto")
        self.bottom_settings_layout.addWidget(self.autorange_checkbox)
        self.bottom_settings_layout.addWidget(QtWidgets.QLabel("min, max"))
        self.min_range_line_edit = QtWidgets.QLineEdit()
        self.bottom_settings_layout.addWidget(self.min_range_line_edit)
        self.bottom_settings_layout.addWidget(QtWidgets.QLabel(","))
        self.max_range_line_edit = QtWidgets.QLineEdit()
        self.bottom_settings_layout.addWidget(self.max_range_line_edit)

        self.active_toggle = QtWidgets.QCheckBox("Active")
        self.header_layout.addWidget(self.active_toggle)

    def add_curve(self, curve):
        curve_item = CurveItem()
        self.layout().addWidget(curve_item)

    def close(self) -> bool:
        for i in range(1, self.layout().count()):
            self.layout().itemAt(i).widget().close()
        self.setParent(None)
        self.deleteLater()
        return super().close()
