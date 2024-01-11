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

    def __new__(cls, *args, **kwargs):
        """Guard against instantiation."""
        raise Exception('Config should not be instantiated.')
