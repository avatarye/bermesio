from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPainter, QPixmap
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel

from commons.qt_common import get_app_icon_path
from widgets.button import ComponentOpsButton
from widgets.component_table import ComponentTableWidget


class ComponentLabel(QLabel):

    def __init__(self, text, color, glyph_icon=None, parent=None):
        super().__init__(parent)
        self.setText(text.upper())
        self.color = color
        self.glyph_icon = glyph_icon
        self.setFixedWidth(4)

        self.text_font = QFont("JetBrainsMono NFP", 20)
        self.text_font.setWeight(300)
        self.setStyleSheet('border: 1px solid red;')

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self.color))
        # painter.setPen(QColor(self.color))
        #
        # painter.setFont(self.text_font)
        # painter.translate(self.rect().center())
        # painter.rotate(90)
        # painter.drawText(-80, 10, self.text())
        painter.end()


class ComponentWindowWidget(QWidget):
    """A base class for the widget that are used in the stacked widget of the main window."""

    def __init__(self, setting_dict, sub_repo, parent=None):
        super().__init__(parent)
        self.setting_dict = setting_dict
        self.name = setting_dict['name']
        self.setObjectName(f'MainWindowComponentWidget{self.name.title()}')
        self.color = setting_dict['color']
        self.sub_repo = sub_repo

        self._setup_gui()

    def _setup_gui(self):
        self.hlayout = QHBoxLayout(self)
        self.hlayout.setContentsMargins(4, 4, 4, 4)
        self.hlayout.setSpacing(4)
        # self.component_label = ComponentLabel(self.name, self.color, parent=self)
        # self.component_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.component_table = ComponentTableWidget(self.setting_dict, self.sub_repo, parent=self)
        self.vlayout_buttons = QVBoxLayout(self)
        self.vlayout_buttons.setSpacing(4)
        self.pushbutton_add = ComponentOpsButton('\U000f0704', self.color, parent=self)
        self.pushbutton_add.setToolTip('Add')
        self.pushbutton_duplicate = ComponentOpsButton('\U0000f4c4', self.color, parent=self)
        self.pushbutton_duplicate.setToolTip('Duplicate')
        self.pushbutton_rename = ComponentOpsButton('\U0000f45a', self.color, parent=self)
        self.pushbutton_rename.setToolTip('Rename')
        self.pushbutton_delete = ComponentOpsButton('\U000f17c3', self.color, parent=self)
        self.pushbutton_delete.setToolTip('Delete')

        self.setLayout(self.hlayout)
        # self.hlayout.addWidget(self.component_label)
        self.hlayout.addWidget(self.component_table)
        self.hlayout.addLayout(self.vlayout_buttons)
        self.vlayout_buttons.addWidget(self.pushbutton_add)
        self.vlayout_buttons.addWidget(self.pushbutton_duplicate)
        self.vlayout_buttons.addWidget(self.pushbutton_rename)
        self.vlayout_buttons.addWidget(self.pushbutton_delete)
        self.vlayout_buttons.addStretch()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Draw the logo as background
        painter.setOpacity(0.05)
        # painter.fillRect(self.rect(), QColor(self.color))
        pixmap = QPixmap(str(get_app_icon_path(256)))
        painter.drawPixmap(int(self.rect().width() / 2 - pixmap.width() / 2),
                           int(self.rect().height() / 2 - pixmap.height() / 2) - 10,
                           pixmap)
        painter.end()
