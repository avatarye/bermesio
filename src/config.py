import os
from pathlib import Path
import sys

import packaging.version
from PyQt6.QtCore import QSettings


class Config:
    """
    A singleton class that stores the configuration of the application.
    """

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
    }

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
