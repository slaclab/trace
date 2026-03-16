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
    """A QLabel with bold formatting for use as section titles in settings dialogs.

    This widget provides a consistent title appearance across all settings
    dialogs with optional custom font size.
    """

    def __init__(self, parent: QWidget, text: str, size: int = None):
        """Initialize the settings title.

        Parameters
        ----------
        parent : QWidget
            The parent widget
        text : str
            The title text to display
        size : int, optional
            Custom font size in points
        """
        super().__init__(text=text, parent=parent)
        bold_font = QFont()
        bold_font.setBold(True)
        if size is not None:
            bold_font.setPointSize(size)
        self.setFont(bold_font)


class SettingsRowItem(QHBoxLayout):
    """A horizontal layout for settings rows with label and widget.

    This layout provides a consistent structure for settings rows with
    a label on the left, a spacer in the middle, and a widget on the right.
    """

    def __init__(self, label_parent: QWidget, label_txt: str, widget: QWidget):
        """Initialize the settings row item.

        Parameters
        ----------
        label_parent : QWidget
            The parent widget for the label
        label_txt : str
            The text for the label
        widget : QWidget
            The widget to place on the right side
        """
        super().__init__()
        label = QLabel(label_txt, label_parent)
        self.addWidget(label)

        spacer = QSpacerItem(40, 12, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.addSpacerItem(spacer)

        self.addWidget(widget)


class ComboBoxWrapper(QComboBox):
    """A QComboBox wrapper that provides data mapping and custom signal emission.

    This widget extends QComboBox to support data source mapping and emits
    the mapped value rather than the display text when selection changes.
    """

    text_changed = Signal(object)

    def __init__(self, parent: QWidget, data_source: list | tuple | dict, init_value: int | str | None = None):
        """Initialize the combo box wrapper.

        Parameters
        ----------
        parent : QWidget
            The parent widget
        data_source : list, tuple, or dict
            Data source for the combo box items. If list/tuple, creates a
            mapping to itself. If dict, uses keys as display text and values
            as emitted values.
        init_value : int, str, or None, optional
            Initial value to select
        """
        super().__init__(parent)
        if isinstance(data_source, (list, tuple)):
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

    def clean_text_changed(self, inc_text: str) -> None:
        """Handle text changes and emit the mapped value.

        Parameters
        ----------
        inc_text : str
            The incoming text from the combo box
        """
        outgoing_text = inc_text
        if inc_text in self.data_source:
            outgoing_text = self.data_source[inc_text]

        self.text_changed.emit(outgoing_text)
