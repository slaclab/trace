from config import archiver_urls, logger
from widgets import ArchiversTableDelegate
from table_models import ArchiversTableModel


class ArchiversTabMixin:
    def archivers_tab_init(self):
        self.archivers_table_model = ArchiversTableModel(self, archiver_urls)
        self.ui.archivers_tbl.setModel(self.archivers_table_model)

        self.archivers_delegate = ArchiversTableDelegate(self.ui.archivers_tbl)
        self.ui.archivers_tbl.setItemDelegateForColumn(0, self.archivers_delegate)

        self.ui.add_archiver_btn.clicked.connect(self.archivers_table_model.add_empty_row)
