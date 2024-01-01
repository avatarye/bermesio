import os
from pathlib import Path
import tempfile

import requests

from commons.common import Result, blog
from components.blender_addon import BlenderAddon
from components.blender_dev_addon import BlenderDevAddon
from components.blender_program import BlenderProgram
from components.blender_script import BlenderScript
from components.blender_venv import BlenderVenv
from components.python_dev_library import PythonDevLibrary
from components.profile import Profile
from config import Config


class Repository:

    repo_component_path = '.repo'  # The path for saving components' dill files

    sub_repo_config = {
        'blender_program_repo': {
            'path': None,
            'extension': '.dbp',
            'class': BlenderProgram,
        },
        'blender_venv_repo': {
            'path': 'Venvs',
            'extension': '.dbv',
            'class': BlenderVenv,
        },
        'blender_addon_repo': {
            'path': 'Addons',
            'extension': '.dba',
            'class': BlenderAddon,
        },
        'blender_script_repo': {
            'path': 'Scripts',
            'extension': '.dbs',
            'class': BlenderScript,
        },
        'dev_library_repo': {
            'path': None,
            'extension': '.ddb',
            'class': PythonDevLibrary,
        },
        'dev_addon_repo': {
            'path': None,
            'extension': '.dda',
            'class': BlenderDevAddon,
        },
        'profile_repo': {
            'path': 'Profiles',
            'extension': '.dpr',
            'class': Profile,
        },
    }

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Repository, cls).__new__(cls)
        return cls._instance

    def __init__(self, repository_path=None):
        # Allow using a repository path other than the default one
        if repository_path:
            self.repo_path = Path(repository_path)
        else:
            self.repo_path = Path(Config.repo_path)
        self.is_repository_path_ready = False
        self.has_internet_connection = False
        self.verify_readiness()

        if self.is_repository_path_ready:
            self.repo_component_path = self.repo_path / self.repo_component_path
            self._init_sub_repos()

    def _is_repository_path_ready(self) -> bool:
        try:
            # Check if the path exists and is a directory
            if not self.repo_path.exists():
                os.makedirs(self.repo_path)
            if os.path.exists(self.repo_path) and self.repo_path.is_dir():
                testfile = tempfile.TemporaryFile(dir=self.repo_path)
                testfile.close()
                return True
        except (OSError, IOError):
            pass
        blog(5, f'Repository path {self.repo_path} is not accessible.')
        return False

    @staticmethod
    def _if_has_internet_connection() -> bool:
        try:
            response = requests.get("http://www.google.com", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            pass
        blog(3, f'No internet connection.')
        return False

    def verify_readiness(self):
        self.is_repository_path_ready = self._is_repository_path_ready()
        self.has_internet_connection = self._if_has_internet_connection()

    def _init_sub_repos(self):
        for sub_repo_name, sub_repo_config in self.sub_repo_config.items():
            sub_repo = SubRepository(sub_repo_name, sub_repo_config)
            setattr(self, sub_repo_name, sub_repo)


class SubRepository:

    def __init__(self, name, config):
        self.repo = Repository()  # Get the singleton instance of Repository
        self.name = name
        self.config = config
        self.path = self._get_sub_repo_path()
        self.extension = config['extension']
        self.class_ = config['class']
        self.class_.dill_extension = self.extension  # Monkey patch the dill extension to the class

        self.load_components_from_disk()

    def _get_sub_repo_path(self):
        if self.config['path']:
            sub_repo_path = self.repo.repo_path / self.config['path']
            if not sub_repo_path.exists():
                os.makedirs(sub_repo_path)
            return sub_repo_path
        else:
            return

    def load_components_from_disk(self):
        self.pool = {}
        if self.path:
            for file in self.repo.repo_path.iterdir():
                if file.suffix == self.extension:
                    component = self.class_.load_from_disk(file)
                    if component.verify():
                        self.pool[component.uuid] = component

    def save_components_to_disk(self):
        for component in self.pool.values():
            component.save_to_disk(self.path)

    def get(self, component):
        return self.pool.get(component.uuid, None)

    def add(self, component):
        if isinstance(component, self.class_):
            if component.uuid not in self.pool:
                self.pool[component.uuid] = component
                component.save_to_disk(self.path)

    def remove(self, component):
        if isinstance(component, self.class_):
            if component.uuid in self.pool:
                del self.pool[component.uuid]
                component.remove_from_disk()

    def clear(self, remove_from_disk=False):
        if remove_from_disk:
            for component in self.pool.values():
                component.remove_from_disk()
        self.pool = {}
