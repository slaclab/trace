from qtpy.QtWidgets import (
    QDialog,
    QWidget,
    QLineEdit,
    QTextEdit,
    QListWidget,
    QMessageBox,
    QVBoxLayout,
    QDialogButtonBox,
    QSizePolicy,
)
from services.elog_client import get_logbooks

from widgets.settings_components import SettingsTitle, SettingsRowItem


class ElogPostModal(QDialog):
    def __init__(
        self,
        parent: QWidget = None,
    ):
        super().__init__(parent)

        self.setModal(True)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        modal_label = SettingsTitle(self, "New Elog Entry", size=14)
        main_layout.addWidget(modal_label)

        self.title_edit = QLineEdit(self)
        self.title_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.title_edit.setMinimumWidth(250)
        title_row = SettingsRowItem(self, "Title", self.title_edit)
        main_layout.addLayout(title_row)

        self.body_edit = QTextEdit(self)
        body_row = SettingsRowItem(self, "Body", self.body_edit)
        main_layout.addLayout(body_row)

        self.logbook_list = QListWidget(self)
        self.logbook_list.setSelectionMode(QListWidget.MultiSelection)
        logbook_row = SettingsRowItem(self, "Logbooks", self.logbook_list)
        main_layout.addLayout(logbook_row)

        buttons = QDialogButtonBox()
        send_button = buttons.addButton("Send", QDialogButtonBox.AcceptRole)
        cancel_button = buttons.addButton(QDialogButtonBox.Cancel)

        cancel_button.clicked.connect(self.reject)
        send_button.clicked.connect(self.accept)
        main_layout.addWidget(buttons)

    def get_inputs(self):
        title = self.title_edit.text().strip()
        body = self.body_edit.toPlainText().strip()
        logbooks = [item.text() for item in self.logbook_list.selectedItems()]
        return title, body, logbooks

    @classmethod
    def maybe_create(cls, parent: QWidget = None) -> "ElogPostModal | None":
        """
        Creates and shows the ElogPostModal dialog if the logbook list can be populated.
        """
        status_code, logbooks = get_logbooks()
        if status_code != 200:
            QMessageBox.critical(
                parent,
                "Elog Access Error",
                f"Unable to fetch logbooks. \n\nError code: {status_code}",
            )
            return None

        modal = cls(parent)
        modal.logbook_list.addItems(logbooks)
        return modal
