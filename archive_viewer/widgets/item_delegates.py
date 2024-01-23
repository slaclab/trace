from PyQt5.QtCore import QObject
from qtpy.QtGui import QColor
from qtpy.QtCore import (Qt, QObject, QEvent, QPoint, Slot)
from qtpy.QtWidgets import (QStyledItemDelegate, QSlider, QComboBox, QCheckBox,
                            QStyle)
from widgets import (ColorButton, CenterCheckbox)


class PVTableDelegate(QStyledItemDelegate):
    def __init__(self, parent, column_widgets: dict):
        super().__init__(parent)
        self.widgets = list(column_widgets.values())

    def paint(self, painter, option, index):
        column_widget = self.widgets[index.column()]

        if column_widget is str and column_widget is None:
            return super().paint(painter, option, index)

        if option.state == QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        self.parent().openPersistentEditor(index)

    def createEditor(self, parent, option, index):
        column_widget = self.widgets[index.column()]
        data = index.data(Qt.UserRole)

        if column_widget is QSlider:
            editor = QSlider(parent, orientation=Qt.Horizontal)
            editor.setValue(data)
            editor.setFocusPolicy(Qt.StrongFocus)
            editor.valueChanged.connect(lambda: self.commitData.emit(editor))

        elif column_widget is QCheckBox:
            editor = CenterCheckbox(parent, data)
            editor.toggled.connect(lambda: self.commitData.emit(editor))

        elif column_widget is QComboBox:
            editor = QComboBox(parent)
            editor.setCurrentIndex(data)
            editor.addItem('A')
            editor.addItem('B')
            editor.setFocusPolicy(Qt.StrongFocus)
            editor.setContextMenuPolicy(Qt.CustomContextMenu)
            editor.customContextMenuRequested.connect(self.combo_menu_requested)
            editor.currentIndexChanged.connect(lambda: self.commitData.emit(editor))

        elif column_widget is ColorButton:
            editor = ColorButton(parent, color=data)
            editor.color_changed.connect(lambda: self.commitData.emit(editor))

        else:
            return super().createEditor(parent, option, index)

        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.UserRole)

        if isinstance(editor, QSlider):
            editor.setValue(value)
        elif isinstance(editor, CenterCheckbox):
            editor.checkState = value
        elif isinstance(editor, QComboBox):
            editor.setCurrentIndex(value)
        elif isinstance(editor, ColorButton):
            editor.color = QColor(value)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QSlider):
            data = editor.value()
        elif isinstance(editor, CenterCheckbox):
            data = editor.checkState
        elif isinstance(editor, QComboBox):
            data = editor.currentIndex()
        elif isinstance(editor, ColorButton):
            data = editor.color.name()
        else:
            super().setModelData(editor, model, index)
            return

        model.setData(index, data, Qt.EditRole)

    def eventFilter(self, object: QObject, event: QEvent):
        """Disable scrolling for widgets that are not the focus."""
        if event.type() == QEvent.Wheel and not object.hasFocus():
            return True
        return super().eventFilter(object, event)
    
    @Slot(QPoint)
    def combo_menu_requested(self, pos: QPoint):
        pos = self.sender().mapToParent(pos)
        self.parent().customContextMenuRequested.emit(pos)


class ArchiversTableDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super().__init__(parent)

    def paint(self, painter, option, index):
        if option.state == QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        self.parent().openPersistentEditor(index)

    def createEditor(self, parent, option, index):
        data = index.data(Qt.UserRole)
        editor = CenterCheckbox(parent, data)
        editor.toggled.connect(lambda: self.commitData.emit(editor))

        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.UserRole)
        editor.checkState = value

    def setModelData(self, editor, model, index):
        data = editor.checkState
        model.setData(index, data, Qt.EditRole)

