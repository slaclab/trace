from qtpy.QtCore import Qt, QRect, QPropertyAnimation, Property
from qtpy.QtGui import QColor, QPainter
from qtpy.QtWidgets import QCheckBox
from typing import Optional, Any


class ToggleSwitch(QCheckBox):
    """
    A custom toggle switch widget that looks like a modern mobile switch.
    
    This widget extends QCheckBox to create a toggle switch with animated
    transition between on and off states. The switch consists of a rounded
    rectangle track and a circular knob that moves horizontally.
    
    Parameters
    ----------
    parent : QWidget, optional
        The parent widget.
        
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
    
    def __init__(self, parent: Optional[Any] = None) -> None:
        """
        Initialize the toggle switch widget.
        
        Parameters
        ----------
        parent : QWidget, optional
            The parent widget.
        """
        super().__init__(parent)
        self.setFixedSize(46, 26)
        self.setCursor(Qt.PointingHandCursor)
        self._x = self.MARGIN  # Start with knob on the left (off position)
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(120)
    
    def getOffset(self) -> int:
        """
        Get the current horizontal offset of the knob.
        
        Returns
        -------
        int
            The current x-coordinate of the knob.
        """
        return self._x
    
    def setOffset(self, x: int) -> None:
        """
        Set the horizontal offset of the knob and update the widget.
        
        Parameters
        ----------
        x : int
            The new x-coordinate for the knob.
        """
        self._x = x
        self.update()
    
    offset = Property(int, fget=getOffset, fset=setOffset)
    
    def nextCheckState(self) -> None:
        """
        Handle the toggle state change and animate the knob movement.
        
        This method is called when the checkbox state changes and
        manages the animation of the knob from one position to another.
        """
        super().nextCheckState()
        start = self._x
        end = (self.width() - self.DIAMETER - self.MARGIN if self.isChecked()
              else self.MARGIN)
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()
    
    def paintEvent(self, _: Any) -> None:
        """
        Paint the toggle switch with the appropriate colors and position.
        
        Parameters
        ----------
        _ : QPaintEvent
            The paint event (unused).
        """
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        # Draw the track
        track_col = self.TRACK_ON if self.isChecked() else self.TRACK_OFF
        p.setPen(Qt.NoPen)
        p.setBrush(track_col)
        p.drawRoundedRect(self.rect(), self.height()/2, self.height()/2)
        
        # Draw the knob
        knob_rect = QRect(self._x, self.MARGIN,
                         self.DIAMETER, self.DIAMETER)
        p.setBrush(Qt.white)
        p.drawEllipse(knob_rect)
    
    def hitButton(self, pos: Any) -> bool:
        """
        Determine if the given position is on the button.
        
        This is overridden to make the entire widget clickable, not just
        the standard checkbox indicator area.
        
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

