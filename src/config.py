import os
from pathlib import Path

import packaging.version

class Config:
    """
    A singleton class that stores the configuration of the application.
    """

    app_version = packaging.version.parse('0.1.0')
    app_name = 'Bermesio'

    repo_path = Path(os.path.expanduser('~')) / f'.{app_name.lower()}'


    def __new__(cls, *args, **kwargs):
        """Guard against instantiation."""
        raise Exception('Config should not be instantiated.')
