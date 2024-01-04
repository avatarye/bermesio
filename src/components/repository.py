import os
from pathlib import Path
import shutil
import tempfile

import requests

from commons.common import Result, blog, SharedFunctions as SF
from components.blender_addon import BlenderAddon
from components.blender_program import BlenderProgram
from components.blender_setup import BlenderSetup
from components.blender_script import BlenderScript
from components.blender_venv import BlenderVenv
from components.python_dev_library import PythonDevLibrary
from components.profile import Profile
from config import Config


class Repository:
    _instance = None
    _is_initialized = False

    component_save_dir_name = '.repo'  # The path for saving components' dill files

    sub_repo_config = {
        'blender_program_repo': { 'path': None, 'extension': '.dbp', 'class': BlenderProgram, },
        'blender_venv_repo': { 'path': 'Venvs', 'extension': '.dbv', 'class': BlenderVenv, },
        'blender_setup_repo': { 'path': 'Setups', 'extension': '.dsu', 'class': BlenderSetup, },
        'blender_addon_repo': { 'path': 'Addons', 'extension': '.dba', 'class': BlenderAddon, },
        'blender_script_repo': { 'path': 'Scripts', 'extension': '.dbs', 'class': BlenderScript, },
        'dev_library_repo': { 'path': None, 'extension': '.ddb', 'class': PythonDevLibrary, },
        'dev_addon_repo': { 'path': None, 'extension': '.dda', 'class': BlenderAddon, },
        'profile_repo': { 'path': 'Profiles', 'extension': '.dpr', 'class': Profile, },
    }
    sub_repo_dict = {}  # A dict of all sub repo instances, indexed by class name

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Repository, cls).__new__(cls)
        return cls._instance

    def __init__(self, repo_dir=None):
        if not self._is_initialized:
            # Allow using a repository path other than the default one
            if repo_dir:
                self.repo_path = Path(repo_dir)
            else:
                self.repo_path = Path(Config.repo_path)
            self.is_repository_path_ready = False
            self.has_internet_connection = False
            self.verify_readiness()

            if self.is_repository_path_ready:
                self.component_save_dir = self._get_component_save_dir()
                self.sub_repo_dict = {}
                self._init_sub_repos()

            self._is_initialized = True

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

    def _get_component_save_dir(self) -> Path or None:
        if self.is_repository_path_ready:
            component_save_dir = self.repo_path / self.component_save_dir_name
            if not component_save_dir.exists():
                os.makedirs(component_save_dir)
            if component_save_dir.exists() and component_save_dir.is_dir():
                return component_save_dir
        return

    def _init_sub_repos(self):
        for sub_repo_name, sub_repo_config in self.sub_repo_config.items():
            sub_repo = SubRepository(self.component_save_dir, sub_repo_name, sub_repo_config)
            setattr(self, sub_repo_name, sub_repo)
            self.sub_repo_dict[sub_repo_config['class']] = sub_repo

    def save_all(self):
        for sub_repo in self.sub_repo_dict.values():
            sub_repo.save_components_to_disk()

    def _get_sub_repo_by_class(self, component_class) -> 'SubRepository' or None:
        sub_repo = self.sub_repo_dict.get(component_class, None)
        if not sub_repo:
            for sub_repo_class in self.sub_repo_dict.keys():
                if issubclass(component_class, sub_repo_class):
                    sub_repo = self.sub_repo_dict[sub_repo_class]
                    break
        return sub_repo

    def add_component(self, component) -> Result:
        sub_repo = self._get_sub_repo_by_class(component.__class__)
        if sub_repo:
            return sub_repo.add(component)
        return Result(False, f'No sub repo found for {component}')

    def create_component(self, component_class, *args, **kwargs) -> Result:
        try:
            component = component_class(*args, **kwargs)
        except Exception as e:
            return Result(False, f'Error creating component: {e}')
        return self.add_component(component)

    def remove_component(self, component) -> Result:
        sub_repo = self._get_sub_repo_by_class(component.__class__)
        if sub_repo:
            return sub_repo.remove(component)
        return Result(False, f'No sub repo found for {component}')

    def update_component(self, component) -> Result:
        """
        Update the component in the repo with the new component. The new component must be an updatable type, such as
        BlenderAddon, BlenderScript, and have the same content.

        :param component:
        :return:
        """
        if issubclass(component.__class__, BlenderAddon) or issubclass(component.__class__, BlenderScript):
            sub_repo = self._get_sub_repo_by_class(component.__class__)
            return sub_repo.update(component)
        else:
            return Result(False, f'Component {component} is not updatable')

    def match_venv_to_blender_program(self):
        """
        BlenderVenv needs to be matched with BlenderProgram in the repo, because the venv is created with its own
        BlenderProgram based on the config of the venv. It needs to be replaced with the repo's existing BlenderProgram
        by comparing the Blender exe paths.

        :param blender_program:
        """
        for venv in self.blender_venv_repo.pool.values():
            if venv.blender_program not in self.blender_program_repo.pool:  # Not already using a repo BlenderProgram
                for blender_program in self.blender_program_repo.pool.values():
                    if venv.blender_program.blender_exe_path == blender_program.blender_exe_path:
                        venv.blender_program = blender_program
                        break


