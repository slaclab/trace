from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import (
    QLabel,
    QDialog,
    QWidget,
    QCheckBox,
    QLineEdit,
    QTextEdit,
    QListWidget,
    QMessageBox,
    QSizePolicy,
    QVBoxLayout,
    QDialogButtonBox,
)
from trace.services.elog_client import get_logbooks

from trace.widgets.settings_components import SettingsTitle, SettingsRowItem


class ElogPostModal(QDialog):
    def __init__(
        self,
        parent: QWidget = None,
        image_bytes: bytes | None = None,
    ):
        super().__init__(parent)

        self.setModal(True)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        modal_label = SettingsTitle(self, "New Elog Entry", size=14)
        main_layout.addWidget(modal_label)

        if image_bytes is not None:
            pixmap = QPixmap()
            pixmap.loadFromData(image_bytes)
            image_label = QLabel()
            image_label.setPixmap(pixmap)
            image_label.setScaledContents(True)
            image_label.setFixedSize(400, 300)
            main_layout.addWidget(image_label)

        self.title_edit = QLineEdit(self)
        self.title_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.title_edit.setMinimumWidth(250)
        title_row = SettingsRowItem(self, "Title\n(required)", self.title_edit)
        main_layout.addLayout(title_row)

        self.body_edit = QTextEdit(self)
        body_row = SettingsRowItem(self, "Body\n(optional)", self.body_edit)
        main_layout.addLayout(body_row)

        self.logbook_list = QListWidget(self)
        self.logbook_list.setSelectionMode(QListWidget.MultiSelection)
        logbook_row = SettingsRowItem(self, "Logbooks\n(required)", self.logbook_list)
        main_layout.addLayout(logbook_row)

        self.logbook_readback = QLabel()
        self.logbook_readback.setWordWrap(True)
        self.logbook_readback.setMinimumWidth(250)
        self.logbook_readback.setMaximumWidth(350)
        logbook_readback_row = SettingsRowItem(self, "Selected Logbooks", self.logbook_readback)
        self.logbook_list.itemSelectionChanged.connect(
            lambda: self.logbook_readback.setText(", ".join(item.text() for item in self.logbook_list.selectedItems()))
        )
        main_layout.addLayout(logbook_readback_row)

        self.attach_config_checkbox = QCheckBox(self)
        attach_config_row = SettingsRowItem(self, "Attach Config", self.attach_config_checkbox)
        main_layout.addLayout(attach_config_row)

        buttons = QDialogButtonBox()
        send_button = buttons.addButton("Send", QDialogButtonBox.AcceptRole)
        cancel_button = buttons.addButton(QDialogButtonBox.Cancel)

        cancel_button.clicked.connect(self.reject)
        send_button.clicked.connect(self.on_submit)
        main_layout.addWidget(buttons)

    def on_submit(self) -> None:
        """
        Handles the submission of the dialog. This method is called when the user clicks the 'Send' button.
        It retrieves the inputs, validates, and closes the dialog.
        """
        title, _, logbooks, _ = self.get_inputs()
        if not title:
            QMessageBox.warning(self, "Input Error", "Title is required.")
            return
        if not logbooks:
            QMessageBox.warning(self, "Input Error", "At least one logbook must be selected.")
            return

        self.accept()

    def get_inputs(self) -> tuple[str, str, list[str], bool]:
        """
        Returns the inputs from the dialog as a tuple of (title, body, logbooks, attach_config).
        """
        title = self.title_edit.text().strip()
        body = self.body_edit.toPlainText().strip()
        logbooks = [item.text() for item in self.logbook_list.selectedItems()]
        attach_config = self.attach_config_checkbox.isChecked()
        return title, body, logbooks, attach_config

    @classmethod
    def maybe_create(cls, parent: QWidget = None, image_bytes: bytes | None = None) -> "ElogPostModal | None":
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

        modal = cls(parent, image_bytes=image_bytes)
        modal.logbook_list.addItems(logbooks)
        return modal
