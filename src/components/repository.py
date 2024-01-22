import os
from pathlib import Path
import tempfile

import requests

from commons.common import Result, ResultList, blog, SharedFunctions as SF
from components.blender_addon import BlenderAddon, BlenderReleasedAddon, BlenderDevAddon, BlenderAddonManager
from components.blender_program import BlenderProgram, BlenderProgramManager
from components.blender_setup import BlenderSetup, BlenderSetupManager
from components.blender_script import BlenderScript, BlenderReleasedScript, BlenderDevScript, BlenderScriptManager
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
            'storage_dir': 'BlenderPrograms',
            'class': BlenderProgram,
            'manager': BlenderProgramManager,
            'creation_fn': BlenderProgramManager.create,
        },
        'blender_venv_repo': {
            'storage_dir': 'Venvs',
            'class': BlenderVenv,
            'manager': BlenderVenvManager,
            'creation_fn': BlenderVenvManager.create,
        },
        'blender_released_addon_repo': {
            'storage_dir': 'Addons',
            'class': BlenderReleasedAddon,
            'manager': BlenderAddonManager,
            'creation_fn': BlenderAddonManager.create_blender_addon,
        },
        'blender_released_script_repo': {
            'storage_dir': 'Scripts',
            'class': BlenderReleasedScript,
            'manager': BlenderScriptManager,
            'creation_fn': BlenderScriptManager.create_blender_script,
        },
        'blender_dev_addon_repo': {
            'storage_dir': None,
            'class': BlenderDevAddon,
            'manager': BlenderAddonManager,
            'creation_fn': BlenderAddonManager.create_blender_dev_addon,
        },
        'blender_dev_script_repo': {
            'storage_dir': None,
            'class': BlenderDevScript,
            'manager': BlenderScriptManager,
            'creation_fn': BlenderScriptManager.create_blender_dev_script,
        },
        'python_dev_library_repo': {
            'storage_dir': None,
            'class': PythonDevLibrary,
            'manager': PythonDevLibraryManager,
            'creation_fn': PythonDevLibraryManager.create
        },
        'blender_setup_repo': {
            'storage_dir': 'Setups',
            'class': BlenderSetup,
            'manager': BlenderSetupManager,
            'creation_fn': BlenderSetupManager.create,
        },
        'profile_repo': {
            'storage_dir': 'Profiles',
            'class': Profile,
            'manager': ProfileManager,
            'creation_fn': ProfileManager.create,
        },
    }
    sub_repos = {}  # A dict of sub repos indexed by the same keys above

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Repository, cls).__new__(cls)
        return cls._instance

    def __init__(self, repo_dir: str or Path =None, user_query_fn=None):
        repo_dir = Path(repo_dir)
        self.init_params = {'repo_dir': repo_dir, 'user_query_fn': user_query_fn}

    def _is_repository_path_ready(self, repo_dir: Path) -> bool:
        try:
            # Check if the path exists and is a directory
            if not repo_dir.exists():
                os.makedirs(repo_dir)
            if os.path.exists(repo_dir) and repo_dir.is_dir():
                testfile = tempfile.TemporaryFile(dir=repo_dir)
                testfile.close()
                return True
        except (OSError, IOError):
            pass
        blog(5, f'Repository path {repo_dir} is not accessible.')
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

    def _get_component_save_dir(self, repo_dir) -> Path:
        component_save_dir = repo_dir / self.component_save_dir_name
        result = SF.create_target_dir(component_save_dir)
        if result:
            return result.data
        else:
            raise Exception(f'Error creating component save directory at {component_save_dir}')

    def create_instance(self) -> Result:
        repo_dir = self.init_params['repo_dir']
        user_query_fn = self.init_params['user_query_fn']
        if not self._is_initialized:
            try:
                # Allow using a repository path other than the default one from the global config
                if repo_dir:
                    self.repo_dir = Path(repo_dir)
                else:
                    self.repo_dir = Path(Config.repo_dir)
                self.is_repository_path_ready = self._is_repository_path_ready(self.repo_dir)
                self.has_internet_connection = self._if_has_internet_connection()

                self.user_query_fn = user_query_fn

                if self.is_repository_path_ready:
                    Config.repo_dir = repo_dir  # Update the global config with the repo path
                    self.component_save_dir = self._get_component_save_dir(repo_dir)
                    self.sub_repos = {}
                    self._is_initialized = True
                    return Result(True, 'Repository instance created successfully', self)
                else:
                    return Result(False, f'Repository path {self.repo_dir} is not accessible.')
            except Exception as e:
                return Result(False, f'Error creating a Repository instance: {e}')
        else:
            return Result(True, 'Repository instance already created', self)

    def init_sub_repos(self) -> ResultList:
        """
        Initialize all sub repos defined in sub_repo_config. The sub repos will load existing components from disk
        and perform the verification on the components and cleaning of the unloaded or corrupted dill files. The results
        need to be returned to the caller, so this function is not called in create_instance().

        :return: A ResultList of the results of initializing all sub repos
        """
        results = []
        for sub_repo_name, sub_repo_config in self.sub_repo_config.items():
            result = SubRepository(self.repo_dir, self.component_save_dir, sub_repo_name, sub_repo_config,
                                   user_query_fn=self.user_query_fn).create_instance()
            if result:
                sub_repo = result.data
                setattr(self, sub_repo_name, sub_repo)
                self.sub_repos[sub_repo_name] = sub_repo
                result = sub_repo.load_components_from_disk()
            results.append(result)
        return ResultList(results)

    def save_all_components(self) -> Result:
        return ResultList([sub_repo.save_components_to_disk() for sub_repo in self.sub_repos.values()]).to_result()

    def load_all_components(self) -> Result:
        return ResultList([sub_repo.load_components_from_disk() for sub_repo in self.sub_repos.values()]).to_result()

    def get_component_class_belonging_sub_repo(self, component_class) -> 'SubRepository' or None:
        """
        Get the sub repo that the component class belongs to by checking the component class against the sub repo's
        classes defined in the sub_repo_config.

        :param component_class: a component class

        :return: the sub repo that the component class belongs to or None
        """
        for sub_repo_name, sub_repo_config in self.sub_repo_config.items():
            if issubclass(component_class, sub_repo_config['class']):
                return getattr(self, sub_repo_name)
        return

    def get_component_belonging_sub_repo(self, component) -> 'SubRepository' or None:
        """
        Get the sub repo that the component belongs to by checking the component's class against the sub repo's
        classes defined in the sub_repo_config.

        :param component: a component object

        :return: the sub repo that the component belongs to or None
        """
        return self.get_component_class_belonging_sub_repo(component.__class__)

    def add_component(self, component, query_user=False) -> Result:
        sub_repo = self.get_component_belonging_sub_repo(component)
        if sub_repo:
            # If the component is a BlenderVenv, check if it was created from a Blender program in the repo.
            if isinstance(component, BlenderVenv):
                result = self.match_venv_to_blender_program_in_repo(component)
                if not result:
                    return Result(False, f'The Blender venv appears to be not created from a Blender program in the '
                                         f'repo.')
            # Set the component's dill save dir to the repo's component save dir
            component.dill_save_dir = self.component_save_dir
            return sub_repo.add(component, query_user=query_user)
        return Result(False, f'No sub repo found for {component}')

    def create_component(self, component_class, *args, **kwargs) -> Result:
        sub_repo = self.get_component_class_belonging_sub_repo(component_class)
        if sub_repo:
            result = sub_repo.config['creation_fn'](*args, **kwargs)
            if result:
                return self.add_component(result.data)
            else:
                return result
        else:
            return Result(False, f'No sub repo found for {component_class}')

    def remove_component(self, component) -> Result:
        sub_repo = self.get_component_belonging_sub_repo(component)
        if sub_repo:
            return sub_repo.remove(component)
        return Result(False, f'No sub repo found for {component}')

    def replace_component(self, component) -> Result:
        """
        Replace an existing component in the repo with a new component without comparing version numbers. After
        replacing, update all other components that depend on the replaced component.
        """
        raise NotImplementedError

    def update_component(self, component) -> Result:
        """
        Update an existing component in the repo with a new component if the new component has a higher version number.
        After updating, update all other components that depend on the updated component.
        """
        if issubclass(component.__class__, BlenderAddon) or issubclass(component.__class__, BlenderScript):
            sub_repo = self.get_component_belonging_sub_repo(component)
            return sub_repo.update(component)
        else:
            return Result(False, f'Component {component} is not updatable')

    def duplicate_component(self, component) -> Result:
        raise NotImplementedError

    def rename_component(self, component) -> Result:
        raise NotImplementedError

    def match_venv_to_blender_program_in_repo(self, blender_venv: BlenderVenv) -> Result:
        """
        Match the BlenderProgram of the BlenderVenv to the one in the repo. It constraints all the BlenderVenvs in the
        repo to be created from the Blender programs in the repo.

        :param blender_venv: a BlenderVenv object
        """
        if isinstance(blender_venv, BlenderVenv):
            if self.blender_program_repo.pool is not None:
                # Check if the BlenderProgram of the venv is already in the repo
                if hash(blender_venv.blender_program) in self.blender_program_repo.pool:
                    # If found, replace the venv's BlenderProgram with the one in the repo
                    blender_venv.blender_program = self.blender_program_repo.pool[hash(blender_venv.blender_program)]
                    return Result(True, f'Blender venv {blender_venv} matched with an existing Blender program in the '
                                        f'repo.')
                else:
                    return Result(False, f'No matching Blender program in the repo found for {blender_venv}')
            else:
                return Result(False, f'Error getting Blender program sub-repo')
        else:
            return Result(False, f'Invalid Blender venv {blender_venv}')