class SubRepository:

    def __init__(self, component_save_dir: Path, name: str, config: dict):
        self.component_save_dir = component_save_dir  # Get the singleton instance of Repository
        self.name = name
        self.config = config
        self.path = self._get_sub_repo_path()
        self.extension = config['extension']
        self.class_ = config['class']
        self.class_.dill_extension = self.extension  # Monkey patch the dill extension to the class
        self.pool = {}

        self.load_components_from_disk()

    def _get_sub_repo_path(self) -> Path or None:
        # Check if this sub repo needs a path
        if self.config['path']:
            sub_repo_path = self.component_save_dir.parent / self.config['path']
            if not sub_repo_path.exists():
                os.makedirs(sub_repo_path)
            return sub_repo_path
        else:
            return

    def load_components_from_disk(self):
        if self.component_save_dir:
            self.pool = {}
            for file in self.component_save_dir.iterdir():
                if file.suffix == self.extension:
                    component = self.class_.load_from_disk(file)
                    if component.verify():
                        self.pool[component.uuid] = component

    def save_components_to_disk(self):
        if self.component_save_dir:
            for component in self.pool.values():
                component.save_to_disk(self.component_save_dir)

    def get(self, component) -> object or None:
        return self.pool.get(component.uuid, None)

    def add(self, component) -> Result:
        if issubclass(component.__class__, self.class_):
            if component.uuid not in self.pool:
                self.pool[component.uuid] = component
                if self.component_save_dir:
                    component.save_to_disk(self.component_save_dir)
                return Result(True, f'{component} added to {self.name}', component)
            return Result(False, f'{component} already exists in {self.name}')
        return Result(False, 'Invalid component type')

    def _get_associated_data_path_to_delete(self, component) -> Path or None:
        data_path_dict = {
            BlenderProgram: None,  # We don't delete the existing Blender program
            BlenderVenv: 'venv_path',
            BlenderAddon: 'addon_path',
            BlenderScript: 'script_path',
            PythonDevLibrary: None,  # We don't delete the existing Python dev library
            BlenderDevDirectoryAddon: None,  # We don't delete the existing Blender dev addon
            Profile: 'profile_dir',
        }
        for class_ in data_path_dict.keys():
            if issubclass(component.__class__, self.class_):
                attr = data_path_dict[class_]
                if attr:
                    return getattr(component, attr, None)
        return

    def update(self, component) -> Result:
        if issubclass(component.__class__, self.class_):
            # Find all components in pool with the same content
            same_content_components = []
            for existing_component in self.pool.values():
                if existing_component.compare_name(component):
                    same_content_components.append(existing_component)
            # If there are existing components with the same content, remove them
            if len(same_content_components):
                for existing_component in same_content_components:
                    self.remove(existing_component)
                # Add the new component
                return self.add(component)
            return Result(False, f'No existing component with the same content found in {self.name}')
        return Result(False, 'Invalid component type')

    def remove(self, component) -> Result:
        if issubclass(component.__class__, self.class_):
            if component.uuid in self.pool:
                del self.pool[component.uuid]
                if self.component_save_dir:
                    component.remove_from_disk()
                associated_data_path = self._get_associated_data_path_to_delete(component)
                if associated_data_path and associated_data_path.exists():
                    if associated_data_path.is_file():
                        os.remove(associated_data_path)
                    else:
                        shutil.rmtree(associated_data_path)
                return Result(True, f'{component} removed from {self.name}', component)
            else:
                return Result(False, f'{component} doesn\'t exists in {self.name}')
        return Result(False, 'Invalid component type')

    def clear_pool(self, remove_from_disk=False):
        if self.pool and remove_from_disk:
            for component in self.pool.values():
                component.remove_from_disk()
        self.pool = {}

    def __str__(self):
        return f'{self.name}: {len(self.pool)} components'
