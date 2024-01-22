from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPainter, QPixmap, QFontMetrics
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QTableWidget, QPushButton, QFrame
from PyQt6.QtSvg import QSvgRenderer

from config import Config
from commons.color import BColors
from commons.qt_common import get_blender_logo

if TYPE_CHECKING:
    from components.blender_addon import BlenderReleasedAddon
    from components.blender_program import BlenderProgram
    from components.blender_script import BlenderReleasedScript


class ComponentItemWidget(QWidget):
    """
    A base class for the widget that are used to represent individual component in the grid layout of the widget in
    the stacked widget of the main window.
    """

    safe_string_padding = 8  # Padding to add to the width of the string to make sure it fits in the width

    def __init__(self, component, parent=None):
        super().__init__(parent)
        self.component = component
        self._setup_gui()

    def _setup_gui(self):

        layout = QHBoxLayout(self)
        layout.addWidget(QLabel(self.component.name))
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _get_width_safe_string(self, string, font):
        """Return a string that fits in the given width."""
        max_width = self.parent.setting_dict['table_item_size_hint'][0] - self.safe_string_padding * 2
        metrics = QFontMetrics(font)
        if metrics.horizontalAdvance(string) <= max_width:
            return string
        else:
            return self._get_width_safe_string(string[:-1], font, max_width)

    def paintEvent(self, event):
        super().paintEvent(event)


class ProfileItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):
        super().__init__(component, parent=parent)
        self.component = component

    def paintEvent(self, event):
        super().paintEvent(event)


class BlenderSetupItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):

        super().__init__(component, parent=parent)
        self.component = component

    def paintEvent(self, event):
        super().paintEvent(event)


class BlenderProgramItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):

        super().__init__(component, parent=parent)
        self.component: BlenderProgram = component

    def _setup_gui(self):
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)
        self.label_blender_logo = QLabel()
        self.label_blender_logo.setPixmap(get_blender_logo(36, format='pixmap'))
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(4, 0, 0, 0)
        info_layout.setSpacing(0)
        self.label_name = QLabel(f'Blender {self.component.blender_version}')
        self.label_name.setStyleSheet(f'font-family: {Config.font_settings["label_font"]}; font-size: 14px; '
                                      f'font-weight: bold; color: {BColors.text.value}')
        if self.component.platform == 'win32':
            platform_icon = '\U000f05b3'
        elif self.component.platform == 'darwin':
            platform_icon = '\U0000e711'
        elif self.component.platform == 'linux':
            platform_icon = '\U000f033d'
        else:
            raise NotImplementedError(f'Platform {self.component.platform} not supported.')
        self.label_python = QLabel(f'{platform_icon} \U0000e606 {self.component.python_version}')
        self.label_python.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; font-size: 12px;'
                                        f'font-weight: bold; color: {BColors.sub_text.value}')
        layout.addWidget(self.label_blender_logo)
        layout.addLayout(info_layout)
        info_layout.addWidget(self.label_name)
        info_layout.addWidget(self.label_python)


class BlenderVenvItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):

        super().__init__(component, parent=parent)
        self.component = component

    def paintEvent(self, event):
        super().paintEvent(event)


class BlenderReleasedAddonItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):
        super().__init__(component, parent=parent)
        self.component: BlenderReleasedAddon = component

    def _setup_gui(self):
        # Set the tooltip to the description of the addon
        self.setToolTip(self.component.description)
        self.setStyleSheet("""
            QToolTip {
                color: #F8F8F2;
                background-color: #272822;
                border: #75715E solid 1px;
                font-family: "Open Sans", sans-serif;
                font-size: 13px;
                padding: 2px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)
        self.label_name = QLabel(self.component.name)
        self.label_name.setStyleSheet(f'font-family: {Config.font_settings["label_font"]}; font-size: 14px; '
                                      f'font-weight: bold; color: {BColors.text.value}')
        self.label_version = QLabel(f'\U0000f454 {self.component.version}')
        self.label_version.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; font-size: 12px;'
                                         f'font-weight: bold; color: {BColors.sub_text.value}')
        self.label_blender_verison = QLabel(f'\U000f00ab {self.component.blender_version_min}')
        self.label_blender_verison.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; '
                                                 f'font-size: 12px; '
                                                 f'font-weight: bold; color: {BColors.blender_program.value}')
        layout.addWidget(self.label_name)
        layout.addWidget(self.label_version)
        layout.addWidget(self.label_blender_verison)


class BlenderReleasedScriptItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):
       super().__init__(component, parent=parent)
       self.component: BlenderReleasedScript = component

    def _setup_gui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)
        self.label_name = QLabel(self.component.name)
        self.label_name.setStyleSheet(f'font-family: {Config.font_settings["label_font"]}; font-size: 14px; '
                                      f'font-weight: bold; color: {BColors.text.value}')
        if self.component.__class__.__name__ == 'BlenderRegularScript':
            self.label_type = QLabel(f'\U000f0477 Regular Script')
        elif self.component.__class__.__name__ == 'BlenderStartupScript':
            self.label_type = QLabel(f'\U000f0bc2 Startup Script')
        self.label_type.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; font-size: 12px; '
                                      f'font-weight: bold; color: {BColors.sub_text.value}')
        layout.addWidget(self.label_name)
        layout.addWidget(self.label_type)


class BlenderDevAddonItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):
        super().__init__(component, parent=parent)
        self.component: BlenderReleasedAddon = component

    def _setup_gui(self):
        # Set the tooltip to the description of the addon
        self.setToolTip(self.component.description)
        self.setStyleSheet("""
            QToolTip {
                color: #F8F8F2;
                background-color: #272822;
                border: #75715E solid 1px;
                font-family: "Open Sans", sans-serif;
                font-size: 13px;
                padding: 2px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)
        self.label_name = QLabel(self.component.name)
        self.label_name.setStyleSheet(f'font-family: {Config.font_settings["label_font"]}; font-size: 14px; '
                                      f'font-weight: bold; color: {BColors.text.value}')
        self.label_version = QLabel(f'\U0000f454 {self.component.version}')
        self.label_version.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; font-size: 12px;'
                                         f'font-weight: bold; color: {BColors.sub_text.value}')
        self.label_blender_verison = QLabel(f'\U000f00ab {self.component.blender_version_min}')
        self.label_blender_verison.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; '
                                                 f'font-size: 12px; '
                                                 f'font-weight: bold; color: {BColors.blender_program.value}')
        layout.addWidget(self.label_name)
        layout.addWidget(self.label_version)
        layout.addWidget(self.label_blender_verison)


class BlenderDevScriptItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):
        super().__init__(component, parent=parent)
        self.component: BlenderReleasedScript = component

    def _setup_gui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)
        self.label_name = QLabel(self.component.name)
        self.label_name.setStyleSheet(f'font-family: {Config.font_settings["label_font"]}; font-size: 14px; '
                                      f'font-weight: bold; color: {BColors.text.value}')
        if self.component.__class__.__name__ == 'BlenderDevRegularScript':
            self.label_type = QLabel(f'\U000f0477 Regular Script')
        elif self.component.__class__.__name__ == 'BlenderDevStartupScript':
            self.label_type = QLabel(f'\U000f0bc2 Startup Script')
        self.label_type.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; font-size: 12px; '
                                      f'font-weight: bold; color: {BColors.sub_text.value}')
        layout.addWidget(self.label_name)
        layout.addWidget(self.label_type)


class PythonDevLibraryItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):
        super().__init__(component, parent=parent)
        self.component = component

    def paintEvent(self, event):
        super().paintEvent(event)


class ComponentItemWidgetManager:

    component_class_mapping = {
        'Profile': ProfileItemWidget,
        'BlenderSetup': BlenderSetupItemWidget,
        'BlenderProgram': BlenderProgramItemWidget,
        'BlenderVenv': BlenderVenvItemWidget,
        'BlenderReleasedAddon': BlenderReleasedAddonItemWidget,
        'BlenderReleasedScript': BlenderReleasedScriptItemWidget,
        'BlenderDevAddon': BlenderDevAddonItemWidget,
        'BlenderDevScript': BlenderDevScriptItemWidget,
        'PythonDevLibrary': PythonDevLibraryItemWidget,
    }

    def __new__(cls):
        raise NotImplementedError('This class cannot be instantiated.')

    @staticmethod
    def create(component, parent):
        """Create a component item widget based on the component type."""
        for class_ in component.__class__.__mro__:
            if class_.__name__ in ComponentItemWidgetManager.component_class_mapping.keys():
                component_item_widget_class = ComponentItemWidgetManager.component_class_mapping[class_.__name__]
                return component_item_widget_class(component, parent)
        raise NotImplementedError(f'Component item widget class not found for component {component}')
