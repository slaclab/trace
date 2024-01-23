from qtpy.QtGui import QColor
from qtpy.QtCore import Qt
from pydm import Display
from config import (logger, archiver_urls)
from mixins import (PVTableMixin, ArchiversTabMixin)


class ArchiveViewer(Display, PVTableMixin, ArchiversTabMixin):
    def __init__(self, parent=None, args=None, macros=None, ui_filename=None):
        ui_filename=__file__.replace(".py", ".ui")
        super(ArchiveViewer, self).__init__(parent=parent, args=args,
                                            macros=macros, ui_filename=ui_filename)

        # self.ui.archiver_select_cmbx.addItems(archiver_urls)

        self.ui.archiver_plot.setAxisColor(QColor(Qt.black))
        self.ui.archiver_plot.setBackgroundColor(QColor(Qt.white))

        self.pv_names_to_plot = set()

        self.pv_table_init()
        self.archivers_tab_init()
