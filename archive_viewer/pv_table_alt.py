from qtpy.QtWidgets import QApplication, QTableView, QStyledItemDelegate, QItemDelegate, QComboBox, QCheckBox, QPushButton, QSlider, QVBoxLayout, QAbstractItemView, QStyle, QWidget
from qtpy.QtCore import QAbstractTableModel, Qt, QModelIndex, Signal, QPoint, QEvent
from qtpy.QtGui import QRegion, QColor

class SingleClickTableView(QTableView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_editor = None

    def mousePressEvent(self, event):
        if not self.rect().contains(event.pos()):
            # Click is outside the table, close any open editors
            #self.closePersistentEditor(self.currentIndex())
            self.close_active_editor()
        else:
            super().mousePressEvent(event)
            if event.button() == Qt.LeftButton:
                for row in range(self.model().rowCount()):
                    for column in range(self.model().columnCount()):
                        index = self.model().index(row, column)
                        if index.isValid():
                            self.close_active_editor()
                            self.open_active_editor(index)


    def open_active_editor(self, index):
        self.active_editor = self.openPersistentEditor(index)

    def close_active_editor(self):
        if self.active_editor:
            self.closePersistentEditor(self.active_editor)
            self.active_editor = None

class MyTableModel(QAbstractTableModel):
    """
    """
    dataChangedSignal = Signal()

    def __init__(self, data, headers):
        super().__init__()
        self._data = data
        self._headers = headers

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data[0])

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self._data[row][col]

    def setData(self, index, value, role=Qt.EditRole):
            if role == Qt.EditRole:
                self._data[index.row()][index.column()] = value
                self.dataChanged.emit(index, index)
                self.dataChangedSignal.emit()  # Emit the custom signal
                return True
            return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]

        return super().headerData(section, orientation, role)

    def flags(self, index):
            # Set the Qt.ItemIsEditable flag to make the cells editable
            return super().flags(index) | Qt.ItemIsEditable
    
class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, items):
        super().__init__()
        self.items = items

    def initStyleOption(self, option, index):
        btn = self.parent().indexWidget(index)
        if not btn:
            data = index.data(Qt.UserRole)
            btn = QComboBox()
            btn.setText(data[1])
            btn.showIcon = False
            btn.openInNewWindow = True
            self.parent().setIndexWidget(index, btn)

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.items)
        return editor

    def setEditorData(self, editor, index):
        editor.setCurrentText(index.data())

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText())

class CheckBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        super(CheckBoxDelegate, self).__init__(parent)

    def initStyleOption(self, option, index):
        btn = self.parent().indexWidget(index)
        if not btn:
            data = index.data(Qt.UserRole)
            #btn = PyDMRelatedDisplayButton(filename=data[0])
            #btn.setText(data[1])
            #btn.showIcon = False
            #btn.openInNewWindow = True
            self.parent().setIndexWidget(index, btn)

        return super().initStyleOption(option, index)

    def createEditor(self, parent, option, index):
        editor = QCheckBox(parent)
        return editor

    def setEditorData(self, editor, index):
        editor.setChecked(index.data())

    def setModelData(self, editor, model, index):
        model.setData(index, editor.isChecked())

    def drawDisplay(self, painter, option, rect, text):
        super().drawDisplay(painter, option, rect, "")

        
class ButtonDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QPushButton(parent)
        return editor

    def setEditorData(self, editor, index):
        editor.setText(index.data())
        
    def drawDisplay(self, painter, option, rect, text):
        super().drawDisplay(painter, option, rect, "")
    
class SliderDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QSlider(Qt.Horizontal, parent)
        editor.setRange(0, 100)
        return editor

    def setEditorData(self, editor, index):
        editor.setValue(index.data())

    def setModelData(self, editor, model, index):
        model.setData(index, editor.value())

    def drawDisplay(self, painter, option, rect, text):
        super().drawDisplay(painter, option, rect, "")
    
class ColorColumnDelegate(QItemDelegate):
    """The ColorColumnDelegate is an item delegate that is installed on the
    color column of the table view.  Its only job is to ensure that the default
    editor widget (a line edit) isn't displayed for items in the color column.
    """
    def createEditor(self, parent, option, index):
        return None
    
    def drawDisplay(self, painter, option, rect, text):
        super().drawDisplay(painter, option, rect, "")

class PyDMPVTable_alt(QWidget):
    """
    """
    def __init__(self, macros=None, table_headers=[], max_rows=1, number_columns=10, col_widths=[50]):
        super().__init__()
        
        data = ["name"]
        self.model = MyTableModel(data, table_headers)
        
        self.table_view = SingleClickTableView()
        self.table_view.setModel(self.model)
        self.table_view.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.table_view.setProperty("showDropIndicator", False)
        self.table_view.setDragDropOverwriteMode(False)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSortingEnabled(False)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setVisible(False)
        
        self.setup_delegate_columns()

        def table_data_changed():
            print("Table data changed!")

        self.model.dataChangedSignal.connect(table_data_changed)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.table_view)
        
        self.setLayout(main_layout)


    def setup_delegate_columns(self):
        self.combo_delegate = ComboBoxDelegate(['Option A', 'Option B', 'Option C'])
        self.table_view.setItemDelegateForColumn(1, self.combo_delegate)

        self.combo_delegate_2 = ComboBoxDelegate(['Option 1', 'Option 2', 'Option 3'])
        self.table_view.setItemDelegateForColumn(2, self.combo_delegate_2)
        
        self.combo_delegate_3 = CheckBoxDelegate(self.table_view)
        self.table_view.setItemDelegateForColumn(3, self.combo_delegate_3)
        
        self.table_view.setItemDelegateForColumn(4, ColorColumnDelegate(self.table_view))

        self.table_view.setItemDelegateForColumn(5, ButtonDelegate(self.table_view))

        self.combo_delegate_4 = ComboBoxDelegate(['Option 1', 'Option 2', 'Option 3'])
        self.table_view.setItemDelegateForColumn(6, self.combo_delegate_4)
        
        self.table_view.setItemDelegateForColumn(7, SliderDelegate(self.table_view))



    