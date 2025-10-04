from random import random
from typing import Any

from qtpy.QtGui import QColor, QMouseEvent
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import QPushButton, QColorDialog

from config import color_palette


class ColorButton(QPushButton):
    """Custom button to allow the user to select a color. The default
    color is a random bright color.

    Left-clicking opens a color dialog box to choose a color.
    Right-clicking resets the color to the default.

    Parameters
    ----------
    color : QColor or str, optional
        Default color for the button to use, by default None
    index : int, optional
        A value used in determining a default color, by default -1
    """

    color_changed = Signal(QColor)

    def __init__(self, *args: Any, color: QColor | str = None, index: int = -1, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if not color:
            if index >= 0:
                color = self.index_color(index)
            else:
                color = self.random_color()
        elif not isinstance(color, QColor):
            color = QColor(color)

        self._color = None
        self._default = color
        self.dialog_box = QColorDialog(self)
        self.dialog_box.setCurrentColor(color)

        self.pressed.connect(self.dialog_box.show)
        self.dialog_box.colorSelected.connect(lambda c: setattr(self, "color", c))

        self.color = self._default

    @property
    def color(self) -> QColor:
        """The current color as a QColor."""
        return self._color

    @color.setter
    def color(self, color: QColor) -> None:
        """Set the background color of the button to the selected color.

        Parameters
        ----------
        color : QColor
            The color to set the button to
        """
        if color == self._color:
            return

        self._color = color
        style_str = "ColorButton {background-color: " + self._color.name() + "};"
        self.setStyleSheet(style_str)

        self.color_changed.emit(color)

    def mousePressEvent(self, e: QMouseEvent) -> None:
        """Set the color to the default on right-click."""
        if e.button() == Qt.RightButton:
            self.color = self._default
            return

        return super().mousePressEvent(e)

    @staticmethod
    def random_color() -> QColor:
        """Pick a random color for the default color of each PV. This
        function ensures that the color is bright.

        Returns
        -------
        QColor
            A random color that is guaranteed to be "bright"
        """
        hue = int(360 * random())
        saturation = int(256 * (0.5 + random() / 2.0))
        lightness = int(256 * (0.4 + random() / 5.0))
        color = QColor()
        color.setHsl(hue, saturation, lightness)
        return color

    @staticmethod
    def index_color(index: int, palette: str = "default") -> QColor:
        """Returns the color in the color palette at index. If the
        requested index is larger than the size of the color palette, then
        the palette is cycled through again, but darker by a factor of 35%.
        If palette str is not a key in color_palette dict from trace/config, 
        it will be replaced with 'default'

        Parameters
        ----------
        index : int
            Requested index of color palette
        palette : str
            Name of selected palette
        """
        if palette not in color_palette:
            palette = "default"
        modded_index = index % len(color_palette[palette])
        color = color_palette[palette][modded_index]

        dark_factor = (index // len(color_palette[palette])) * 35
        return color.darker(100 + dark_factor)
