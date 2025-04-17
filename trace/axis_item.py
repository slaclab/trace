import qtawesome as qta
from qtpy import QtWidgets
from curve_item import CurveItem


class AxisItem(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
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

    def add_curve(self, pv):
        curve_item = CurveItem()
        curve_item.label.setText(pv)
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

    def close(self) -> bool:
        for i in range(1, self.layout().count()):
            self.layout().itemAt(i).widget().close()
        self.setParent(None)
        self.deleteLater()
        return super().close()
