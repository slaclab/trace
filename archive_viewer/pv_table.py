import os
import epics
import copy
import pandas as pd
import typing
from archive_search import ArchiveSearchWidget
from functools import partial
from datetime import datetime
from qtpy import QtCore, QtGui
from pydm.widgets import PyDMLineEdit
from qtpy.QtWidgets import (QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout,
                            QLineEdit, QPushButton, QTableWidget, QSpinBox,
                            QComboBox, QMessageBox, QFileDialog, QTableWidgetItem,
                            QSpacerItem, QSizePolicy, QCheckBox, QSlider, QHeaderView, QColorDialog)
from collections.abc import MutableSequence
from PyQt5.QtWidgets import QWidget, QCalendarWidget, QMenu, QAction, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QButtonGroup, QGridLayout


## Test PV: SIOC:SYS0:MG01:HEARTBEAT
class PyDMPVTable(QWidget):
    """
      The PyDMPVTable,

      Parameters
      ----------
      parent : QWidget
          The parent widget for the table
      macros : str, optionalt

      table_headers : list, optional
        list of strings that sets the header names for the table.
      max_rows : int, optional
        max number of rows for the table.
      number_columns : int, optional
        number of columns in the table
      """

    send_data_change_signal = QtCore.Signal()



    def __init__(self, time_axes, macros=None, table_headers=[], max_rows=1, number_columns=10, col_widths=[50]):
        super().__init__()
        self.time_axes = time_axes  # Store the reference to the time axes list
        self.data = PVList()
        self.data.set_callback(self.data_changed)    
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.spacer = QSpacerItem(100, 10, QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.widget_list = [PyDMLineEdit(), QComboBox(), QComboBox(), QCheckBox(), QCheckBox(), QPushButton(),
                            QComboBox(), QSlider(orientation=QtCore.Qt.Horizontal)]
        self.table_headers = table_headers
        self.table = None
        self.number_columns = number_columns
        self.max_rows = max_rows
        self.col_widths = col_widths
        self.makeMainFrames()
        self.setup_table()



        if macros:
            self.macros = macros
            if 'PV' in self.macros.keys():
                try:
                    self.table.cellWidget(0, 0).setText(macros['PV'])
                    self.passPV(0)
                except:
                    print('Error with loading single PV')
            elif 'CSV' in self.macros.keys():
                try:
                    self.applyCSVFile(macros['CSV'])
                except:
                    print('Error: File not found')
        else:
            self.macros = {'PV': '',
                           'CSV': ''}


        self.time_axes = time_axes  # Store the reference to the time axes list
        self.contextMenu = PVContextMenu(self)
        self.contextMenu.data_changed_signal.connect(self.handle_delete_pv_row)




    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            if isinstance(self.focusWidget(), QLineEdit):
                position_of_click = event.pos()
                self.data_menu(position_of_click)

    def data_menu(self, position_of_click):
        self.archive_search = ArchiveSearchWidget()
        self.archive_search.move(self.mapToGlobal(position_of_click))
        self.archive_search.show()


    def handle_delete_pv_row(self, row):
        if row < 0 or row >= len(self.data):
            return

        pv_name = self.data[row][0]  # Assuming the PV name is stored at index 0 in the data list (adjust as needed)
        self.remove_row(row)
        self.send_data_change_signal.emit()


    @staticmethod
    def make_frame(orientation):
        frame = QFrame()
        if orientation == 'H':
            layout = QHBoxLayout()
        elif orientation == 'V':
            layout = QVBoxLayout()
        frame.setLayout(layout)

        new_frame = (frame, layout)

        return new_frame

    @staticmethod
    def fill_layout(layout, widgets):
        for widget in widgets:
            try:
                layout.addWidget(widget)
            except TypeError:
                layout.addItem(widget)

    def makeMainFrames(self):
        #self.title_frame = self.make_frame('H')
        #self.header_frame = self.make_frame('H')
        #self.eget_frame = self.make_frame('H')
        self.table_frame = self.make_frame('V')
        #self.footer_frame = self.make_frame('H')

        #frames = [self.title_frame[0], self.header_frame[0], self.eget_frame[0], self.table_frame[0], self.footer_frame[0]]
        frames = [self.table_frame[0]]
        self.fill_layout(self.main_layout, frames)

    '''
    def setupTitle(self):
        self.title_frame[0].setStyleSheet('background-color: rgb(127,127,127); color: rgb(242,242,242)')
        img = QImage()
        img.load('SLAC_LogoSD_W.png')
        pixmap = QPixmap.fromImage(img)

        img = QLabel()
        img.setMaximumHeight(30)
        img.setPixmap(pixmap.scaled(img.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

        title = QLabel('PV Table')
        title.setStyleSheet('QLabel {font-size: 24px; font-weight: bold}')
        self.title_frame[1].addWidget(img)
        self.title_frame[1].addItem(self.spacer)
        self.title_frame[1].addWidget(title)
        self.title_frame[1].addItem(self.spacer)
        self.title_frame[0].setMaximumHeight(50)
    '''




    def setup_table(self):
        self.table = QTableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.table.setRowCount(self.max_rows)
        self.table.setColumnCount(self.number_columns)

        if len(self.col_widths) == 1:
            self.col_widths = self.col_widths*self.table.columnCount()
        if len(self.col_widths) < self.table.columnCount():
            pass
            #self.col_widths.append()

        #col_widths = [200, 200, 80, 80, 100, 80, 160, 40, 60, 80]
        for i in range(self.table.columnCount()):
            self.table.setColumnWidth(i, self.col_widths[i])

        self.table.setHorizontalHeaderLabels(self.table_headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        #self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        for i in range(self.table.rowCount()):
            self.setupRow(i)

        self.table_frame[1].addWidget(self.table)


    def setupRow(self, index):
        for i in range(0, self.table.columnCount()):
            obj = [QLineEdit(), QComboBox(), QComboBox(), QCheckBox(), QCheckBox(), QPushButton(),
                   QComboBox(), QSlider(orientation=QtCore.Qt.Horizontal)]

            if i == 1:  # Time Axis drop-down menu
                time_axes_names = [axis["axis_name"] for axis in self.time_axes]
                obj[i].addItems(time_axes_names)

            if i == 5:  # Color column
                color_button = QPushButton()
                color_button.clicked.connect(partial(self.openColorPicker, index))
                self.table.setCellWidget(index, i, color_button)
            else:
                self.table.setCellWidget(index, i, obj[i])
        # establish signals
        self.table.cellWidget(index, 0).textChanged.connect(partial(partial(self.update_data, index, 0,
                                                                                self.table.cellWidget(index, 0).text)))

        self.table.cellWidget(index, 1).currentIndexChanged.connect(partial(self.update_data, index, 1,
                                                                    self.table.cellWidget(index, 1).currentText()))
        self.table.cellWidget(index, 2).currentIndexChanged.connect(partial(self.update_data, index, 2,
                                                                    self.table.cellWidget(index, 2).currentText()))
        self.table.cellWidget(index, 3).stateChanged.connect(partial(self.update_data, index, 3,
                                                             self.table.cellWidget(index, 3).checkState))
        self.table.cellWidget(index, 4).stateChanged.connect(partial(self.update_data, index, 4,
                                                             self.table.cellWidget(index, 4).checkState))
        # self.table.cellWidget(index, 5).clicked.connect(partial(self.update_data, index, 5,
        #                                                self.table.cellWidget(index, 5)))
        self.table.cellWidget(index, 6).currentIndexChanged.connect(partial(self.update_data, index, 6,
                                                                    self.table.cellWidget(index, 6).currentText()))
        self.table.cellWidget(index, 7).valueChanged.connect(partial(self.update_data, index, 7,
                                                                     self.table.cellWidget(index, 7).value))

        self.data.append(PVList([self.table.cellWidget(index, 0).text(),
                          self.table.cellWidget(index, 1).currentText(),
                          self.table.cellWidget(index, 2).currentText(),
                          self.table.cellWidget(index, 3).checkState(),
                          self.table.cellWidget(index, 4).checkState(),
                          0,
                          self.table.cellWidget(index, 6).currentText(),
                          self.table.cellWidget(index, 7).value]))

        self.data[-1].set_callback(self.data_changed)


    def update_data(self, index, position, value):
        print(index, position, value)
        self.add_Row(index)
        try:
            self.data[index][position] = value
        except IndexError:
            print("Error: Invalid index")


    def add_Row(self, index):
        if index != len(self.data) - 1:
            return

        current_row_count = self.table.rowCount()
        current_row_count += 1
        self.table.setRowCount(current_row_count)
        self.setupRow(current_row_count-1)


    def resetRow(self, index):
        if not self.widget_list:
            return False

        obj = [PyDMLineEdit(), QComboBox(), QComboBox(), QCheckBox(), QCheckBox(), QPushButton(),
               QComboBox(), QSlider(orientation=QtCore.Qt.Horizontal)]

        for i in range(0, self.table.columnCount()):
            self.table.setCellWidget(index, i, obj[i])

        '''
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
        '''

    def passPV(self, index):
        self.data = self.table.cellWidget(index, 0).text()

        '''
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
        '''

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
                except:
                    a = 1

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
            except:
                a = 1

    def setupHeader(self):
        self.header_frame[0].setMaximumHeight(40)

        row_lbl = QLabel('Number of Rows:')
        self.row_spin = QSpinBox()
        self.row_spin.setValue(10)
        self.row_spin.setKeyboardTracking(False)
        self.row_spin.setRange(1,200)
        self.row_spin.valueChanged.connect(self.editRows)

        fltr_lbl = QLabel('Filter:')
        self.fltr_edit = QLineEdit()
        self.fltr_edit.returnPressed.connect(self.doSearch)
        fltr_btn = QPushButton('Search')
        fltr_btn.clicked.connect(self.doSearch)
        fltr_rst_btn = QPushButton('Reset')
        fltr_rst_btn.clicked.connect(self.resetSearch)

        combo_lbl = QLabel('Menu:')
        self.combo_btn = QComboBox()
        combo_items = ['Export to CSV', 'Load Snapshot',
                       'Load with eget', 'Clear Saves (Confirm)',
                       'Clear Table (Confirm)',]
        self.combo_btn.addItems(combo_items)
        self.combo_btn.activated.connect(self.comboChoice)

        #header_widgets = [row_lbl, self.row_spin, self.spacer, fltr_lbl, self.fltr_edit, fltr_btn, fltr_rst_btn, self.spacer, combo_lbl, self.combo_btn]

        #self.fill_layout(self.header_frame[1], header_widgets)

    def editRows(self):
        new_num_rows = self.row_spin.value()
        total_num_rows = self.table.rowCount()

        for i in range(total_num_rows):
            self.table.hideRow(i)
        for i in range(new_num_rows):
            self.table.showRow(i)

        #if new_num_rows > 199:
         #   self.insert_btn.setEnabled(False)
        #else:
         #   self.insert_btn.setEnabled(True)

    def doSearch(self):
        search_text = self.fltr_edit.text()
        if search_text == '':
            self.editRows()
        for i in range(self.table.rowCount()):
            pv = self.table.cellWidget(i, 0).text()
            if search_text.upper() not in pv.upper():
                self.table.hideRow(i)

    def resetSearch(self):
        self.fltr_edit.setText('')
        self.editRows()

    def comboChoice(self):
        if self.combo_btn.currentIndex() == 0:
            self.exportToCSV()
        elif self.combo_btn.currentIndex() == 1:
            self.loadSnapshot()
        elif self.combo_btn.currentIndex() == 2:
            self.showEGETFrame()
        elif self.combo_btn.currentIndex() == 3:
            self.clearConfirm(self.clearSaves, 'Saves')
        elif self.combo_btn.currentIndex() == 4:
            self.clearConfirm(self.clearTable, 'Table')

    def exportToCSV(self):
        list_data = []
        shown_rows = int(self.row_spin.text())
        for i in range(shown_rows):
            list_row = []
            for j in range(self.table.columnCount()):
                if j in [0,1,2,3,5,6,9,10]:
                    cell_text = self.table.cellWidget(i,j).text()
                    if not cell_text:
                        cell_text = ' '
                elif j == 4:
                    cell_text = self.table.item(i,j).text()
                    if not cell_text:
                        cell_text = ' '
                elif j in [7,8]:
                    cell_text = ' '
                list_row.append(cell_text)
            list_data.append(list_row)
        df = pd.DataFrame(list_data, columns=self.table_headers)
        file_dialog = QFileDialog()
        file_dialog.setDefaultSuffix('.csv')
        try:
            csv_file = file_dialog.getSaveFileName(self, 'Save File','',  'Comma-separated values (*.csv)')[0]
            df.to_csv(csv_file)
        except IOError:
            a = 1

    def loadSnapshot(self):
        file_dialog = QFileDialog()
        try:
            csv_file = file_dialog.getOpenFileName(self, 'Open File', '', 'Comma-separated values (*.csv)')

            if csv_file != '':
                self.applyCSVFile(csv_file[0])

        except IOError:
            a = 1

    def applyCSVFile(self, filename):
        df = pd.read_csv(filename)
        pvs = list(df.PV)
        self.clearTable()
        self.row_spin.setValue(len(pvs))

        for i in range(len(pvs)):
            self.table.cellWidget(i, 0).setText(str(df.PV.iloc[i]))
            self.table.item(i, 4).setText(str(df['Saved Value'].iloc[i]))
            self.table.cellWidget(i, 6).setText(str(df['Save Timestamp'].iloc[i]))

    def clearConfirm(self, fxn, items):
        msg = QMessageBox()
        msg.setWindowTitle('Confirm ' + str(items) + ' Clear')
        msg.setText('Are you sure you want to clear the ' + items.lower() + '?')
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.buttonClicked.connect(partial(self.clearConfirmClicked, fxn = fxn))
        x = msg.exec_()

    def clearConfirmClicked(self, i, fxn):
        button_clicked = i.text()
        if button_clicked == '&Yes':
            fxn()

    def clearTable(self):
        self.table.deleteLater()
        self.setup_table()
        self.editRows()

    def clearSaves(self):
        for i in range(self.table.rowCount()):
            if self.table.item(i, 4).text():
                self.table.item(i, 4).setText('')
                self.table.item(i, 4).setBackground(QtGui.QColor(159, 157, 154))
                self.table.cellWidget(i, 5).setText('')
                self.table.cellWidget(i, 6).setText('')

    def setupFooter(self):
        self.footer_frame[0].setMaximumHeight(40)
        #insert_lbl = QLabel('Insert Row Below:')
        #self.insert_spin = QSpinBox()
        #self.insert_spin.setRange(1,199)
        #self.insert_btn = QPushButton('Insert Row')
        #self.insert_btn.clicked.connect(self.insertRow)

        save_all_btn = QPushButton('Save All')
        save_all_btn.clicked.connect(self.saveAll)

        restore_all_btn = QPushButton('Restore All')
        restore_all_btn.setEnabled(False)
        #restore_all_btn.clicked.connect(self.restoreAll)

        '''
        helpfile = 'pv_table_help.ui'
        help_btn = PyDMRelatedDisplayButton('Help...', filename = helpfile)
        help_btn.setMaximumWidth(80)
        help_btn.setProperty('openInNewWindow', True)
        '''

        #footer_widgets = [self.spacer, save_all_btn, restore_all_btn, help_btn]
        #footer_widgets = [self.spacer, save_all_btn, restore_all_btn]
        #self.fill_layout(self.footer_frame[1], footer_widgets)

    #def insertRow(self):
     #   insert_row = self.insert_spin.value()
      #  num_rows = self.row_spin.value() + 1
       # self.table.insertRow(insert_row)
        #for i in range(insert_row, num_rows):
         #   self.setupRow(i)
        #self.row_spin.setValue(num_rows)

    def setupEGET(self):
        self.eget_edit = QLineEdit()
        self.eget_edit.setPlaceholderText('Enter eget command')
        self.eget_edit.returnPressed.connect(self.runEGET)

        self.eget_btn = QPushButton('Run')
        self.eget_btn.clicked.connect(self.runEGET)

        eget_widgets = [self.spacer, self.eget_edit, self.eget_btn]
        self.fill_layout(self.eget_frame[1], eget_widgets)

        self.eget_frame[0].setMaximumHeight(40)
        self.eget_frame[0].hide()

    def showEGETFrame(self):
        self.eget_frame[0].show()

    def runEGET(self):
        command = self.eget_edit.text()
        startswith = command.startswith('eget')
        if startswith:
            try:
                stream = os.popen(command)
                output = stream.read()
                split_lines = output.splitlines()
                new_lines = []
                for line in split_lines:
                    line = str(line)
                    line = ''.join(line.split())
                    if ':' in line:
                        new_lines.append(line)

                length = len(new_lines)
                self.row_spin.setValue(length)
                self.editRows()

                for i in range(len(new_lines)):
                    self.table.cellWidget(i, 0).setText(new_lines[i])
                    self.passPV(i)
            except:
                print('Error with eget command')
        else:
            print('Error: Not an eget command')



    def openColorPicker(self, index):
        color_dialog = QColorDialog()
        color = color_dialog.getColor()

        if color.isValid():
            color_button = self.table.cellWidget(index, 5)
            color_button.setStyleSheet(f"background-color: {color.name()}")
            self.update_data(index, 5, color.name())

    def contextMenuEvent(self, event):
        menu = PVContextMenu(self)
        menu.exec_(event.globalPos())


    def data_changed(self):
        self.send_data_change_signal.emit()




class PVList(MutableSequence):


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
        dialog.setWindowModality(Qt.ApplicationModal)

        # Create the layout for the dialog
        layout = QVBoxLayout(dialog)

        # Create the QLineEdit for formula input
        formula_input = QLineEdit()
        layout.addWidget(formula_input)

        # Create the QButtonGroup for calculator buttons
        button_group = QButtonGroup(dialog)

        # Define the list of calculator buttons
        buttons = [
            "7", "8", "9", "+",
            "4", "5", "6", "-",
            "1", "2", "3", "*",
            "0", "(", ")", "/",
            ".", "PV", "Clear", "="
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
        # Get the row index of the selected PV
        index = self.table.currentRow()

        # Emit the delete_pv_row_requested signal with the row index
        self.data_changed_signal.emit(index)
        print("Delete Row")


    #         self.time_axis_combo.addItem(time_axis.name, time_axis)

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