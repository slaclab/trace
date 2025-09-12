from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QLabel,
    QWidget,
    QComboBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
)

from config import color_palette
from widgets import SettingsTitle, SettingsRowItem


class CurveColorPaletteModal(QWidget):
    sig_palette_changed = Signal(str, bool)

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowFlag(Qt.Popup)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        title_label = SettingsTitle(self, "Select Curve Color Palette", size=14)
        main_layout.addWidget(title_label)

        if self.is_axis:
            subtitle_label = QLabel(
                "Click 'Apply to current' to apply palette to curves on this axis"
                + "\nNew curves will be colored according to global plot color palette"
            )
        else:
            subtitle_label = QLabel("Selected palette will apply to new curves added to the plot ")
        main_layout.addWidget(subtitle_label)

        # combobox for choosing palette
        self.palette_cbox = QComboBox()
        self.palette_cbox.addItems([key for key in color_palette.keys()])
        self.palette_cbox.activated.connect(self.set_palette)

        palette_row = SettingsRowItem(self, "  Select Palette: ", self.palette_cbox)
        main_layout.addLayout(palette_row)

        # widget for displaying preview of colors in palette
        color_preview = QWidget()
        self.color_preview_layout = QHBoxLayout(color_preview)
        self.color_preview_layout.setContentsMargins(0, 0, 0, 0)
        self.color_preview_layout.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(color_preview)

        # button to apply palette to existing curves
        apply_button = QPushButton("Apply to current")
        apply_button.clicked.connect(self.apply_palette)
        apply_button.setFixedWidth(128)
        apply_button.setToolTip("Click to apply selected color palette to existing curves")
        main_layout.addWidget(apply_button)

        self.set_palette()

    def set_palette(self):
        """Set default palette to option currently selected in combobox"""
        palette = self.palette_cbox.currentText()
        self.clear_layout(self.color_preview_layout)
        # Display preview of colors
        for color in color_palette[palette]:
            button = QPushButton()
            button.setStyleSheet(f"background-color: {color.name()}; border-radius: 4px;")
            button.setFixedWidth(30)
            self.color_preview_layout.addWidget(button)
        # Emit signal with selected palette
        self.sig_palette_changed.emit(palette, False)

    def apply_palette(self):
        """Apply palette to existing curves"""
        palette = self.palette_cbox.currentText()
        self.sig_palette_changed.emit(palette, True)

    def clear_layout(self, layout):
        """Remove widgets from QLayout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()  # Schedule deletion of the widget

    @property
    def is_axis(self):
        """Check whether this instance of modal's parent is an axisItem"""
        return hasattr(self.parent(), "axis")

    def show(self):
        if self.is_axis:
            parent_pos = self.parent().rect().bottomLeft()
        else:
            parent_pos = self.parent().rect().topRight()
        global_pos = self.parent().mapToGlobal(parent_pos)
        self.move(global_pos)
        super().show()
