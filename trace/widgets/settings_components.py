from qtpy.QtGui import QFont
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QLabel,
    QWidget,
    QComboBox,
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
)


class SettingsTitle(QLabel):
    def __init__(self, parent: QWidget, text: str, size: int = None):
        super().__init__(text=text, parent=parent)
        bold_font = QFont()
        bold_font.setBold(True)
        if size is not None:
            bold_font.setPixelSize(size)
        self.setFont(bold_font)


class SettingsRowItem(QHBoxLayout):
    def __init__(self, parent: QWidget, label_txt: str, widget: QWidget):
        super().__init__(parent)
        label = QLabel(label_txt, self)
        self.addWidget(label)

        spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.addSpacerItem(spacer)

        self.addWidget(widget)


class ComboBoxWrapper(QComboBox):
    text_changed = Signal(object)

    def __init__(self, parent: QWidget, data_source: list | tuple | dict, init_value: int | str = None):
        super().__init__(parent)
        if isinstance(data_source, list, tuple):
            data_source = {v: v for v in data_source}
        self.data_source = data_source
        self.addItems(self.data_source.keys())

        if init_value is not None:
            if str(init_value) in self.data_source:
                self.setCurrentText(str(init_value))
            else:
                value_ind = list(self.data_source.values()).index(init_value)
                self.setCurrentIndex(value_ind)

        self.currentTextChanged.connect(self.clean_text_changed)

    def clean_text_changed(self, inc_text: str):
        outgoing_text = inc_text
        if inc_text in self.data_source:
            outgoing_text = self.data_source[inc_text]

        self.text_changed.emit(outgoing_text)
