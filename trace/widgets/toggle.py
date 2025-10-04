from typing import Any, Optional

from qtpy.QtGui import QColor, QPainter
from qtpy.QtCore import Qt, QRect, Property, QPropertyAnimation
from qtpy.QtWidgets import QCheckBox


class ToggleSwitch(QCheckBox):
    """A custom toggle switch widget that looks like a modern mobile switch.
    This widget extends QCheckBox to create a toggle switch with animated
    transition between on and off states. The switch consists of a rounded
    rectangle track and a circular knob that moves horizontally.

    Attributes
    ----------
    TRACK_OFF : QColor
        Color of the track when the switch is off.
    TRACK_ON : QColor
        Color of the track when the switch is on.
    DIAMETER : int
        Diameter of the circular knob in pixels.
    MARGIN : int
        Margin between the knob and the track edge in pixels.
    """

    TRACK_OFF = QColor("#454545")
    TRACK_ON = QColor("#3a76d8")
    DIAMETER = 22
    MARGIN = 2

    def __init__(self, text: str = "", parent: Optional[Any] = None, color: Optional[QColor] = None) -> None:
        """Initialize the toggle switch widget.

        Parameters
        ----------
        text : str, optional
            The text label (for compatibility with QCheckBox, but not displayed)
        parent : QWidget, optional
            The parent widget.
        color : QColor, optional
            Custom color for the "on" state. If None, uses default blue.
        """
        if isinstance(text, (type(None), object)) and not isinstance(text, str):
            parent = text
            text = ""
        super().__init__(parent)
        self.setFixedSize(46, 26)
        self.setCursor(Qt.PointingHandCursor)
        self._x = self.MARGIN
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(120)

        self._track_on_color = color if color is not None else self.TRACK_ON

    def getOffset(self) -> int:
        """Get the current horizontal offset of the knob.

        Returns
        -------
        int
            The current x-coordinate of the knob.
        """
        return self._x

    def setOffset(self, x: int) -> None:
        """Set the horizontal offset of the knob and update the widget.

        Parameters
        ----------
        x : int
            The new x-coordinate for the knob.
        """
        self._x = x
        self.update()

    offset = Property(int, fget=getOffset, fset=setOffset)

    def nextCheckState(self) -> None:
        """Handle the toggle state change and animate the knob movement.
        This method is called when the checkbox state changes and
        manages the animation of the knob from one position to another.
        """
        super().nextCheckState()
        start = self._x
        end = self.width() - self.DIAMETER - self.MARGIN if self.isChecked() else self.MARGIN

        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()

    def setChecked(self, checked: bool) -> None:
        """Override setChecked to handle programmatic state changes with animation."""
        if self.isChecked() != checked:
            super().setChecked(checked)
            start = self._x
            end = self.width() - self.DIAMETER - self.MARGIN if checked else self.MARGIN
            self._anim.stop()
            self._anim.setStartValue(start)
            self._anim.setEndValue(end)
            self._anim.start()

    def setCheckState(self, state) -> None:
        """Override setCheckState to handle Qt.CheckState enums properly in PySide6."""
        if isinstance(state, int):
            checked = state != 0
        else:
            checked = state != Qt.Unchecked

        self.setChecked(checked)

    def setColor(self, color: QColor) -> None:
        """Set the color for the "on" state of the toggle switch.

        Parameters
        ----------
        color : QColor
            The color to use when the toggle is in the "on" state
        """
        self._track_on_color = color
        self.update()

    def getColor(self) -> QColor:
        """Get the current "on" state color.

        Returns
        -------
        QColor
            The current color used for the "on" state
        """
        return self._track_on_color

    def paintEvent(self, _: Any) -> None:
        """Paint the toggle switch with the appropriate colors and position.

        Parameters
        ----------
        _ : QPaintEvent
            The paint event (unused).
        """
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        track_col = self._track_on_color if self.isChecked() else self.TRACK_OFF
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(track_col))
        p.drawRoundedRect(self.rect(), self.height() / 2, self.height() / 2)

        # Draw the knob
        knob_rect = QRect(self._x, self.MARGIN, self.DIAMETER, self.DIAMETER)
        p.setBrush(Qt.white)
        p.drawEllipse(knob_rect)

    def hitButton(self, pos: Any) -> bool:
        """Determine if the given position is on the button. This is
        overridden to make the entire widget clickable, not just the
        standard checkbox indicator area.

        Parameters
        ----------
        pos : QPoint
            The position to test.

        Returns
        -------
        bool
            True if the position is within the widget's area, False otherwise.
        """
        return self.contentsRect().contains(pos)