class SubRepository:

    def __init__(self, repo_dir: Path, component_save_dir: Path, name: str, config: dict, user_query_fn=None):
        self.init_params = {'repo_dir': repo_dir, 'component_save_dir': component_save_dir, 'name': name,
                            'config': config, 'user_query_fn': user_query_fn}

    def _get_storage_save(self, storage_dir) -> Path or None:
        # Check if this sub repo needs a path
        result = SF.create_target_dir(self.repo_dir / storage_dir)
        if result:
            return result.data
        else:
            raise Exception(f'Error creating sub repo storage path at {storage_dir}')

    def create_instance(self) -> Result:
        try:
            self.repo_dir = self.init_params['repo_dir']
            self.component_save_dir = self.init_params['component_save_dir']
            self.name = self.init_params['name']
            self.config = self.init_params['config']
            self.user_query_fn = self.init_params['user_query_fn']
            if self.config['storage_dir'] is not None:  # Some sub-repo doesn't need a storage path
                self.storage_save_dir = self._get_storage_save(self.config['storage_dir'])
            else:
                self.storage_save_dir = None
            self.class_ = self.config['class']
            self.dill_extension = Config.dill_extensions[self.class_.__name__]
            self.pool = {}
            return Result(True, f'Sub repo {self.name} created successfully', self)
        except Exception as e:
            return Result(False, f'Error creating a SubRepository instance: {e}')

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
            dill_files = [file for file in self.component_save_dir.iterdir()
                          if file.suffix == self.dill_extension]
            # Go through all found dill files
            while len(dill_files):
                file = dill_files.pop()
                result = self.class_.load_from_disk(file)
                if result:
                    component = result.data
                    # Doublecheck the class of the loaded component
                    if issubclass(component.__class__, self.class_):
                        # The component pool is indexed by the hash of the component. We do not check if the component
                        # already exists in the pool, because this method should be only be called when the pool is
                        # empty.
                        self.pool[hash(component)] = component
                        result = Result(True, f'{component} loaded from {file}')
                    else:
                        corrupted_dill_files.append(file)
                        result = Result(False, f'The loaded component is of the type {component.__class__}, '
                                               f'not the expected type {self.class_}. The file will be removed.')
                # If failed to load, consider the file to be corrupted
                else:
                    corrupted_dill_files.append(file)
                results.append(result)

            # Remove the corrupted dill files from disk if user agrees
            if len(corrupted_dill_files) and self.user_query_fn is not None:
                result = self.user_query_fn('Corrupted Saved Data Found',
                                            f'{len(corrupted_dill_files)} corrupted saved files found for {self.name}. '
                                            f'Would you like to remove them?')
                if result:
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
            return ResultList([component.save_to_disk() for component in self.pool.values()]).to_result()
        else:
            return Result(False, f'No component save directory found for {self.name}')

    def get(self, component) -> object or None:
        return self.pool.get(hash(component), None)

    def add(self, component, query_user=False) -> Result:
        if issubclass(component.__class__, self.class_):
            # Check if the component already exists in the pool, note this is comparing the hash of the component,
            # which essentially means the content of the component, not the instance itself.
            if hash(component) in self.pool:
                if query_user and self.user_query_fn is not None:
                    result = self.user_query_fn('Add Component', f'{component} already exists in the repo. Would you '
                                                                 f'like to replace it?')
                    # If user agrees to replace the existing component, remove the existing component from the repo
                    if result:
                        # Remove the existing component from the repo
                        result = self.remove(component, query_user=False)
                        if not result:
                            return result  # Return error message if failed to remove the existing component
                    # If user cancels the operation, return True to indicate the operation is cancelled.
                    else:
                        return Result(True, f'User cancelled adding {component} to the repo.')
                else:
                    return Result(False, f'{component} already exists in the repo')

            if self.component_save_dir:
                # Store the component in the repo storage path if applicable
                if self.storage_save_dir and component.if_store_in_repo:
                    result = component.store_in_repo(self.storage_save_dir)
                    if not result:
                        return result
                # Add the component to the pool after storing it in the repo, for this will change its data path and
                # hash value
                self.pool[hash(component)] = component
                # Save the component to the repo's component save dir immediately after adding it to the pool
                result = component.save_to_disk()
                if not result:
                    return result
                return Result(True, f'{component} added to the repo', component)
            else:
                return Result(False, f'No component save directory found for the repo')
        else:
            return Result(False, 'Invalid component type')

    def remove(self, component, query_user=True) -> Result:
        if self.component_save_dir:
            if issubclass(component.__class__, self.class_):
                # Query user if necessary
                if query_user and self.user_query_fn is not None:
                    result = self.user_query_fn('Remove Component',
                                                f'Would you like to remove {component} from the repo?')
                    if not result:
                        return Result(True, f'User cancelled removing {component} from the repo.')

                # Remove the component from the pool, its dill file, and associated data if stored in the repo
                if hash(component) in self.pool:
                    # Remove the component from the pool
                    del self.pool[hash(component)]
                    component.remove_from_disk()
                    if component.if_store_in_repo:
                        if component.data_path.exists():
                            result = SF.remove_target_path(component.data_path)
                            if result:
                                return Result(True, f'{component} removed from the repo')
                            else:
                                return Result(True, f'{component} removed from the repo, but failed to remove its '
                                                    f'data in the repo at {component.data_path}.')
                        else:
                            return Result(True, f'{component} removed from the repo, but failed to find its data in '
                                                f'the repo.')
                    return Result(True, f'{component} removed from the repo')
                else:
                    return Result(False, f'{component} doesn\'t exists in the repo')
            return Result(False, f'Invalid component type, {component.__class__} is not a subclass of {self.class_}')
        else:
            return Result(False, f'No component save directory found for the repo')

    # TODO: Implement this function after Profile and Setup are implemented. Updating components needs to be done with
    # Profile and Setup instances as well.
    def update(self, component) -> Result:
        raise NotImplementedError

    def clear_pool(self) -> Result:
        result = Result(True, f'Pool cleared for {self.name}')
        if self.pool:
            components = list(self.pool.values())
            result = ResultList([self.remove(component, query_user=False) for component in components]).to_result()
        self.pool = {}
        return result

    def __str__(self):
        return f'{self.name}: {len(self.pool)} components'
