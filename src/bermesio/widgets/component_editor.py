from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPixmap, QFont
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel

from bermesio.commons.color import BColors
from bermesio.commons.qt_common import get_app_icon_path, LabelVerticalBar
from bermesio.commons.qt_singal import SIGNAL
from bermesio.components.repository import Repository
from bermesio.config import Config
from bermesio.widgets.button import ComponentOpsButton
from bermesio.widgets.component_table import ComponentTableWidget


class ComponentEditor(QWidget):

    def __init__(self, component_class_name, parent=None):
        super().__init__(parent)
        self.component_class_name = component_class_name
        self.component_setting_dict = Config.component_settings[self.component_class_name]
        self.name = self.component_setting_dict['name']
        self.setObjectName(f'MainWindowComponentEditor{self.name.title()}')
        self.color = self.component_setting_dict['color']

        self.sub_text_style = (f'font-family: {Config.font_settings["note_font"]}; font-size: 12px; font-weight: normal;'
                               f'border: 0px; background: transparent;')

        self._setup_gui()
        self._setup_action()

    def _setup_gui(self):
        # Set up the widgets
        self.hlayout = QHBoxLayout(self)
        self.hlayout.setContentsMargins(4, 4, 4, 4)
        self.hlayout.setSpacing(0)
        self.label_vertical_bar = LabelVerticalBar(self.color, 4, parent=self)
        self.label_vertical_bar.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.hlayout.addWidget(self.label_vertical_bar)

    def _setup_action(self):
        SIGNAL.load_component_in_editor.connect(self.load_component)

    def load_component(self, component):
        ...

    def paintEvent(self, event):
        # Draw the logo as background using the central widget as the reference
        central_widget = self.parent().parent().parent().parent()
        pos_in_central_widget = self.mapTo(central_widget, self.pos())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(0.05)
        pixmap = QPixmap(str(get_app_icon_path(256)))
        painter.drawPixmap(int(central_widget.rect().width() / 2 - pixmap.width() / 2),
                           int(central_widget.rect().height() / 2 - pixmap.height() / 2)
                           - pos_in_central_widget.y() + 20,
                           pixmap)
        painter.end()

class DefaultEditor(ComponentEditor):

    def __init__(self, parent=None):
        super().__init__('Default', parent)

    def _setup_gui(self):
        """
        Set up the GUIs for the default editor, which is different from the other component editors. So it doesn't
        call the super method.
        """
        self.hlayout = QHBoxLayout(self)
        self.hlayout.setContentsMargins(4, 4, 4, 4)
        self.hlayout.setSpacing(0)
        self.label_vertical_bar = LabelVerticalBar(self.color, 4, parent=self)
        self.label_vertical_bar.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_labels = QHBoxLayout(self)
        layout_labels.setContentsMargins(0, 0, 0, 0)
        layout_labels.setSpacing(8)
        layout_labels.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_click_icon = QLabel('\U000f0cfe', parent=self)
        self.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; font-size: 40px; border: 0px;'
                           f'font-weight: normal; color: {BColors.sub_text.value}; background: transparent;')
        self.label_note = QLabel('Please double click on a Profile, Setup, or Venv item to edit.\n'
                                 'Tip: You can drag and drop a valid file or directory from the OS\n'
                                 'file manager into any of the tables above.', parent=self)
        self.label_note.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.label_note.setStyleSheet(self.sub_text_style)

        self.hlayout.addWidget(self.label_vertical_bar)
        self.hlayout.addLayout(layout_labels)
        layout_labels.addWidget(self.label_click_icon)
        layout_labels.addWidget(self.label_note)


class ProfileEditor(ComponentEditor):

    def __init__(self, parent=None):
        super().__init__('Profile', parent)

    def _setup_gui(self):
        super()._setup_gui()

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)
        label_editor_type = QLabel('Profile Editor', parent=self)
        label_editor_type.setStyleSheet(f'font-family: {Config.font_settings["label_font"]}; font-size: 12px; '
                                        f'font-weight: bold; border: 0px;'
                                        f'background: transparent, color: {self.color};')
        label_component_name = QLabel('name', parent=self)

        self.hlayout.addLayout(vlayout)
        vlayout.addWidget(label_editor_type)
        vlayout.addWidget(label_component_name)

    def load_component(self, component):
        if component.__class__.__name__ == self.component_class_name:
            self.parent().setCurrentWidget(self)


class BlenderSetupEditor(ComponentEditor):
    def __init__(self, parent=None):
        super().__init__('BlenderSetup', parent)

    def load_component(self, component):
        if component.__class__.__name__ == self.component_class_name:
            self.parent().setCurrentWidget(self)

class BlenderVenvEditor(ComponentEditor):
    def __init__(self, parent=None):
        super().__init__('BlenderVenv', parent)

    def load_component(self, component):
        if component.__class__.__name__ == self.component_class_name:
            self.parent().setCurrentWidget(self)
