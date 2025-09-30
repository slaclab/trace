from qtpy.QtCore import Qt, QModelIndex
from qtpy.QtWidgets import QTableView, QHeaderView, QAbstractItemView


class FrozenTableView(QTableView):
    """QTableView with the leftmost column frozen so it always shows while the
    rest of the table is horizontally scrollable.

    Python version of Qt FreezeTableWidget example:
    https://doc.qt.io/qt-6/qtwidgets-itemviews-frozencolumn-example.html
    """

    def __init__(self, model):
        """Initialize the frozen table view with the given model.

        Parameters
        ----------
        model : QAbstractTableModel
            The data model for the table
        """
        super(FrozenTableView, self).__init__()
        self.setModel(model)
        self.frozenTableView = QTableView(self)
        self.init()
        self.horizontalHeader().sectionResized.connect(self.updateSectionWidth)
        self.verticalHeader().hide()
        self.frozenTableView.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.verticalScrollBar().valueChanged.connect(self.frozenTableView.verticalScrollBar().setValue)

    def init(self) -> None:
        """Initialize the frozen table view layout and properties."""
        self.frozenTableView.setModel(self.model())
        self.frozenTableView.setFocusPolicy(Qt.NoFocus)
        self.frozenTableView.verticalHeader().hide()
        self.frozenTableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.viewport().stackUnder(self.frozenTableView)

        self.setAlternatingRowColors(True)
        self.frozenTableView.setAlternatingRowColors(True)
        self.frozenTableView.setStyleSheet("QTableView {border: none; border-right: 1px solid lightGray}")

        self.setSelectionBehavior(QTableView.SelectRows)
        self.frozenTableView.setSelectionBehavior(QTableView.SelectRows)
        self.frozenTableView.setSelectionModel(self.selectionModel())
        for col in range(1, self.model().columnCount()):
            self.frozenTableView.setColumnHidden(col, True)
        self.frozenTableView.setColumnWidth(0, self.columnWidth(0))
        self.frozenTableView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frozenTableView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frozenTableView.show()
        self.updateFrozenTableGeometry()
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.frozenTableView.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

    def updateSectionWidth(self, logicalIndex, oldSize, newSize) -> None:
        """Update the width of the frozen column when the main table column is resized.

        Parameters
        ----------
        logicalIndex : int
            The logical index of the column being resized
        oldSize : int
            The previous width of the column, unused
        newSize : int
            The new width of the column
        """
        if logicalIndex == 0:
            self.frozenTableView.setColumnWidth(0, newSize)
            self.updateFrozenTableGeometry()

    def updateSectionHeight(self, logicalIndex, oldSize, newSize) -> None:
        """Update the height of a row in the frozen table.

        Parameters
        ----------
        logicalIndex : int
            The logical index of the row being resized
        oldSize : int
            The previous height of the row, unused
        newSize : int
            The new height of the row
        """
        self.frozenTableView.setRowHeight(logicalIndex, newSize)

    def resizeEvent(self, event) -> None:
        """Handle resize events by updating the frozen table geometry."""
        super(FrozenTableView, self).resizeEvent(event)
        self.updateFrozenTableGeometry()

    def moveCursor(self, cursorAction, modifiers) -> QModelIndex:
        """Handle cursor movement with special logic for the frozen column.

        Parameters
        ----------
        cursorAction : QAbstractItemView.CursorAction
            The cursor action being performed
        modifiers : Qt.KeyboardModifiers
            Keyboard modifiers

        Returns
        -------
        QModelIndex
            The new cursor position
        """
        current = super(FrozenTableView, self).moveCursor(cursorAction, modifiers)
        if (
            cursorAction == self.MoveLeft
            and current.column() > 0
            and self.visualRect(current).topLeft().x() < self.frozenTableView.columnWidth(0)
        ):
            newValue = (
                self.horizontalScrollBar().value()
                + self.visualRect(current).topLeft().x()
                - self.frozenTableView.columnWidth(0)
            )
            self.horizontalScrollBar().setValue(newValue)
        return current

    def scrollTo(self, index, hint):
        """Scroll to the given index, but only if it's not in the frozen column.

        Parameters
        ----------
        index : QModelIndex
            The index to scroll to
        hint : QAbstractItemView.ScrollHint
            The scroll hint
        """
        if index.column() > 0:
            super(FrozenTableView, self).scrollTo(index, hint)

    def updateFrozenTableGeometry(self) -> None:
        """Update the geometry of the frozen table to match the main table."""
        self.frozenTableView.setGeometry(
            self.verticalHeader().width() + self.frameWidth(),
            self.frameWidth(),
            self.columnWidth(0),
            self.viewport().height() + self.horizontalHeader().height(),
        )
