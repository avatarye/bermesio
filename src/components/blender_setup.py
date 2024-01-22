import json
from pathlib import Path

from commons.common import Result, ResultList, SharedFunctions as SF
from components.blender_addon import (BlenderZippedAddon, BlenderDirectoryAddon, BlenderSingleFileAddon,
                                      BlenderDevDirectoryAddon, BlenderDevSingleFileAddon)
from components.blender_script import (BlenderRegularScript, BlenderStartupScript, BlenderDevRegularScript,
                                       BlenderDevStartupScript)
from components.component import Component, Dillable
from config import Config


class BlenderSetup(Component):
    """
    A class representing a Blender setup. A Blender setup is a directory that contains a Blender config directory, which
    can be used a custom config for Blender if proper Blender env var points to it, and a "scripts" directory, which
    can be used as a custom scripts directory for Blender if proper Blender env var points to it. The "scripts"
    directory contains an "addons" subdirectory for storing addons, a "startup" subdirectory for storing startup
    scripts. An additional "regular" subdirectory is also created for storing regular scripts. A BlenderSetup instance
    is a collection of all BlenderAddon and BlenderScript objects that are associated with this setup and deployed to
    its directory in the repo.
    """

    # Setup config file name
    setup_json_path = Path(f'.blender_setup.json')
    # Custom Blender config directory
    setup_blender_config_path = Path('config')
    # Inherent "Scripts" directory to a Blender setup
    setup_scripts_path = Path('scripts')
    # Addon directory
    setup_addon_path = Path('scripts/addons')
    # Startup script directory
    setup_startup_script_path = Path('scripts/startup')
    # Additional regular script directory, must be the same as BlenderScript class's
    setup_regular_scripts_path = Path(f'scripts/{Config.app_name.lower()}_scripts')

    # A dict helps to establish the relationship between component classes and their corresponding directories
    component_class_dict = {
        'released_addons': {
            'classes': [BlenderZippedAddon, BlenderDirectoryAddon, BlenderSingleFileAddon],
            'dir': setup_addon_path,
        },
        'dev_addons': {
            'classes': [BlenderDevDirectoryAddon, BlenderDevSingleFileAddon],
            'dir': setup_addon_path,
        },
        'startup_scripts': {
            'classes': [BlenderStartupScript],
            'dir': setup_scripts_path,  # The BlenderScript subclasses know what subdir to use, hence the script dir
        },
        'regular_scripts': {
            'classes': [BlenderRegularScript],
            'dir': setup_scripts_path,
        },
        'dev_startup_scripts': {
            'classes': [BlenderDevStartupScript],
            'dir': setup_scripts_path,
        },
        'dev_regular_scripts': {
            'classes': [BlenderDevRegularScript],
            'dir': setup_scripts_path,
        },
    }

    def __init__(self, repo_dir: str or Path, name: str):
        """
        Initialize a BlenderSetup instance. "name" is mandatory and determines the name of the setup directory in the
        repo.

        :param repo_dir: a str or Path object of the path to the sub-repo directory for BlenderSetup
        :param name: a str of the name of the Blender setup
        """
        data_path = Path(repo_dir) / name  # The data path is a subdirectory in the setup repo directory
        super().__init__(data_path)
        self.dill_extension = Config.get_dill_extension(self)
        self.__class__.dill_extension = self.dill_extension
        # All BlenderSetup instances must be created in the repo directly. No need to store it.
        self.if_store_in_repo = False
        self.is_renamable = True
        self.is_upgradeable = False
        self.is_duplicable = True
        self.init_params = {'repo_dir': repo_dir, 'name': name}

    def _get_setup_config(self) -> dict:
        """
        Get the setup config from the setup config file. If the setup config file doesn't exist, create a new one with
        default values.

        :return: a dict of the setup config
        """
        setup_json_path = self.data_path / self.setup_json_path
        if setup_json_path.exists():
            with open(self.data_path / self.setup_json_path, 'r') as f:
                return json.load(f)
        else:
            return  {
                'blender_config': False,
                'released_addons': self.released_addons,
                'dev_addons': self.dev_addons,
                'startup_scripts': self.startup_scripts,
                'regular_scripts': self.regular_scripts,
                'dev_startup_scripts': self.dev_startup_scripts,
                'dev_regular_scripts': self.dev_regular_scripts,
            }

    def create_instance(self) -> Result:
        """
        Create a BlenderSetup instance.

        :return: a Result object indicating if the creation is successful, the message generated during the creation,
                 and this object if successful
        """
        # Make sure the setup directory is inside the repo
        assert Config.repo_dir in Path(self.init_params['repo_dir']).parents
        # Create the setup directory if not exists, this is a new BlenderSetup instance
        if self.data_path is None:
            if SF.is_valid_name_for_path(self.init_params['name']):
                result = SF.create_target_dir(self.init_params['repo_dir'] / self.init_params['name'])
                if not result:
                    return result
            else:
                return Result(False, f'Invalid name {self.data_path.name} for the Blender setup.')
            self.data_path = result.data
        if self.data_path.exists():
            # Initialize the BlenderSetup instance's attributes
            self.name = self.data_path.name
            self.is_stored_in_repo = True
            self.repo_rel_path = self.data_path.relative_to(Config.repo_dir)
            self.released_addons = {}  # {addon hash:addon relative path}
            self.dev_addons = {}
            self.regular_scripts = {}
            self.startup_scripts = {}
            self.dev_regular_scripts = {}
            self.dev_startup_scripts = {}
            self.setup_json = self._get_setup_config()
            # Populate above based on the setup config
            return self._verify_components_against_config()
        else:
            return Result(False, f'Blender setup path not found at {self.data_path}')

    def _verify_components_against_config(self) -> Result:
        """
        Verify the components against the setup config. The main principle is to correct the setup config based on the
        existing data. Avoid deleting or altering the existing data.

        :return: a Result object indicating if the verification is successful
        """

        def get_blender_config_status() -> bool:
            blender_config = self.data_path / self.setup_blender_config_path
            return blender_config.exists()

        def verify_component_dict(component_dict) -> Result:
            if len(component_dict) == 0:
                return Result(True)
            results = []
            for hash_, rel_path in component_dict.component_items():
                if not (self.data_path / rel_path).exists():
                    results.append(Result(False, f'Component {rel_path} not found'))
            return ResultList(results).to_result()

        results = []
        # Check Blender config
        self.setup_json['blender_config'] = get_blender_config_status()

        # Check addons
        results.append(verify_component_dict(self.setup_json['released_addons']))
        results.append(verify_component_dict(self.setup_json['dev_addons']))

        # Check scripts
        results.append(verify_component_dict(self.setup_json['startup_scripts']))
        results.append(verify_component_dict(self.setup_json['regular_scripts']))
        results.append(verify_component_dict(self.setup_json['dev_startup_scripts']))
        results.append(verify_component_dict(self.setup_json['dev_regular_scripts']))

        # Update the setup config
        result = self.save_config_json()  # Don't save dill file here, it may not be saved by the repo yet
        if not result:
            return result

        result = ResultList(results).to_result()
        if result:
            return Result(True, 'Blender setup instance created successfully', self)
        else:
            return result

    def verify_components_against_repo(self, repo) -> Result:
        raise NotImplementedError

    def add_blender_config(self) -> Result:
        """
        Add a Blender config directory to the setup directory. The Blender config directory is used as a custom config
        for Blender if proper Blender env var points to it.

        :return: a Result object indicating if the addition is successful
        """
        blender_config = self.data_path / self.setup_blender_config_path
        if not blender_config.exists():
            result = SF.create_target_dir(blender_config)
            if not result:
                return result
            result = self.save_config_json()
            if not result:
                return result
        if blender_config.exists():
            self.setup_json['blender_config'] = True
            return Result(True, f'Blender config created at {blender_config}', blender_config)
        else:
            self.setup_json['blender_config'] = False
            return Result(False, f'Error adding Blender config to {blender_config}')

    def remove_blender_config(self) -> Result:
        """
        Remove the Blender config directory in the setup directory.

        :return: a Result object indicating if the removal is successful
        """
        blender_config = self.data_path / self.setup_blender_config_path
        if blender_config.exists():
            result = SF.remove_target_path(blender_config)
            if not result:
                return result
            result = self.save_config_json()
            if not result:
                return result
        if blender_config.exists():
            self.setup_json['blender_config'] = True
            return Result(False, f'Error removing Blender config at {blender_config}', blender_config)
        else:
            self.setup_json['blender_config'] = False
            return Result(True, f'Blender config removed at {blender_config}')

    def _get_component_belonging_attr(self, component: Component) -> (dict, Path) or (None, None):
        """
        Get the attribute and directory that a component belongs to.

        :param component: a Component object

        :return: a tuple of the attribute and directory that the component belongs to
        """
        for key, val in self.component_class_dict.items():
            class_list = val['classes']
            if component.__class__ in class_list:
                if hasattr(self, key):
                    return getattr(self, key), val['dir']
        return None, None

    @Dillable.save_dill
    def add_component(self, component: Component) -> Result:
        """
        Add a component to the setup. The component must be a subclass of BlenderAddon or BlenderScript. The component
        will be deployed to the corresponding directory in the setup directory.

        :param component: a Component object
        :return: a Result object indicating if the addition is successful
        """
        attr, dir = self._get_component_belonging_attr(component)
        if None not in (attr, dir):
            if hash(component) not in attr:
                result = component.deploy(self.data_path / dir)
                if not result:
                    return result
                deployed_path = result.data
                attr[hash(component)] = deployed_path.relative_to(self.data_path).as_posix()

                # Update the setup config
                result = self.save_config_json()
                if not result:
                    return result

                return Result(True)
            else:
                return Result(False, f'Component {component} already exists in the setup')
        else:
            return Result(False, f'Component {component} is not supported in the setup')

    @Dillable.save_dill
    def remove_component(self, component: Component) -> Result:
        """
        Remove a component from the setup. The component must be a subclass of BlenderAddon or BlenderScript. The
        component will be removed from the corresponding directory in the setup directory.

        :param component: a Component object
        :return: a Result object indicating if the removal is successful
        """
        attr, dir = self._get_component_belonging_attr(component)
        if None not in (attr, dir):
            if hash(component) in attr:
                result = SF.remove_target_path(self.data_path / attr[hash(component)])
                if not result:
                    return result
                del attr[hash(component)]

                # Update the setup config
                result = self.save_config_json()
                if not result:
                    return result

                return Result(True)
            else:
                return Result(False, f'Component {component} doesn\'t exist in the setup')
        else:
            return Result(False, f'Component {component} is not supported in the setup')

    @Dillable.save_dill
    def update_component(self, component: Component) -> Result:
        raise NotImplementedError

    def save_config_json(self) -> Result:
        """
        Save the setup config file and the dill file. The dill file is saved only if this instance has been saved to the
        repo and the save_dill flag is set to True.

        :return: a Result object indicating if the saving is successful
        """
        # Save setup json file
        setup_json_path = self.data_path / self.setup_json_path
        try:
            with open(setup_json_path, 'w') as f:
                json.dump(self.setup_json, f, indent=4)
        except Exception as e:
            return Result(False, f'Error writing to {setup_json_path}')
        return Result(True)

    def __str__(self):
        return f'{self.__class__.__name__}: {self.name}'


class BlenderSetupManager:

    def __new__(cls):
        raise NotImplementedError

    @classmethod
    def create(cls, repo_dir: str or Path, name: str) -> Result:
        """
        Create a BlenderSetup object.

        :param repo_dir: a str or Path object of the path to the repo directory
        :param name: a str of the name of the Blender setup

        :return: a Result object indicating if the creation is successful, the message generated during the creation,
                 and this object if successful
        """
        return BlenderSetup(repo_dir, name).create_instance()
