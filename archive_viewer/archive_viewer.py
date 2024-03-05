from qtpy.QtGui import QColor
from qtpy.QtCore import Qt
from pydm import Display
from mixins import (TracesTableMixin, AxisTableMixin, ArchiversTabMixin)


class ArchiveViewer(Display, TracesTableMixin, AxisTableMixin, ArchiversTabMixin):
        super(ArchiveViewer, self).__init__(parent=parent, args=args,
                                            macros=macros, ui_filename=ui_filename)

        # self.ui.archiver_select_cmbx.addItems(archiver_urls)

        self.axis_table_init()
        self.traces_table_init()
        self.archivers_tab_init()

        self.curve_delegates_init()
        self.axis_delegates_init()
