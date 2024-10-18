from qtpy.QtCore import QRect
from qtpy.QtWidgets import QStyle, QWidget, QProxyStyle, QStyleOption


class CenterCheckStyle(QProxyStyle):
    def subElementRect(self, element: QStyle.SubElement, option: QStyleOption, widget: QWidget) -> QRect:
        """QProxyStyle used for centering all checkboxes contained in tables."""
        if element == self.SE_ItemViewItemCheckIndicator and not option.text:
            rect = super().subElementRect(element, option, widget)
            rect.moveCenter(option.rect.center())
            return rect
        return super().subElementRect(element, option, widget)
