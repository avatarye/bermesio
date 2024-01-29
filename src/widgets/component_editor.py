from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPixmap, QColor, QPen
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy

from commons.color import BColors
from commons.qt_common import get_app_icon_path, LabelVerticalBar
from commons.qt_singal import SIGNAL
from components.repository import Repository
from config import Config
from widgets.button import ComponentOpsButton
from widgets.component_table import ComponentTableWidget


class ComponentEditorDropWidget(QWidget):

    def __init__(self, parent_editor, component_class_name):
        super().__init__(parent_editor)
        self.parent_editor = parent_editor
        self.component_class_name = component_class_name
        self.component_display_type = Config.component_settings[self.component_class_name]['display_text']
        self.component_color = Config.component_settings[self.component_class_name]['color']
        self.component = None
        self.setAcceptDrops(True)
        self.setFixedHeight(130)

        self._setup_gui()

    def _setup_gui(self):
        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.label_empty_component = QLabel(f'Drop a {self.component_display_type} here', parent=self)
        self.label_empty_component.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_empty_component.setStyleSheet(f'border: 0px; background: transparent; color: {BColors.text.value};'
                                                 f'font-family: {Config.font_settings["input_font"]}; font-size: 13px;'
                                                 f'font-weight: normal')

        self.setLayout(self.vlayout)
        self.vlayout.addWidget(self.label_empty_component)

    def _get_component_from_mime_data(self, mime_data):
        # Get the component uuid from the mime data, then retrieve the component from the Config.drag_drop_objects dict
        component = None
        if mime_data.hasFormat(Config.mime_custom_type_str):
            uuid = mime_data.data(Config.mime_custom_type_str).data().decode()
            if uuid in Config.drag_drop_objects:
                component = Config.drag_drop_objects[uuid]
        return component

    def dragEnterEvent(self, event):
        component = self._get_component_from_mime_data(event.mimeData())
        if component is not None and component.__class__.__name__ == self.component_class_name:
            self.component = component
            event.acceptProposedAction()

    def dropEvent(self, event):
        component = self._get_component_from_mime_data(event.mimeData())
        if component is not None and component.__class__.__name__ == self.component_class_name:
            self.component = component
            del Config.drag_drop_objects[component.uuid]
            event.acceptProposedAction()

    def paintEvent(self, event):
        # super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(0.05)
        painter.fillRect(self.rect(), QColor(self.component_color))
        painter.setOpacity(0.2)
        selection_pen = QPen(QColor(BColors.sub_text.value))
        selection_pen.setWidth(2)
        selection_pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(selection_pen)
        painter.drawRect(QRect(1, 1, self.rect().width() - 2, self.rect().height() - 2))
        painter.end()


class ComponentEditor(QWidget):

    def __init__(self, component_class_name, parent=None):
        super().__init__(parent)
        self.component_class_name = component_class_name
        self.component_setting_dict = Config.component_settings[self.component_class_name]
        self.name = self.component_setting_dict['name']
        self.setObjectName(f'MainWindowComponentEditor{self.name.title()}')
        self.color = self.component_setting_dict['color']

        self.sub_text_style = (f'font-family: {Config.font_settings["note_font"]}; font-size: 12px;'
                               f'font-weight: normal; border: 0px; background: transparent;')
        self.small_text_style = (f'font-family: {Config.font_settings["note_font"]}; font-size: 10px;'
                               f'font-weight: bold; border: 0px; background: transparent;')
        self.name_text_style = (f'font-family: {Config.font_settings["title_font"]}; font-size: 20px; '
                                f'color: {self.color}; font-weight: bold; border: 0px; background: transparent;')

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
        central_widget = self.parent().parent().parent().parent().parent()
        pos_in_central_widget = self.mapTo(central_widget, self.pos())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(0.05)
        pixmap = QPixmap(str(get_app_icon_path(256)))
        painter.drawPixmap(int(central_widget.rect().width() / 2 - pixmap.width() / 2),
                           int(central_widget.rect().height() / 2 - pixmap.height() / 2)
                           - pos_in_central_widget.y() + 20, pixmap)
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
        self.label_click_icon.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; font-size: 40px;'
                                            f'border: 0px;' f'font-weight: normal; color: {BColors.sub_text.value};'
                                            f'background: transparent;')
        self.label_note = QLabel('Please double click on a Profile, Setup, or Venv item to edit.\n'
                                 'Tips: You can drag and drop a valid file or directory from the OS\n'
                                 'file manager into any of the tables above.', parent=self)
        self.label_note.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.label_note.setStyleSheet(self.sub_text_style)

        self.hlayout.addWidget(self.label_vertical_bar)
        self.hlayout.addLayout(layout_labels)
        layout_labels.addWidget(self.label_click_icon)
        layout_labels.addWidget(self.label_note)

    def load_component(self, component):
        if component is None:
            self.parent().setCurrentWidget(self)


class ProfileEditor(ComponentEditor):

    def __init__(self, parent=None):
        super().__init__('Profile', parent)

    def _setup_gui(self):
        super()._setup_gui()

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(4, 0, 0, 0)
        vlayout.setSpacing(4)
        label_editor_type = QLabel('A Profile consists of three components: a Blender program, a Setup, and an '
                                   'optional Venv. You can launch Blender in the usual window mode or the Venv in the '
                                   'command line window. Additionally, you can adjust the launch options here.',
                                   parent=self)
        label_editor_type.setWordWrap(True)
        label_editor_type.setStyleSheet(self.small_text_style)
        label_editor_type.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.label_component_name = QLabel('name', parent=self)
        self.label_component_name.setStyleSheet(self.name_text_style)
        self.hlayout_components = QHBoxLayout(self)
        self.hlayout_components.setSpacing(4)
        self.drop_widget_blender_program = ComponentEditorDropWidget(self, 'BlenderProgram')
        self.drop_widget_blender_setup = ComponentEditorDropWidget(self, 'BlenderSetup')
        self.drop_widget_blender_venv = ComponentEditorDropWidget(self, 'BlenderVenv')
        label_launch_blender = QLabel('Launch Blender', parent=self)

        self.hlayout.addLayout(vlayout)
        vlayout.addWidget(label_editor_type)
        vlayout.addWidget(self.label_component_name)
        vlayout.addLayout(self.hlayout_components)
        self.hlayout_components.addWidget(self.drop_widget_blender_program)
        self.hlayout_components.addWidget(self.drop_widget_blender_setup)
        self.hlayout_components.addWidget(self.drop_widget_blender_venv)
        vlayout.addWidget(label_launch_blender)
        vlayout.addStretch()

    def load_component(self, component):
        if component.__class__.__name__ == self.component_class_name:
            self.component = component
            self.label_component_name.setText(self.component.name)
            self.parent().setCurrentWidget(self)


class BlenderSetupEditor(ComponentEditor):
    def __init__(self, parent=None):
        super().__init__('BlenderSetup', parent)

    def _setup_gui(self):
        super()._setup_gui()

        vlayout = QVBoxLayout(self)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)
        label_editor_type = QLabel('Setup Editor', parent=self)
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

class BlenderVenvEditor(ComponentEditor):
    def __init__(self, parent=None):
        super().__init__('BlenderVenv', parent)

    def load_component(self, component):
        if component.__class__.__name__ == self.component_class_name:
            self.parent().setCurrentWidget(self)
