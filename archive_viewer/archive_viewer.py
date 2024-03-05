from qtpy.QtGui import QColor
from qtpy.QtCore import Qt
from pydm import Display
from mixins import (TracesTableMixin, AxisTableMixin, ArchiversTabMixin)


class ArchiveViewer(Display, TracesTableMixin, AxisTableMixin, ArchiversTabMixin):
    def __init__(self, parent=None, args=None, macros=None, ui_filename=__file__.replace(".py", ".ui")):
        super(ArchiveViewer, self).__init__(parent=parent, args=args,
                                            macros=macros, ui_filename=ui_filename)

        self.ui.main_spltr.setCollapsible(0, False)
        self.ui.main_spltr.setStretchFactor(0, 1)

        self.axis_table_init()
        self.traces_table_init()
        self.archivers_tab_init()

        self.curve_delegates_init()
        self.axis_delegates_init()
