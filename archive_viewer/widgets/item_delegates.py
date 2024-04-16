from typing import (Union, Tuple)
from qtpy.QtGui import QColor, QPainter
from qtpy.QtCore import (Qt, QObject, QEvent, QPoint, Slot, Signal,
                         QAbstractTableModel, QModelIndex, QAbstractItemModel)
from qtpy.QtWidgets import (QStyledItemDelegate, QSlider, QComboBox, QStyle,
                            QPushButton, QTableView, QStyleOptionViewItem,
                            QWidget, QDoubleSpinBox)
from config import logger
from widgets import (ColorButton, CenterCheckbox)


class SliderDelegate(QStyledItemDelegate):
    """SliderDelegate is a QStyledItemDelegate to display a persistent
    QSlider widget on a QTableView.

    Parameters
    ----------
    parent : QTableView
        The parent object for the SliderDelegate. Should be the
        associated QTableView
    init_range : Tuple[int, int], optional
        The range for the QSlider widget, by default (1, 10)
    """
    def __init__(self, parent: QTableView, init_range: Tuple[int, int] = (1, 10)) -> None:
        super().__init__(parent)
        self.init_range = init_range
        self.editor_map = {}

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        if index not in self.editor_map:
            self.parent().openPersistentEditor(index)
        return super().paint(painter, option, index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QSlider:
        """Initialize a QSlider object for use in the Table View."""
        if index not in self.editor_map:
            value = index.data(Qt.DisplayRole)
            editor = QSlider(orientation=Qt.Horizontal)
            editor.setFocusPolicy(Qt.StrongFocus)
            editor.setRange(*self.init_range)
            editor.setTickPosition(QSlider.TicksBothSides)
            editor.setTickInterval(1)
            editor.setValue(value)
            editor.valueChanged.connect(lambda: self.commitData.emit(editor))

            self.editor_map[index] = editor
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: QSlider, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = index.data(Qt.DisplayRole)
        editor.setValue(value)

    def setModelData(self, editor: QSlider, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        data = editor.value()
        model.setData(index, data, Qt.EditRole)

    def eventFilter(self, object: QObject, event: QEvent):
        """Disable scrolling for widgets that are not the focus."""
        if event.type() == QEvent.Wheel and not object.hasFocus():
            return True
        return super().eventFilter(object, event)


class ComboBoxDelegate(QStyledItemDelegate):
    """ComboBoxDelegate is a QStyledItemDelegate to display a persistent
    QComboBox widget on a QTableView.

    Parameters
    ----------
    parent : QTableView
        The parent object for the ComboBoxDelegate. Should be the
        associated QTableView
    data_source : ArchiverAxisModel, list, dict
        The initial dataset to use when populating the QComboBox.
    """
    sigTextChange = Signal(int, str)

    def __init__(self, parent: QTableView, data_source: Union[QAbstractItemModel, list, dict]) -> None:
        super().__init__(parent)
        if isinstance(data_source, list):
            data_source = {v: v for v in data_source}
        self.data_source = data_source
        self.editor_map = {}

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Open a persistent QComboBox on the Table View at the index."""
        if index not in self.editor_map:
            self.parent().openPersistentEditor(index)
        return super().paint(painter, option, index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QComboBox:
        """Initialize a QComboBox for use in the Table View."""
        if index not in self.editor_map:
            editor = QComboBox()

            logger.debug(f"Setting input to {self.data_source}")
            if isinstance(self.data_source, dict):
                editor.addItems(self.data_source.keys())
                value = index.data(Qt.DisplayRole)
                if str(value) in self.data_source:
                    editor.setCurrentText(str(value))
                else:
                    value_ind = list(self.data_source.values()).index(value)
                    editor.setCurrentIndex(value_ind)
            elif isinstance(self.data_source, QAbstractItemModel):
                editor.setModel(self.data_source)
                editor.setModelColumn(0)

            editor.setFocusPolicy(Qt.StrongFocus)
            editor.setContextMenuPolicy(Qt.CustomContextMenu)
            editor.customContextMenuRequested.connect(self.combo_menu_requested)
            editor.currentIndexChanged.connect(lambda: self.commitData.emit(editor))

            self.editor_map[index] = editor
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: QComboBox, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = index.data(Qt.DisplayRole)
        if str(value) in self.data_source:
            editor.setCurrentText(str(value))
        else:
            value_ind = list(self.data_source.values()).index(value)
            editor.setCurrentIndex(value_ind)

    def setModelData(self, editor: QComboBox, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        curr_text = editor.currentText()
        if isinstance(self.data_source, dict):
            data = self.data_source[curr_text]
        elif isinstance(self.data_source, QAbstractItemModel):
            self.sigTextChange.emit(index.row(), curr_text)
            data = curr_text
        model.setData(index, data, Qt.EditRole)

    def eventFilter(self, object: QObject, event: QEvent) -> bool:
        """Disable scrolling for widgets that are not the focus."""
        if event.type() == QEvent.Wheel and not object.hasFocus():
            return True
        return super().eventFilter(object, event)

    @Slot(QPoint)
    def combo_menu_requested(self, pos: QPoint) -> None:
        """Redirect menu requests to the Table View."""
        pos = self.sender().mapToParent(pos)
        self.parent().customContextMenuRequested.emit(pos)


class CheckboxDelegate(QStyledItemDelegate):
    """CheckboxDelegate is a QStyledItemDelegate to display a persistent
    QCheckbox widget on a QTableView.

    Parameters
    ----------
    parent : QTableView
        The parent object for the CheckboxDelegate. Should be the
        associated QTableView
    """
    def __init__(self, parent: QTableView) -> None:
        super().__init__(parent)
        self.editor_map = {}

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        if index not in self.editor_map:
            self.parent().openPersistentEditor(index)
        return super().paint(painter, option, index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        """Initialize a QCheckbox for use in the Table View."""
        if index not in self.editor_map:
            value = index.data(Qt.DisplayRole)
            editor = CenterCheckbox(parent, bool(value))
            editor.toggled.connect(lambda: self.commitData.emit(editor))

            self.editor_map[index] = editor
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: CenterCheckbox, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = index.data(Qt.DisplayRole)
        editor.checkState = bool(value)

    def setModelData(self, editor: CenterCheckbox, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        data = editor.checkState
        model.setData(index, data, Qt.EditRole)


class ColorButtonDelegate(QStyledItemDelegate):
    """ColorButtonDelegate is a QStyledItemDelegate to display a persistent
    QPushButton widget on a QTableView that allow's the user to change an object's color.

    Parameters
    ----------
    parent : QTableView
        The parent object for the ColorButtonDelegate. Should be the
        associated QTableView
    """
    def __init__(self, parent: QTableView) -> None:
        super().__init__(parent)
        self.editor_map = {}

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        if index not in self.editor_map:
            self.parent().openPersistentEditor(index)
        return super().paint(painter, option, index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> ColorButton:
        """Initialize a ColorButton for use in the Table View."""
        if index not in self.editor_map:
            value = index.data(Qt.DisplayRole)
            editor = ColorButton(parent, color=value)
            editor.color_changed.connect(lambda: self.commitData.emit(editor))

            self.editor_map[index] = editor
            return editor

        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: ColorButton, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = index.data(Qt.DisplayRole)
        logger.debug("Setting ColorButton data in delegate to: " + value)
        editor.color = QColor(value)

    def setModelData(self, editor: ColorButton, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        data = editor.color.name()
        model.setData(index, data, Qt.EditRole)


class DeleteRowDelegate(QStyledItemDelegate):
    """DeleteRowDelegate is a QStyledItemDelegate to display a persistent
    QPushButton widget on a QTableView that allow's the user to delete the row.

    Parameters
    ----------
    parent : QTableView
        The parent object for the DeleteRowDelegate. Should be the
        associated QTableView
    """
    def __init__(self, parent: QTableView) -> None:
        super().__init__(parent)
        self.editor_map = {}

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        if index not in self.editor_map:
            self.parent().openPersistentEditor(index)
        return super().paint(painter, option, index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QPushButton:
        """Initialize a QPushButton to delete the table's row."""
        logger.debug("called method: DeleteRowDelegate.initStyleOption")
        if index not in self.editor_map:
            editor = QPushButton(self.parent())
            icon = editor.style().standardIcon(QStyle.SP_DialogCancelButton)
            editor.setIcon(icon)
            editor.setToolTip("Delete Trace")
            editor.clicked.connect(lambda: self.commitData.emit(editor))

            self.editor_map[index] = editor
            return editor

        return super().createEditor(parent, option, index)

    def setModelData(self, editor: ColorButton, model: QAbstractTableModel, index: QModelIndex) -> None:
        """When the setModelData slot is triggered, the row is removed."""
        model.removeAtIndex(index)

class FloatDelegate(QStyledItemDelegate):
    def __init__(self, parent: QTableView, init_range: Tuple[float, float] = (float("-inf"), float("inf")), prec: int = 2):
        super().__init__(parent)
        self.range = init_range
        self.prec = prec
        self.editor_map = {}

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Create a new persistent editor on the Table View at the given index."""
        if index not in self.editor_map:
            self.parent().openPersistentEditor(index)
        return super().paint(painter, option, index)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QDoubleSpinBox:
        """Initialize a QDoubleSpinBox to delete the table's row."""
        if index not in self.editor_map:
            value = index.data(Qt.DisplayRole)
            if value is None:
                value = self.range[0]

            editor = QDoubleSpinBox()
            editor.setMinimum(self.range[0])
            editor.setMaximum(self.range[1])
            editor.setDecimals(self.prec)
            editor.setValue(value)
            editor.editingFinished.connect(lambda: self.commitData.emit(editor))

            self.editor_map[index] = editor
            return editor

        return super().createEditor(parent, option, index)

    def setEditorData(self, editor: QDoubleSpinBox, index: QModelIndex) -> None:
        """Set the editor's data to match the table model's data."""
        value = index.data(Qt.DisplayRole)
        editor.setValue(value)

    def setModelData(self, editor: QDoubleSpinBox, model: QAbstractTableModel, index: QModelIndex) -> None:
        """Set the table model's data to match the editor's data."""
        data = editor.value()
        model.setData(index, data, Qt.EditRole)
