from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QStyle, QStyleOption, QWidget
from qtpy.QtWidgets import QProxyStyle


class CenterCheckStyle(QProxyStyle):
    def subElementRect(self, element: QStyle.SubElement, option: QStyleOption, widget: QWidget) -> QRect:
        """QProxyStyle used for centering all checkboxes contained in tables."""
        if element == self.SE_ItemViewItemCheckIndicator and not option.text:
            rect = super().subElementRect(element, option, widget)
            rect.moveCenter(option.rect.center())
            return rect
        return super().subElementRect(element, option, widget)
