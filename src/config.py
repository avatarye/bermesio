import os
from pathlib import Path

import packaging.version


class Config:
    """
    A singleton class that stores the configuration of the application.
    """

    app_name = 'Bermesio'
    app_version = packaging.version.parse('0.1.0')

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
        # 'BlenderZippedAddon': '.dra',
        # 'BlenderDirectoryAddon': '.dra',
        # 'BlenderSingleFileAddon': '.dra',
        'BlenderDevAddon': '.dda',
        # 'BlenderDevDirectoryAddon': '.dda',
        # 'BlenderDevSingleFileAddon': '.dda',
        'BlenderScript': '.dbs',
        'BlenderReleasedScript': '.drs',
        # 'BlenderStartupScript': '.drs',
        # 'BlenderRegularScript': '.drs',
        'BlenderDevScript': '.dds',
        # 'BlenderDevStartupScript': '.dds',
        # 'BlenderDevRegularScript': '.dds',
        'PythonDevLibrary': '.dpl',
    }

    def __new__(cls, *args, **kwargs):
        """Guard against instantiation."""
        raise Exception('Config should not be instantiated.')

    @classmethod
    def get_dill_extension(cls, component: str) -> str:
        """Get the dill extension of a component class."""
        component_class_name = component.__class__.__name__
        if component_class_name not in cls.dill_extensions:
            for class_ in component.__class__.__bases__:
                if class_.__name__ in cls.dill_extensions:
                    return cls.dill_extensions[class_.__name__]
        return cls.dill_extensions[component_class_name]
