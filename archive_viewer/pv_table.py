import epics
import re
import pandas as pd
from archive_search import ArchiveSearchWidget
from functools import partial
from datetime import datetime
from qtpy import QtCore, QtGui
from pydm.widgets import PyDMLineEdit
from collections.abc import MutableSequence
from qtpy.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QSpinBox,
    QComboBox,
    QMessageBox,
    QFileDialog,
    QTableWidgetItem,
    QSpacerItem,
    QSizePolicy,
    QCheckBox,
    QSlider,
    QHeaderView,
    QColorDialog,
    QMenu,
    QAction,
    QDialog,
    QButtonGroup,
    QGridLayout,
)


class PVTable(QWidget):
    """
    The PVTable,

    Parameters
    ----------
    parent : QWidget
      The parent widget for the table
    macros : str, optional

    table_headers : list, optional
      list of strings that sets the header names for the table.
    max_rows : int, optional
      max number of rows for the table.
    number_columns : int, optional
      number of columns in the table
    """

    send_data_change_signal = QtCore.Signal()

    def __init__(self, macros=None, table_headers=[], max_rows=1, number_columns=8, col_widths=[50]):
        super().__init__()
        self.data = PVList()
        self.data.set_callback(self.data_changed)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.spacer = QSpacerItem(100, 10, QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.widget_list = [
            PyDMLineEdit(),
            QComboBox(),
            QComboBox(),
            QCheckBox(),
            QCheckBox(),
            QPushButton(),
            QComboBox(),
            QSlider(orientation=QtCore.Qt.Horizontal),
        ]
        self.table_headers = table_headers
        self.table = None
        self.number_columns = number_columns
        self.max_rows = max_rows
        self.col_widths = col_widths
        self.make_frame()
        self.setup_table()
        self.last_clicked_index = None  # Add this line
        self.contextMenu = PVContextMenu(self)
        self.contextMenu.data_changed_signal.connect(self.handle_delete_pv_row)

        if macros:
            self.macros = macros
            if "PV" in self.macros.keys():
                try:
                    self.table.cellWidget(0, 0).setText(macros["PV"])
                    self.passPV(0)
                except Exception:
                    print("Error with loading single PV")
            elif "CSV" in self.macros.keys():
                try:
                    self.applyCSVFile(macros["CSV"])
                except Exception:
                    print("Error: File not found")
        else:
            self.macros = {"PV": "", "CSV": ""}

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            position = event.pos()
            index = self.table.indexAt(position)

            if index.isValid():
                self.last_clicked_index = index  # Store the clicked index
                self.show_context_menu(index, event.globalPos())

        super().mousePressEvent(event)

    def remove_row(self, index):
        if 0 <= index < len(self.data):
            self.data.pop(index)
            self.table.removeRow(index)

    def show_context_menu(self, index, global_position):
        context_menu = PVContextMenu(self)
        context_menu.data_changed_signal.connect(self.handle_delete_pv_row)
        context_menu.index = index.row()  # Store the row index for deletion
        context_menu.exec_(global_position)

    """
    def show_context_menu(self, point):
        index = self.table.indexAt(point)
        if index.isValid():
            row = index.row()
            self.contextMenu.index = row  # Update the stored index in the context menu
            self.contextMenu.exec_(self.table.viewport().mapToGlobal(point))
    """

    def data_menu(self, position_of_click):
        self.archive_search = ArchiveSearchWidget()
        self.archive_search.move(self.mapToGlobal(position_of_click))
        self.archive_search.show()

    def handle_delete_pv_row(self, row):
        if row < 0 or row >= len(self.data):
            return

        self.data[row][0]  # Assuming the PV name is stored at index 0 in the data list (adjust as needed)
        self.remove_row(row)
        self.send_data_change_signal.emit()

    def make_frame(self) -> None:
        self.table_frame = QFrame()
        self.table_frame_layout = QVBoxLayout()
        self.table_frame.setLayout(self.table_frame_layout)
        self.main_layout.addWidget(self.table_frame)

    def setup_table(self):
        self.table = QTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.table.setRowCount(self.max_rows)
        self.table.setColumnCount(self.number_columns)

        if len(self.col_widths) == 1:
            self.col_widths = self.col_widths * self.table.columnCount()
        if len(self.col_widths) < self.table.columnCount():
            pass

        # Set the row headers with letters
        for row_index in range(self.table.rowCount()):
            letter = self.get_letter(row_index)
            self.table.setVerticalHeaderItem(row_index, QTableWidgetItem(letter))

        # col_widths = [200, 200, 80, 80, 100, 80, 160, 40, 60, 80]
        for i in range(self.table.columnCount()):
            self.table.setColumnWidth(i, self.col_widths[i])

        self.table.setHorizontalHeaderLabels(self.table_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

        for i in range(self.table.rowCount()):
            self.setupRow(i)

        self.table_frame_layout.addWidget(self.table)

        # Set context menu policy for the entire table
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        # Connect context menu to the table's customContextMenuRequested signal
        self.table.customContextMenuRequested.connect(self.show_context_menu)

    def setupRow(self, index):
        for i in range(0, self.table.columnCount()):
            obj = [
                QLineEdit(),
                QComboBox(),
                QCheckBox(),
                QCheckBox(),
                QPushButton(),
                QComboBox(),
                QSlider(orientation=QtCore.Qt.Horizontal),
            ]

            # if i == 1:  # Time Axis drop-down menu
            #     time_axes_names = [axis["axis_name"] for axis in self.time_axes]
            #     obj[i].addItems(time_axes_names)

            if i == 4:  # Color column
                color_button = QPushButton()
                color_button.setStyleSheet("background-color: white")
                color_button.clicked.connect(partial(self.openColorPicker, index, color_button))
                self.table.setCellWidget(index, i, color_button)
            else:
                self.table.setCellWidget(index, i, obj[i])
        # establish signals
        self.table.cellWidget(index, 0).textChanged.connect(
            partial(partial(self.update_data, index, 0, self.table.cellWidget(index, 0).text))
        )

        self.table.cellWidget(index, 1).currentIndexChanged.connect(
            partial(self.update_data, index, 1, self.table.cellWidget(index, 1).currentText())
        )
        # self.table.cellWidget(index, 2).currentIndexChanged.connect(partial(self.update_data, index, 2,
        #                                                             self.table.cellWidget(index, 2).currentText()))
        self.table.cellWidget(index, 2).stateChanged.connect(
            partial(self.update_data, index, 2, self.table.cellWidget(index, 2).checkState)
        )
        # Set the initial state of the "Visible" checkbox to checked
        self.table.cellWidget(index, 2).setChecked(True)
        self.table.cellWidget(index, 3).stateChanged.connect(
            partial(self.update_data, index, 3, self.table.cellWidget(index, 3).checkState)
        )
        # self.table.cellWidget(index, 5).currentIndexChanged.connect(partial(self.update_data, index, 5,
        # self.table.cellWidget(index, 5).currentText()))
        self.table.cellWidget(index, 5).currentIndexChanged.connect(
            partial(self.update_data, index, 5, self.table.cellWidget(index, 5).currentText())
        )
        self.table.cellWidget(index, 6).valueChanged.connect(
            partial(self.update_data, index, 6, self.table.cellWidget(index, 6).value)
        )

        letter = self.get_letter(index)
        self.table.setVerticalHeaderItem(index, QTableWidgetItem(letter))

        self.data.append(
            PVList(
                [
                    self.table.cellWidget(index, 0).text(),
                    self.table.cellWidget(index, 1).currentText(),
                    self.table.cellWidget(index, 2).checkState(),
                    self.table.cellWidget(index, 3).checkState(),
                    0,
                    self.table.cellWidget(index, 5).currentText(),
                    self.table.cellWidget(index, 6).value(),
                ]
            )
        )

        self.data[-1].set_callback(self.data_changed)

    def get_letter(self, index):
        if index < 26:
            return chr(ord("A") + index)
        else:
            div = index // 26
            mod = index % 26
            return chr(ord("A") + div - 1) + chr(ord("A") + mod)

    def update_data(self, index, position, value):
        print(index, position, value)
        self.add_Row(index)
        try:
            if isinstance(self.table.cellWidget(index, position), QComboBox):
                self.data[index][position] = value
            elif isinstance(self.table.cellWidget(index, position), QPushButton):
                color_button = self.table.cellWidget(index, position)
                color_style = color_button.styleSheet()
                match = re.search(r"background-color: (.*?);", color_style)
                if match:
                    color = match.group(1)
                    self.data[index][position] = color
        except IndexError:
            print("Error: Invalid index")

    def add_Row(self, index):
        if index != len(self.data) - 1:
            return

        current_row_count = self.table.rowCount()
        current_row_count += 1
        self.table.setRowCount(current_row_count)
        self.setupRow(current_row_count - 1)

        # Set the row header for the newly added row
        letter = self.get_letter(current_row_count - 1)
        self.table.setVerticalHeaderItem(current_row_count - 1, QTableWidgetItem(letter))

    def resetRow(self, index):
        if not self.widget_list:
            return False

        obj = [
            PyDMLineEdit(),
            QComboBox(),
            QCheckBox(),
            QCheckBox(),
            QPushButton(),
            QComboBox(),
            QSlider(orientation=QtCore.Qt.Horizontal),
        ]

        for i in range(0, self.table.columnCount()):
            self.table.setCellWidget(index, i, obj[i])

        """
        for j in range(1, self.table.columnCount()):
            self.table.setCellWidget(index, j, PyDMLabel(' '))
            self.table.cellWidget(index, j).setText(None)
            self.table.cellWidget(index, j).setAlignment(QtCore.Qt.AlignCenter)
        self.table.cellWidget(index, 2).setProperty('precisionFromPV', True)
        self.table.removeCellWidget(index, 4)
        self.table.setItem(index, 4, QTableWidgetItem())
        self.table.setCellWidget(index, 7, QPushButton('Save'))
        self.table.setCellWidget(index, 8, QPushButton('Restore'))
        self.table.setCellWidget(index, 9, PyDMLineEdit())
        self.table.cellWidget(index, 7).clicked.connect(partial(self.savePV, index))
        self.table.cellWidget(index, 8).clicked.connect(partial(self.restorePV, index))
        """

    def passPV(self, index):
        self.data = self.table.cellWidget(index, 0).text()

        """
        if '#' in pv:
            self.resetRow(index)
            strings = pv.split('#')
            colors = ['white', 'cyan', 'darkcyan', 'red', 'darkred', 'magenta', 'darkmagenta', 'green', 'darkgreen',
                      'yellow', 'gray', 'darkgray', 'lightgray', 'blue', 'darkblue', 'black']
            darkcolors = ['green', 'darkgreen', 'blue', 'darkblue', 'black', 'darkred', 'darkmagenta', 'red']
            for split in strings:
                if split in colors:
                    style = 'font-weight: bold; background-color: ' + split
                    for i in range(4):
                        self.table.cellWidget(index, i).setStyleSheet(style)
                    for i in range(4,5):
                        pass
                        # self.table.item(index, i).setBackground(QColor(split))
                    for i in range(5,7):
                        self.table.cellWidget(index, i).setStyleSheet(style)
                if split in darkcolors:
                    font = style + '; color: white;'
                    self.table.cellWidget(index, 0).setStyleSheet(font)
        elif pv == '':
            pass
            self.resetRow(index)
        else:
            for i in range(4):
                self.table.cellWidget(index, i).setStyleSheet(None)
            for i in range(4,5):
                pass
                # self.table.item(index, i).setBackground(QColor('transparent'))
            for i in range(5, self.number_columns):
                self.table.cellWidget(index, i).setStyleSheet(None)
            self.table.cellWidget(index, 1).channel = pv + '.DESC'
            self.table.cellWidget(index, 2).channel = pv
            self.table.cellWidget(index, 3).channel = pv + '.SEVR'
            self.chan1 = PyDMChannel(self.table.cellWidget(index, 2).channel, value_slot=partial(self.differenceCalc,
                                                                                                 foobar=index))
            self.chan1.connect()
            self.chan1.connect()
            self.table.cellWidget(index, self.number_columns).channel = pv
        """

    def savePV(self, index):
        ## Check that channel is connected
        if self.table.cellWidget(index, 2).channel:
            value = self.table.cellWidget(index, 2).text()
            self.table.item(index, 4).setText(value)
            now = datetime.now()
            dt_string = now.strftime("%m/%d/%Y %H:%M:%S")
            self.table.cellWidget(index, 6).setText(dt_string)
            self.table.item(index, 4).setBackground(QtGui.QColor(159, 157, 154))

    def saveAll(self):
        for i in range(self.table.rowCount()):
            self.savePV(i)

    def restorePV(self, index):
        if self.table.item(index, 4).text():
            value = self.table.item(index, 4).text()
            pv = epics.PV(self.table.cellWidget(index, 0).text())
            pv.put(value)

    def restoreAll(self):
        pv_list = []
        value_list = []
        for i in range(self.table.rowCount()):
            if self.table.item(i, 4).text():
                try:
                    value = self.table.item(i, 4).text()
                    value = float(value)
                    value_list.append(value)
                    pv = self.table.cellWidget(i, 0).text()
                    pv_list.append(pv)
                    epics.caput_many(pv_list, value_list)
                except Exception:
                    pass

    def differenceCalc(self, new_val, foobar):
        live = self.table.cellWidget(foobar, 2).text()
        saved = self.table.item(foobar, 4).text()
        if saved:
            self.table.item(foobar, 4).setBackground(QtGui.QColor(159, 157, 154))
            if live != saved:
                self.table.item(foobar, 4).setBackground(QtGui.QColor(255, 157, 154))
            try:
                live = float(live)
                saved = float(saved)
                diff = live - saved
                self.table.cellWidget(foobar, 5).setText(str(diff))
            except Exception:
                pass

    def setupHeader(self):
        self.header_frame[0].setMaximumHeight(40)

        QLabel("Number of Rows:")
        self.row_spin = QSpinBox()
        self.row_spin.setValue(10)
        self.row_spin.setKeyboardTracking(False)
        self.row_spin.setRange(1, 200)
        self.row_spin.valueChanged.connect(self.editRows)

        QLabel("Filter:")
        self.fltr_edit = QLineEdit()
        self.fltr_edit.returnPressed.connect(self.doSearch)
        fltr_btn = QPushButton("Search")
        fltr_btn.clicked.connect(self.doSearch)
        fltr_rst_btn = QPushButton("Reset")
        fltr_rst_btn.clicked.connect(self.resetSearch)

        QLabel("Menu:")
        self.combo_btn = QComboBox()
        combo_items = [
            "Export to CSV",
            "Load Snapshot",
            "Load with eget",
            "Clear Saves (Confirm)",
            "Clear Table (Confirm)",
        ]
        self.combo_btn.addItems(combo_items)
        self.combo_btn.activated.connect(self.comboChoice)

    def editRows(self):
        new_num_rows = self.row_spin.value()
        total_num_rows = self.table.rowCount()

        for i in range(total_num_rows):
            self.table.hideRow(i)
        for i in range(new_num_rows):
            self.table.showRow(i)

        # if new_num_rows > 199:
        #   self.insert_btn.setEnabled(False)
        # else:
        #   self.insert_btn.setEnabled(True)

    def doSearch(self):
        search_text = self.fltr_edit.text()
        if search_text == "":
            self.editRows()
        for i in range(self.table.rowCount()):
            pv = self.table.cellWidget(i, 0).text()
            if search_text.upper() not in pv.upper():
                self.table.hideRow(i)

    def resetSearch(self):
        self.fltr_edit.setText("")
        self.editRows()

    def comboChoice(self):
        if self.combo_btn.currentIndex() == 0:
            self.exportToCSV()
        elif self.combo_btn.currentIndex() == 1:
            self.loadSnapshot()
        elif self.combo_btn.currentIndex() == 2:
            self.showEGETFrame()
        elif self.combo_btn.currentIndex() == 3:
            self.clearConfirm(self.clearSaves, "Saves")
        elif self.combo_btn.currentIndex() == 4:
            self.clearConfirm(self.clearTable, "Table")

    def exportToCSV(self):
        list_data = []
        shown_rows = int(self.row_spin.text())
        for i in range(shown_rows):
            list_row = []
            for j in range(self.table.columnCount()):
                if j in [0, 1, 2, 3, 5, 6, 9, 10]:
                    cell_text = self.table.cellWidget(i, j).text()
                    if not cell_text:
                        cell_text = " "
                elif j == 4:
                    cell_text = self.table.item(i, j).text()
                    if not cell_text:
                        cell_text = " "
                elif j in [7, 8]:
                    cell_text = " "
                list_row.append(cell_text)
            list_data.append(list_row)
        df = pd.DataFrame(list_data, columns=self.table_headers)
        file_dialog = QFileDialog()
        file_dialog.setDefaultSuffix(".csv")
        try:
            csv_file = file_dialog.getSaveFileName(self, "Save File", "", "Comma-separated values (*.csv)")[0]
            df.to_csv(csv_file)
        except IOError:
            pass

    def loadSnapshot(self):
        file_dialog = QFileDialog()
        try:
            csv_file = file_dialog.getOpenFileName(self, "Open File", "", "Comma-separated values (*.csv)")

            if csv_file != "":
                self.applyCSVFile(csv_file[0])

        except IOError:
            pass

    def applyCSVFile(self, filename):
        df = pd.read_csv(filename)
        pvs = list(df.PV)
        self.clearTable()
        self.row_spin.setValue(len(pvs))

        for i in range(len(pvs)):
            self.table.cellWidget(i, 0).setText(str(df.PV.iloc[i]))
            self.table.item(i, 4).setText(str(df["Saved Value"].iloc[i]))
            self.table.cellWidget(i, 6).setText(str(df["Save Timestamp"].iloc[i]))

    def clearConfirm(self, fxn, items):
        msg = QMessageBox()
        msg.setWindowTitle("Confirm " + str(items) + " Clear")
        msg.setText("Are you sure you want to clear the " + items.lower() + "?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.buttonClicked.connect(partial(self.clearConfirmClicked, fxn=fxn))
        msg.exec_()

    def clearConfirmClicked(self, i, fxn):
        button_clicked = i.text()
        if button_clicked == "&Yes":
            fxn()

    def clearTable(self):
        self.table.deleteLater()
        self.setup_table()
        self.editRows()

    def clearSaves(self):
        for i in range(self.table.rowCount()):
            if self.table.item(i, 4).text():
                self.table.item(i, 4).setText("")
                self.table.item(i, 4).setBackground(QtGui.QColor(159, 157, 154))
                self.table.cellWidget(i, 5).setText("")
                self.table.cellWidget(i, 6).setText("")

    def setupFooter(self):
        self.footer_frame[0].setMaximumHeight(40)
        # insert_lbl = QLabel('Insert Row Below:')
        # self.insert_spin = QSpinBox()
        # self.insert_spin.setRange(1,199)
        # self.insert_btn = QPushButton('Insert Row')
        # self.insert_btn.clicked.connect(self.insertRow)

        save_all_btn = QPushButton("Save All")
        save_all_btn.clicked.connect(self.saveAll)

        restore_all_btn = QPushButton("Restore All")
        restore_all_btn.setEnabled(False)
        # restore_all_btn.clicked.connect(self.restoreAll)

        """
        helpfile = 'pv_table_help.ui'
        help_btn = PyDMRelatedDisplayButton('Help...', filename = helpfile)
        help_btn.setMaximumWidth(80)
        help_btn.setProperty('openInNewWindow', True)
        """

        # footer_widgets = [self.spacer, save_all_btn, restore_all_btn, help_btn]
        # footer_widgets = [self.spacer, save_all_btn, restore_all_btn]

    # def insertRow(self):
    #   insert_row = self.insert_spin.value()
    #  num_rows = self.row_spin.value() + 1
    # self.table.insertRow(insert_row)
    # for i in range(insert_row, num_rows):
    #   self.setupRow(i)
    # self.row_spin.setValue(num_rows)

    def openColorPicker(self, index, button_widget):
        color_dialog = QColorDialog()
        color = color_dialog.getColor()

        if color.isValid():
            button_widget.setStyleSheet(f"background-color: {color.name()}")
            self.update_data(index, 5, color.name())

    def contextMenuEvent(self, event):
        if self.last_clicked_index is not None:
            index = self.last_clicked_index

            context_menu = PVContextMenu(self)
            context_menu.data_changed_signal.connect(self.handle_delete_pv_row)
            context_menu.index = index.row()  # Store the row index for deletion
            context_menu.exec_(event.globalPos())

    def data_changed(self):
        self.send_data_change_signal.emit()


class PVList(MutableSequence):
    """ """

    def __init__(self, iterable=()):
        self._list = list(iterable)

    def __getitem__(self, key):
        return self._list.__getitem__(key)

    def __setitem__(self, key, item):
        self._list.__setitem__(key, item)
        # trigger change handler
        self.callback()

    def __delitem__(self, key):
        self._list.__delitem__(key)
        # trigger change handler
        self.callback()

    def __len__(self):
        return self._list.__len__()

    def insert(self, index, item):
        self._list.insert(index, item)
        # trigger change handler
        self.callback()

    def set_callback(self, callback):
        self.callback = callback


class PVContextMenu(QMenu):
    """ """

    data_changed_signal = QtCore.Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Add "SEARCH PV" option
        search_pv_action = QAction("SEARCH PV", self)
        search_pv_action.triggered.connect(self.search_pv)
        self.addAction(search_pv_action)

        # Add "FORMULA" option
        formula_action = QAction("FORMULA", self)
        formula_action.triggered.connect(self.open_formula_dialog)
        self.addAction(formula_action)

        # Add "DELETE PV" option
        delete_pv_action = QAction("DELETE PV", self)
        delete_pv_action.triggered.connect(self.delete_pv)
        self.addAction(delete_pv_action)

    def search_pv(self):
        # Open the ArchiveSearchWidget
        archive_search = ArchiveSearchWidget()
        archive_search.show()

    def open_formula_dialog(self):
        # Create the formula dialog window
        dialog = QDialog(self)
        dialog.setWindowTitle("Formula Input")
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)

        # Create the layout for the dialog
        layout = QVBoxLayout(dialog)

        # Create the QLineEdit for formula input
        formula_input = QLineEdit()
        layout.addWidget(formula_input)

        # Create the QButtonGroup for calculator buttons
        button_group = QButtonGroup(dialog)

        # Define the list of calculator buttons
        buttons = [
            "7",
            "8",
            "9",
            "+",
            "4",
            "5",
            "6",
            "-",
            "1",
            "2",
            "3",
            "*",
            "0",
            "(",
            ")",
            "/",
            ".",
            "PV",
            "Clear",
            "=",
        ]

        # Create the calculator buttons and connect them to the input field
        grid_layout = QGridLayout()
        row, col = 0, 0
        for button_text in buttons:
            button = QPushButton(button_text)
            button_group.addButton(button)
            grid_layout.addWidget(button, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

            # Connect the button clicked signal to the appropriate action
            if button_text == "PV":
                button.clicked.connect(lambda checked, field=formula_input: field.insert("PV"))
            elif button_text == "Clear":
                button.clicked.connect(lambda checked, field=formula_input: field.clear())
            elif button_text == "=":
                button.clicked.connect(lambda checked, field=formula_input: self.evaluate_formula(field))
            else:
                button.clicked.connect(lambda checked, field=formula_input, text=button_text: field.insert(text))

        layout.addLayout(grid_layout)

        # Add an input field for PV name
        pv_name_input = QLineEdit()
        pv_name_input.setPlaceholderText("Enter PV name")
        layout.addWidget(pv_name_input)

        # Add an "OK" button to accept the formula and close the dialog
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(lambda: self.accept_formula(dialog, formula_input, pv_name_input))
        layout.addWidget(ok_button)

        # Execute the dialog
        dialog.exec_()

    def evaluate_formula(self, formula_input):
        # Evaluate the formula expression and update the formula input field
        formula = formula_input.text()
        try:
            result = eval(formula)
            formula_input.setText(str(result))
        except (SyntaxError, TypeError):
            formula_input.setText("Error")

    def accept_formula(self, dialog, formula_input, pv_name_input):
        # Retrieve the formula and PV name and perform desired actions
        formula = formula_input.text()
        pv_name = pv_name_input.text()

        print("Formula:", formula)
        print("PV Name:", pv_name)

        dialog.accept()

    def delete_pv(self):
        if self.index is not None and 0 <= self.index < len(self.parentWidget().data):
            self.parentWidget().data[self.index][0]
            self.parentWidget().remove_row(self.index)
            self.parentWidget().send_data_change_signal.emit()
            self.parentWidget().data.pop(self.index)
            self.data_changed_signal.emit(self.index)
            print("Delete Row")
        else:
            print("Invalid index or index out of range")

    def get_letter(self, index):
        return chr(ord("A") + index)

    '''
    def eventFilter(self, obj, event):
        """
                Filters events on this object.

                Params
                ------
                object : QObject
                    The object that is being handled.
                event : QEvent
                    The event that is happening.

                Returns
                -------
                bool
                    True to stop the event from being handled further; otherwise
                    return false.
                """
    '''
