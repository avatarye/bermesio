import os
from pathlib import Path
import sys

import packaging.version

from commons.color import *


class Config:
    """A static class that stores the configuration of the application and related functions."""

    app_name = 'Bermesio'
    app_subtitle = 'Ultimate Blender Manager'
    app_version = packaging.version.parse('0.1.0')
    app_last_update = '2024.01.10'

    default_repo_dir = Path(os.path.expanduser('~')) / f'.{app_name.lower()}'
    # The directory where the repository is stored. User can change this. The new path will be stored in QSettings and
    # loaded from there to override this value when the application is launched.
    repo_dir = default_repo_dir

    dill_extensions = {
        'Profile': '.dpr',
        'BlenderSetup': '.dst',
        'BlenderProgram': '.dbp',
        'BlenderVenv': '.dbv',
        'BlenderAddon': '.dao',
        'BlenderReleasedAddon': '.dra',
        'BlenderDevAddon': '.dda',
        'BlenderScript': '.dbs',
        'BlenderReleasedScript': '.drs',
        'BlenderDevScript': '.dds',
        'PythonDevLibrary': '.dpl',
    }

    resources_paths = {
        'font_dir': 'res/fonts',
        'icon_dir': 'res/icons',
        'icons': {
            '32': 'res/icons/Bermesio_Logo_32.png',
            '64': 'res/icons/Bermesio_Logo_64.png',
            '128': 'res/icons/Bermesio_Logo_128.png',
            '256': 'res/icons/Bermesio_Logo_256.png',
            '512': 'res/icons/Bermesio_Logo_512.png',
            '1024': 'res/icons/Bermesio_Logo_1024.png',
        },
        'banner': 'res/icons/Bermesio_Banner.png',
        'qss': 'res/stylesheets/global_style.qss',
        'blender_logo': 'res/icons/Blender_Logo.svg',
    }

    font_settings = {
        'glyph_icon_font': 'JetBrainsMono NFP',
        'note_font': 'JetBrainsMono NFP',
        'title_font': 'Open Sans SemiCondensed',
        'button_font': 'Open Sans SemiCondensed',
        'label_font': 'Open Sans SemiCondensed',
        'input_font': 'Open Sans',
    }

    component_settings = {
        'Default': {
            'name': 'Default',
            'button_text': 'DEFAULT',
            'display_text': 'Default',
            'color': BColors.sub_text.value,
            'icon_char': '\U000f07e2',
            'table_item_size_hint': (30, 30),
        },
        'Profile': {
            'name': 'profile',
            'button_text': 'PROFILES',
            'display_text': 'Profile',
            'color': BColors.profile.value,
            'icon_char': '\U000f0004',
            'table_item_size_hint': (200, 90),
        },
        'BlenderSetup': {
            'name': 'blender_setup',
            'button_text': 'SETUPS',
            'display_text': 'Blender Setup',
            'color': BColors.blender_setup.value,
            'icon_char': '\U000f01d6',
            'table_item_size_hint': (200, 130),
        },
        'BlenderProgram': {
            'name': 'blender_program',
            'button_text': 'BLENDERS',
            'display_text': 'Blender',
            'color': BColors.blender_program.value,
            'icon_char': '\U000f00ab',
            'table_item_size_hint': (200, 80),
        },
        'BlenderReleasedAddon': {
            'name': 'blender_release_addon',
            'button_text': 'ADDONS',
            'display_text': 'Blender Addon',
            'color': BColors.blender_released_addon.value,
            'icon_char': '\U000f003c',
            'table_item_size_hint': (200, 80),
        },
        'BlenderReleasedScript': {
            'name': 'blender_release_script',
            'button_text': 'SCRIPTS',
            'display_text': 'Blender Script',
            'color': BColors.blender_released_script.value,
            'icon_char': '\U000f09ee',
            'table_item_size_hint': (200, 60),
        },
        'BlenderVenv': {
            'name': 'blender_venv',
            'button_text': 'VENVS',
            'display_text': 'Blender Venv',
            'color': BColors.blender_venv.value,
            'icon_char': '\U000f0862',
            'table_item_size_hint': (200, 130)
        },
        'BlenderDevAddon': {
            'name': 'blender_dev_addon',
            'button_text': 'DEV ADDONS',
            'display_text': 'Blender ',
            'color': BColors.blender_dev_addon.value,
            'icon_char': '\U000f1754',
            'table_item_size_hint': (200, 80),
        },
        'BlenderDevScript': {
            'name': 'blender_dev_script',
            'button_text': 'DEV SCRIPTS',
            'display_text': 'Blender Dev Script',
            'color': BColors.blender_dev_script.value,
            'icon_char': '\U000f0dc9',
            'table_item_size_hint': (200, 60),
        },
        'PythonDevLibrary': {
            'name': 'python_dev_library',
            'button_text': 'DEV LIBS',
            'display_text': 'Python Dev Library',
            'color': BColors.python_dev_library.value,
            'icon_char': '\U0000e606',
            'table_item_size_hint': (200, 40),
        },
    }

    mime_custom_type_str = 'application/x-bermesio-component'
    drag_drop_objects = {}

    def __new__(cls, *args, **kwargs):
        """Guard against instantiation."""
        raise Exception('Config should not be instantiated.')

    @staticmethod
    def _get_root() -> Path:
        """
        Get the root directory of the application. Check if the application is running in a PyInstaller bundle and
        return the root directory accordingly.
        """
        return Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent

    root_dir: Path = _get_root()

    @classmethod
    def get_dill_extension(cls, component: str) -> str:
        """Get the dill extension of a component class."""
        component_class_name = component.__class__.__name__
        if component_class_name not in cls.dill_extensions:
            for class_ in component.__class__.__bases__:
                if class_.__name__ in cls.dill_extensions:
                    return cls.dill_extensions[class_.__name__]
        return cls.dill_extensions[component_class_name]

    @staticmethod
    def get_component_settings(component_name: str) -> dict:
        """Get the component visual settings of a component."""
        assert component_name in Config.component_settings, f'Invalid component name: {component_name}'
        return Config.component_settings[component_name]
