from qtpy.QtGui import QColor
from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import QWidget, QLineEdit, QVBoxLayout

from pydm.widgets.archiver_time_plot import TimePlotCurveItem, PyDMArchiverTimePlot

from widgets import ColorButton, SettingsTitle, ComboBoxWrapper, SettingsRowItem


class CurveSettingsModal(QWidget):
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

    def show(self):
        parent_pos = self.parent().rect().bottomRight()
        global_pos = self.parent().mapToGlobal(parent_pos)
        self.move(global_pos)
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

    @Slot(object)
    def set_curve_type(self, curve_type: str | None):
        self.curve.stepMode = curve_type

    @Slot(object)
    def set_curve_style(self, style: int):
        self.curve.lineStyle = style

    @Slot(object)
    def set_curve_width(self, width: int):
        self.curve.lineWidth = width

    @Slot(object)
    def set_symbol_shape(self, shape: str):
        self.curve.symbol = shape

    @Slot(object)
    def set_symbol_size(self, size: int):
        self.curve.symbolSize = size
