import os
from pathlib import Path
import tempfile

import requests

from commons.common import Result, ResultList, blog, SharedFunctions as SF
from components.blender_addon import (BlenderAddon, BlenderZippedAddon, BlenderDirectoryAddon, BlenderSingleFileAddon,
                                      BlenderDevDirectoryAddon, BlenderDevSingleFileAddon, BlenderAddonManager)
from components.blender_program import BlenderProgram, BlenderProgramManager
from components.blender_setup import BlenderSetup, BlenderSetupManager
from components.blender_script import (BlenderScript, BlenderRegularScript, BlenderStartupScript,
                                       BlenderDevRegularScript, BlenderDevStartupScript, BlenderScriptManager)
from components.blender_venv import BlenderVenv, BlenderVenvManager
from components.python_dev_library import PythonDevLibrary, PythonDevLibraryManager
from components.profile import Profile, ProfileManager
from config import Config


class Repository:
    _instance = None
    _is_initialized = False

    component_save_dir_name = Path('.repo')  # The path for saving components' dill files

    sub_repo_config = {
        'blender_program_repo': {
            'path': None,
            'extension': '.dbp',
            'classes': [BlenderProgram],
            'manager': BlenderProgramManager,
            'creation_fn': BlenderProgramManager.create_blender_program,
            'data_path_attr': None,
        },
        'blender_venv_repo': {
            'path': 'Venvs',
            'extension': '.dbv',
            'classes': [BlenderVenv],
            'manager': BlenderVenvManager,
            'creation_fn': BlenderVenvManager.create_blender_venv,
            'data_path_attr': 'venv_path',
        },
        'blender_setup_repo': {
            'path': 'Setups',
            'extension': '.dsu',
            'classes': [BlenderSetup],
            'manager': BlenderSetupManager,
            'creation_fn': BlenderSetupManager.create_blender_setup,
            'data_path_attr': 'setup_path',
        },
        'blender_addon_repo': {
            'path': 'Addons',
            'extension': '.dba',
            'classes': [BlenderZippedAddon, BlenderDirectoryAddon, BlenderSingleFileAddon],
            'manager': BlenderAddonManager,
            'creation_fn': BlenderAddonManager.create_blender_addon,
            'data_path_attr': 'addon_path',
        },
        'blender_script_repo': {
            'path': 'Scripts',
            'extension': '.dbs',
            'classes': [BlenderRegularScript, BlenderStartupScript],
            'manager': BlenderScriptManager,
            'creation_fn': BlenderScriptManager.create_blender_script,
            'data_path_attr': 'script_path',
        },
        'blender_dev_addon_repo': {
            'path': None,
            'extension': '.dda',
            'classes': [BlenderDevDirectoryAddon, BlenderDevSingleFileAddon],
            'manager': BlenderAddonManager,
            'creation_fn': BlenderAddonManager.create_blender_dev_addon,
            'data_path_attr': None,
        },
        'blender_dev_script_repo': {
            'path': None,
            'extension': '.dds',
            'classes': [BlenderDevRegularScript, BlenderDevStartupScript],
            'manager': BlenderScriptManager,
            'creation_fn': BlenderScriptManager.create_blender_dev_script,
            'data_path_attr': None,
        },
        'dev_library_repo': {
            'path': None,
            'extension': '.ddl',
            'classes': [PythonDevLibrary],
            'manager': PythonDevLibraryManager,
            'creation_fn': PythonDevLibraryManager.create_python_dev_library,
            'data_path_attr': None,
        },
        'profile_repo': {
            'path': 'Profiles',
            'extension': '.dpr',
            'classes': [Profile],
            'manager': ProfileManager,
            'creation_fn': ProfileManager.create_profile,
            'data_path_attr': None,
        },
    }
    sub_repos = {}  # A dict of sub repos indexed by the same keys above

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
                self.sub_repos = {}

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

    def init_sub_repos(self) -> ResultList:
        """
        Initialize all sub repos defined in sub_repo_config. The sub repos will load existing components from disk
        and perform the verification on the components and cleaning of the unloaded or corrupted dill files. The results
        need to be returned to the caller, so this function is not called in __init__.

        :return: A ResultList of the results of initializing all sub repos
        """
        results = []
        for sub_repo_name, sub_repo_config in self.sub_repo_config.items():
            sub_repo = SubRepository(self.component_save_dir, sub_repo_name, sub_repo_config)
            setattr(self, sub_repo_name, sub_repo)
            self.sub_repos[sub_repo_name] = sub_repo
            result = sub_repo.load_components_from_disk()
            results.append(result)
        return ResultList(results)

    def save_all_components(self) -> Result:
        return ResultList([sub_repo.save_components_to_disk() for sub_repo in self.sub_repos.values()]).to_result()

    def get_component_class_belonging_sub_repo(self, component_class) -> 'SubRepository' or None:
        """
        Get the sub repo that the component class belongs to by checking the component class against the sub repo's
        classes defined in the sub_repo_config.

        :param component_class: a component class

        :return: the sub repo that the component class belongs to or None
        """
        for sub_repo_config in self.sub_repo_config.values():
            if component_class in sub_repo_config['classes']:
                return getattr(self, sub_repo_config['name'])
        return

    def get_component_belonging_sub_repo(self, component) -> 'SubRepository' or None:
        """
        Get the sub repo that the component belongs to by checking the component's class against the sub repo's
        classes defined in the sub_repo_config.

        :param component: a component object

        :return: the sub repo that the component belongs to or None
        """
        return self.get_component_class_belonging_sub_repo(component.__class__)

    def add_component(self, component) -> Result:
        sub_repo = self.get_component_belonging_sub_repo(component)
        if sub_repo:
            return sub_repo.add(component)
        return Result(False, f'No sub repo found for {component}')

    def create_component(self, component_class, *args, **kwargs) -> Result:
        sub_repo = self.get_component_class_belonging_sub_repo(component_class)
        if not sub_repo:
            try:
                component = sub_repo.config['creation_fn'](*args, **kwargs)
                return self.add_component(component)
            except Exception as e:
                return Result(False, f'Error creating component: {e}')
        else:
            return Result(False, f'No sub repo found for {component_class}')

    def remove_component(self, component) -> Result:
        sub_repo = self.get_component_belonging_sub_repo(component)
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
            sub_repo = self.get_component_belonging_sub_repo(component)
            return sub_repo.update(component)
        else:
            return Result(False, f'Component {component} is not updatable')

    # TODO: Replace this fn with a more universal matching function for components against the repo
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
        self.classes = config['classes']
        for class_ in self.classes:
            class_.dill_extension = self.extension  # Monkey patch the dill extension to the class
        self.pool = {}

    def _get_sub_repo_path(self) -> Path or None:
        # Check if this sub repo needs a path
        if self.config['path']:
            sub_repo_path = self.component_save_dir.parent / self.config['path']
            if not sub_repo_path.exists():
                os.makedirs(sub_repo_path)
            return sub_repo_path
        else:
            return

    def load_components_from_disk(self) -> Result:
        """
        Load all components from disk to the pool. After loading the components, verify them and remove the unloaded
        or corrupted dill files of the same type from disk. Return the result of these actions.

        :return: a Result object of the result of loading components from disk
        """
        if self.component_save_dir:
            self.pool = {}
            results = []
            corrupted_dill_files = []
            # Collect all dill files of the same extension from disk
            dill_files = [file for file in self.component_save_dir.iterdir() if file.suffix == self.extension]
            # Get the first class in the list, the dill file loading function is a class function, so it is OK to call
            # it with any class in the list.
            class_ = self.classes[0]
            # Go through all found dill files
            while len(dill_files):
                file = dill_files.pop()
                result = class_.load_from_disk(file)
                if result:
                    component = result.data
                    # Doublecheck the class of the loaded component
                    if component.__class__ in self.classes:
                        # The component pool is indexed by the hash of the component
                        self.pool[hash(component)] = component
                    else:
                        corrupted_dill_files.append(file)
                        result = Result(False, f'The loaded component is of the type {component.__class__}, '
                                               f'not the expected type {self.classes}. The file will be removed.')
                # If failed to load, consider the file to be corrupted
                else:
                    corrupted_dill_files.append(file)
                results.append(result)
            # Remove the corrupted dill files from disk
            for file in corrupted_dill_files:
                os.remove(file)

            result_list = ResultList(results)
            if len(result_list.error_messages):
                return Result(False, f'Error loading components from disk: {result_list.error_messages}')
            else:
                return Result(True)
        else:
            return Result(False, f'No component save directory found for {self.name}')

    def save_components_to_disk(self) -> Result:

        if self.component_save_dir:
            return ResultList([component.save_to_disk(self.component_save_dir)
                               for component in self.pool.values()]).to_result()
        else:
            return Result(False, f'No component save directory found for {self.name}')

    def get(self, component) -> object or None:
        return self.pool.get(hash(component), None)

    def add(self, component, force_add=False) -> Result:
        if component.__class__ in self.classes:
            # Check if the component already exists in the pool, note this is comparing the hash of the component,
            # which essentially means the content of the component, not the instance itself.
            if component in self.pool and not force_add:
                return Result(False, f'{component} already exists in {self.name}')
            else:
                self.pool[hash(component)] = component
                if self.component_save_dir:
                    result = component.save_to_disk(self.component_save_dir)
                    if result:
                        return Result(True, f'{component} added to {self.name}', component)
                    else:
                        return Result(False, f'Error saving {component} to disk: {result.message}')
                else:
                    return Result(False, f'No component save directory found for {self.name}')
        return Result(False, 'Invalid component type')

    def update(self, component) -> Result:
        if issubclass(component.__class__, self.classes):
            if component in self.pool:
                result = self.add(component, force_add=True)
                return result
            else:
                return Result(False, f'{component} doesn\'t exists in {self.name}')
        else:
            return Result(False, f'Invalid component type')

    def remove(self, component, remove_in_repo_data=True) -> Result:
        if self.component_save_dir:
            if issubclass(component.__class__, self.classes):
                if component in self.pool:
                    # Remove the component from the pool
                    del self.pool[hash(component)]
                    component.remove_from_disk()
                    if remove_in_repo_data:
                        in_repo_data_path = getattr(component, self.config['data_path_attr'], None)
                        if in_repo_data_path:
                            result = SF.remove_target_path(in_repo_data_path)
                            if result:
                                return Result(True, f'{component} removed from {self.name}')
                            else:
                                return Result(True, f'{component} removed from {self.name}, but failed to remove its '
                                                    f'data in the repo at {in_repo_data_path}.')
                        else:
                            return Result(True, f'{component} removed from {self.name}, but failed to find its data in '
                                                f'the repo.')
                    return Result(True, f'{component} removed from {self.name}')
                else:
                    return Result(False, f'{component} doesn\'t exists in {self.name}')
            return Result(False, 'Invalid component type')
        else:
            return Result(False, f'No component save directory found for {self.name}')

    def clear_pool(self, remove_from_disk=False):
        if self.pool and remove_from_disk:
            for component in self.pool.values():
                component.remove_from_disk()
        self.pool = {}

    def __str__(self):
        return f'{self.name}: {len(self.pool)} components'
