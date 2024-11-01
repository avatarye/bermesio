from typing import TYPE_CHECKING

import packaging.version
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPainter, QPixmap, QFontMetrics, QIcon
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QTableWidget, QPushButton, QFrame
from PyQt6.QtSvg import QSvgRenderer

from bermesio.config import Config
from bermesio.commons.color import BColors
from bermesio.commons.qt_common import get_blender_logo, get_glyph_icon

if TYPE_CHECKING:
    from components.profile import Profile
    from components.blender_addon import BlenderReleasedAddon, BlenderDevAddon
    from components.blender_program import BlenderProgram
    from components.blender_script import BlenderReleasedScript, BlenderDevScript
    from components.blender_setup import BlenderSetup
    from components.blender_venv import BlenderVenv
    from components.python_dev_library import PythonDevLibrary


class ComponentItemWidget(QWidget):
    """
    A base class for the widget that are used to represent individual component in the grid layout of the widget in
    the stacked widget of the main window.
    """

    safe_string_padding = 8  # Padding to add to the width of the string to make sure it fits in the width
    glyph_icon_font = Config.font_settings['glyph_icon_font']

    main_text_style = (f'font-family: {Config.font_settings["label_font"]}; font-size: 14px; '
                       f'font-weight: bold; color: {BColors.text.value}')
    sub_text_style = (f'font-family: {Config.font_settings["glyph_icon_font"]}; font-size: 12px;'
                      f'font-weight: bold; color: {BColors.sub_text.value}')

    def __init__(self, component, parent=None):
        super().__init__(parent)
        self.component = component
        self._setup_gui()

    def _gen_verification_label(self):
        self.label_verification = QLabel(self)
        if self.component.verify():
            verification_pixmap = QIcon(get_glyph_icon('\U0000f058', self.glyph_icon_font, 'green', 12)).pixmap(12, 12)
        else:
            verification_pixmap = QIcon(get_glyph_icon('\U0000f057', self.glyph_icon_font, 'red', 12)).pixmap(12, 12)
        self.label_verification.setPixmap(verification_pixmap)

    def _gen_name_label(self):
        self.label_name = QLabel(self.component.name)
        self.label_name.setStyleSheet(self.main_text_style)

    def _get_platform_glyph_icon_char(self) -> str:
        if self.component.platform == 'win32':
            return '\U000f05b3'
        elif self.component.platform == 'darwin':
            return '\U0000e711'
        elif self.component.platform == 'linux':
            return '\U000f033d'
        else:
            raise NotImplementedError(f'Platform {self.component.platform} not supported.')

    def _gen_platform_label(self):
        platform_icon = self._get_platform_glyph_icon_char()
        self.label_platform = QLabel(platform_icon)
        self.label_platform.setStyleSheet(self.sub_text_style)

    def _gen_blender_version_label(self, blender_version: packaging.version.Version, with_platform=True):
        if with_platform:
            platform_icon = self._get_platform_glyph_icon_char()
            self.label_blender_version = QLabel(f'\U000f00ab {blender_version} {platform_icon}')
        else:
            self.label_blender_version = QLabel(f'\U000f00ab {blender_version}')
        self.label_blender_version.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; '
                                                 f'font-size: 12px; '
                                                 f'font-weight: bold; color: {BColors.blender_program.value}')

    def _setup_gui(self):
        # Add common layout, including verification icon and name label
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setSpacing(0)
        self.layout_name = QHBoxLayout(self)
        self.layout_name.setContentsMargins(0, 0, 0, 0)
        self.layout_name.setSpacing(2)
        self.layout_name.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._gen_verification_label()
        self._gen_name_label()

        self.layout.addLayout(self.layout_name)
        self.layout_name.addWidget(self.label_verification)
        self.layout_name.addWidget(self.label_name)

    def _get_width_safe_string(self, string, font):
        """Return a string that fits in the given width."""
        max_width = self.parent.setting_dict['table_item_size_hint'][0] - self.safe_string_padding * 2
        metrics = QFontMetrics(font)
        if metrics.horizontalAdvance(string) <= max_width:
            return string
        else:
            return self._get_width_safe_string(string[:-1], font, max_width)


class ProfileItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):
        super().__init__(component, parent=parent)
        self.component: Profile = component

    def _setup_gui(self):
        super()._setup_gui()

        if self.component.blender_setup is None:
            self.label_blender_setups = QLabel(f'{Config.component_settings["BlenderSetup"]["icon_char"]} '
                                               f'not set')
        else:
            self.label_blender_setups = QLabel(f'{Config.component_settings["BlenderSetup"]["icon_char"]} '
                                               f'{self.component.blender_setup.name}')
        self.label_blender_setups.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; '
                                                f'font-size: 12px;' f'font-weight: bold; '
                                                f'color: {Config.component_settings["BlenderSetup"]["color"]}')
        if self.component.blender_program is None:
            self.label_blender_programs = QLabel(f'{Config.component_settings["BlenderProgram"]["icon_char"]} '
                                                 f'not set')
        else:
            self.label_blender_programs = QLabel(f'{Config.component_settings["BlenderProgram"]["icon_char"]} '
                                                 f'{self.component.blender_program.name} '
                                                 f'{self._get_platform_glyph_icon_char()}')
        self.label_blender_programs.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; '
                                                  f'font-size: 12px;' f'font-weight: bold; '
                                                  f'color: {Config.component_settings["BlenderProgram"]["color"]}')
        if self.component.blender_venv is None:
            self.label_blender_venvs = QLabel(f'{Config.component_settings["BlenderVenv"]["icon_char"]} '
                                              f'not set')
        else:
            self.label_blender_venvs = QLabel(f'{Config.component_settings["BlenderVenv"]["icon_char"]} '
                                              f'{self.component.blender_venv.name}')
        self.label_blender_venvs.setStyleSheet(f'font-family: {Config.font_settings["glyph_icon_font"]}; '
                                               f'font-size: 12px;' f'font-weight: bold; '
                                               f'color: {Config.component_settings["BlenderVenv"]["color"]}')

        self.layout.addWidget(self.label_blender_programs)
        self.layout.addWidget(self.label_blender_setups)
        self.layout.addWidget(self.label_blender_venvs)


class BlenderSetupItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):

        super().__init__(component, parent=parent)
        self.component: BlenderSetup = component

    def _setup_gui(self):
        super()._setup_gui()
        status_dict = self.component.status_dict

        self.label_released_addons = QLabel(f'{len(status_dict["released_addons"])} addons')
        self.label_dev_addons = QLabel(f'{len(status_dict["released_addons"])} dev addons')
        released_script_num = (len(status_dict["startup_scripts"]) +
                               len(status_dict["regular_scripts"]))
        self.label_released_scripts = QLabel(f'{released_script_num} scripts')
        dev_script_num = (len(status_dict["dev_startup_scripts"]) +
                          len(status_dict["dev_regular_scripts"]))
        self.label_dev_scripts = QLabel(f'{dev_script_num} dev scripts')
        config_icon = '\U0000f058' if status_dict.get('has_blender_config', False) else '\U0000f057'
        self.label_blender_config = QLabel(f'{config_icon} user config')
        for label in [self.label_released_addons, self.label_dev_addons, self.label_released_scripts,
                      self.label_dev_scripts, self.label_blender_config]:
            label.setStyleSheet(self.sub_text_style)

        self.layout.addWidget(self.label_released_addons)
        self.layout.addWidget(self.label_released_scripts)
        self.layout.addWidget(self.label_dev_addons)
        self.layout.addWidget(self.label_dev_scripts)
        self.layout.addWidget(self.label_blender_config)


class BlenderProgramItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):

        super().__init__(component, parent=parent)
        self.component: BlenderProgram = component

    def _setup_gui(self):
        super()._setup_gui()
        self._gen_blender_version_label(self.component.blender_version, with_platform=True)
        self.label_python = QLabel(f'\U0000e606 {self.component.python_version}')
        self.label_python.setStyleSheet(self.sub_text_style)

        self.layout.addWidget(self.label_blender_version)
        self.layout.addWidget(self.label_python)


class BlenderVenvItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):

        super().__init__(component, parent=parent)
        self.component: BlenderVenv = component

    def _setup_gui(self):
        super()._setup_gui()
        status_dict = self.component.status_dict

        self._gen_blender_version_label(self.component.blender_program.blender_version, with_platform=True)
        self.label_python = QLabel(f'\U0000e606 {self.component.blender_program.python_version}')
        self.label_python.setStyleSheet(self.sub_text_style)
        self.label_site_packages = QLabel(f'{len(status_dict["site_packages"])} site packages')
        self.label_dev_libraries = QLabel(f'{len(status_dict.get("dev_libraries", []))} dev libraries')
        bpy_icon = '\U0000f058' if status_dict.get('has_bpy_package', False) else '\U0000f057'
        self.label_bpy_package = QLabel(f'{bpy_icon} bpy package')
        for label in [self.label_python, self.label_bpy_package, self.label_dev_libraries, self.label_site_packages]:
            label.setStyleSheet(self.sub_text_style)

        self.layout.addWidget(self.label_blender_version)
        self.layout.addWidget(self.label_python)
        self.layout.addWidget(self.label_site_packages)
        self.layout.addWidget(self.label_dev_libraries)
        self.layout.addWidget(self.label_bpy_package)


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

        super()._setup_gui()
        self._gen_blender_version_label(self.component.blender_version_min, with_platform=False)
        self.label_version = QLabel(f'\U0000f454 {self.component.version}')
        self.label_version.setStyleSheet(self.sub_text_style)

        self.layout.addWidget(self.label_version)
        self.layout.addWidget(self.label_blender_version)


class BlenderReleasedScriptItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):
       super().__init__(component, parent=parent)
       self.component: BlenderReleasedScript = component

    def _setup_gui(self):
        super()._setup_gui()
        if self.component.__class__.__name__ == 'BlenderRegularScript':
            self.label_type = QLabel(f'\U000f0477 Regular Script')
        elif self.component.__class__.__name__ == 'BlenderStartupScript':
            self.label_type = QLabel(f'\U000f0bc2 Startup Script')
        else:
            raise NotImplementedError(f'Component {self.component} not supported.')
        self.label_type.setStyleSheet(self.sub_text_style)

        self.layout.addWidget(self.label_type)


class BlenderDevAddonItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):
        super().__init__(component, parent=parent)
        self.component: BlenderDevAddon = component

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

        super()._setup_gui()
        self._gen_blender_version_label(self.component.blender_version_min, with_platform=False)
        self.label_version = QLabel(f'\U0000f454 {self.component.version}')
        self.label_version.setStyleSheet(self.sub_text_style)

        self.layout.addWidget(self.label_version)
        self.layout.addWidget(self.label_blender_version)



class BlenderDevScriptItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):
        super().__init__(component, parent=parent)
        self.component: BlenderDevScript = component

    def _setup_gui(self):
        super()._setup_gui()
        if self.component.__class__.__name__ == 'BlenderDevRegularScript':
            self.label_type = QLabel(f'\U000f0477 Regular Script')
        elif self.component.__class__.__name__ == 'BlenderDevStartupScript':
            self.label_type = QLabel(f'\U000f0bc2 Startup Script')
        else:
            raise NotImplementedError(f'Component {self.component} not supported.')
        self.label_type.setStyleSheet(self.sub_text_style)

        self.layout.addWidget(self.label_type)


class PythonDevLibraryItemWidget(ComponentItemWidget):

    def __init__(self, component, parent=None):
        super().__init__(component, parent=parent)
        self.component: PythonDevLibrary = component


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
