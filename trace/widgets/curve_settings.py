from qtpy.QtGui import QColor
from qtpy.QtCore import Qt, Slot, Signal
from qtpy.QtWidgets import QWidget, QCheckBox, QLineEdit, QVBoxLayout

from pydm.widgets.archiver_time_plot import TimePlotCurveItem, PyDMArchiverTimePlot

from config import logger
from widgets import ColorButton, SettingsTitle, ComboBoxWrapper, SettingsRowItem


class CurveSettingsModal(QWidget):
    color_changed = Signal(object)

    def __init__(self, parent: QWidget, plot: PyDMArchiverTimePlot, curve: TimePlotCurveItem):
        super().__init__(parent)
        self.setWindowFlag(Qt.Popup)

        self.legend = plot._legend
        self.curve = curve
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        title_label = SettingsTitle(self, "Curve Settings", size=14)
        main_layout.addWidget(title_label)

        name_edit = QLineEdit(curve.name(), self)
        name_edit.editingFinished.connect(self.set_curve_name)
        name_row = SettingsRowItem(self, "Curve Name", name_edit)
        main_layout.addLayout(name_row)

        color_button = ColorButton(parent=self, color=curve.color_string)
        color_button.color_changed.connect(self.set_curve_color)
        color_row = SettingsRowItem(self, "Color", color_button)
        main_layout.addLayout(color_row)

        self.bin_count_line_edit = bin_count_line_edit = QLineEdit()
        bin_count_line_edit.setMaximumWidth(65)
        bin_count_line_edit.returnPressed.connect(self.set_curve_data_bins)
        optimized_bin_count = SettingsRowItem(self, "Optimized bin count", bin_count_line_edit)
        bin_count = curve.optimized_data_bins
        if not bin_count:
            bin_count = plot.optimized_data_bins
        bin_count_line_edit.setPlaceholderText(str(bin_count))
        main_layout.addLayout(optimized_bin_count)

        self.live_toggle = QCheckBox("")
        self.live_toggle.setCheckState(Qt.Checked if self.curve.liveData else Qt.Unchecked)
        self.live_toggle.stateChanged.connect(self.set_live_data_connection)
        live_toggle_row = SettingsRowItem(self, "Connect to Live", self.live_toggle)
        main_layout.addLayout(live_toggle_row)

        self.archive_toggle = QCheckBox("")
        self.archive_toggle.setCheckState(Qt.Checked if self.curve.use_archive_data else Qt.Unchecked)
        self.archive_toggle.stateChanged.connect(self.set_archive_data_connection)
        archive_toggle_row = SettingsRowItem(self, "Connect to Archive", self.archive_toggle)
        main_layout.addLayout(archive_toggle_row)

        line_title_label = SettingsTitle(self, "Line")
        main_layout.addWidget(line_title_label)

        init_curve_type = "Step" if curve.stepMode in ["left", "right", "center"] else "Direct"
        type_combo = ComboBoxWrapper(self, {"Direct": None, "Step": "right"}, init_curve_type)
        type_combo.text_changed.connect(self.set_curve_type)
        type_row = SettingsRowItem(self, "  Type", type_combo)
        main_layout.addLayout(type_row)

        style_combo = ComboBoxWrapper(self, TimePlotCurveItem.lines, curve.lineStyle)
        style_combo.text_changed.connect(self.set_curve_style)
        style_row = SettingsRowItem(self, "  Style", style_combo)
        main_layout.addLayout(style_row)

        width_options = {f"{i}px": i for i in range(1, 6)}
        width_combo = ComboBoxWrapper(self, width_options, curve.lineWidth)
        width_combo.text_changed.connect(self.set_curve_width)
        width_row = SettingsRowItem(self, "  Width", width_combo)
        main_layout.addLayout(width_row)

        extention_option = QCheckBox(self)
        extention_option.stateChanged.connect(lambda check: self.set_extension_option(bool(check)))
        extention_option_row = SettingsRowItem(self, "Line Extention", extention_option)
        main_layout.addLayout(extention_option_row)

        symbol_title_label = SettingsTitle(self, "Symbol")
        main_layout.addWidget(symbol_title_label)

        shape_combo = ComboBoxWrapper(self, TimePlotCurveItem.symbols, curve.symbol)
        shape_combo.text_changed.connect(self.set_symbol_shape)
        shape_row = SettingsRowItem(self, "  Shape", shape_combo)
        main_layout.addLayout(shape_row)

        size_options = {f"{i}px": i for i in range(5, 26, 5)}
        size_combo = ComboBoxWrapper(self, size_options, curve.symbolSize)
        size_combo.text_changed.connect(self.set_symbol_size)
        size_row = SettingsRowItem(self, "  Size", size_combo)
        main_layout.addLayout(size_row)

    def set_curve_data_bins(self):
        n_bins = self.bin_count_line_edit.text()
        if not n_bins.isdigit() or int(n_bins) < 1:
            self.bin_count_line_edit.setStyleSheet("border: 2px solid #d32f2f")
            logger.warning("Invalid bin count entered. Please enter a postive integer.")
            return
        else:
            self.bin_count_line_edit.setStyleSheet("")
        try:
            n_bins = int(n_bins)
            self.curve.setOptimizedDataBins(n_bins)
            self.bin_count_line_edit.setPlaceholderText(str(n_bins))
        except (AttributeError, ValueError) as e:
            logger.warning(f"Unable to set data bins: {e}")

    def set_live_data_connection(self, state: Qt.CheckState) -> None:
        self.curve.liveData = state == Qt.Checked

    def set_archive_data_connection(self, state: Qt.CheckState) -> None:
        self.curve.use_archive_data = state == Qt.Checked

    def show(self):
        parent_pos = self.parent().rect().bottomRight()
        global_pos = self.parent().mapToGlobal(parent_pos)
        self.move(global_pos)
        self.bin_count_line_edit.setStyleSheet("")
        self.bin_count_line_edit.setText("")
        super().show()

    @Slot()
    def set_curve_name(self):
        sender = self.sender()
        name = sender.text()

        if not name:
            sender.blockSignals(True)
            sender.setText(self.curve.name())
            sender.blockSignals(False)
        elif name != self.curve.name():
            legend_label = self.legend.getLabel(self.curve)
            legend_label.setText(name)

            x, y = self.curve.getData()
            self.curve.setData(name=name, x=x, y=y)

    @Slot(QColor)
    def set_curve_color(self, color: QColor):
        self.curve.color = color
        self.color_changed.emit(color)

    @Slot(object)
    def set_curve_type(self, curve_type: str | None = None) -> None:
        self.curve.stepMode = curve_type

    @Slot(object)
    def set_curve_style(self, style: int) -> None:
        self.curve.lineStyle = style

    @Slot(object)
    def set_curve_width(self, width: int) -> None:
        self.curve.lineWidth = width

    @Slot(object)
    def set_symbol_shape(self, shape: str) -> None:
        self.curve.symbol = shape

    @Slot(object)
    def set_symbol_size(self, size: int) -> None:
        self.curve.symbolSize = size

    @Slot(object)
    def set_extension_option(self, enable: bool) -> None:
        """Set the line extension based on the checkbox state."""
        self.curve.show_extension_line = enable
        self.curve.getViewBox().addItem(self.curve._extension_line)
        self.curve.redrawCurve()
