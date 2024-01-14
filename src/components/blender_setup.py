import copy
import json
import os
from pathlib import Path
import shutil

from commons.common import Result, ResultList, blog, SharedFunctions as SF
from components.blender_addon import (BlenderAddon, BlenderZippedAddon, BlenderDirectoryAddon, BlenderSingleFileAddon,
                                      BlenderDevDirectoryAddon, BlenderDevSingleFileAddon, BlenderAddonManager)
from components.blender_script import (BlenderRegularScript, BlenderStartupScript, BlenderDevRegularScript,
                                       BlenderDevStartupScript, BlenderScriptManager)
from components.component import Component
from config import Config


class BlenderSetup(Component):

    # Setup config file name
    setup_json_path = Path(f'.blender_setup.json')
    # Custom Blender config directory
    setup_blender_config_path = Path('config')
    # Custom disabled Blender config directory
    setup_disabled_blender_config_path = Path('config_disabled')
    # Inherent "Scripts" directory to a Blender setup
    setup_scripts_path = Path('scripts')
    # Addon directory
    setup_addon_path = Path('scripts/addons')
    # Startup script directory
    setup_startup_script_path = Path('scripts/startup')
    # Additional regular script directory, must be the same as BlenderScript class's
    setup_regular_scripts_path = Path(f'scripts/{Config.app_name.lower()}_scripts')

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
            'dir': setup_scripts_path,
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
        setup_json_path = self.data_path / self.setup_json_path
        if setup_json_path.exists():
            with open(self.data_path / self.setup_json_path, 'r') as f:
                return json.load(f)
        else:
            return  {
                'blender_config': 'not_set',  # 'not_set', 'enabled', 'disabled', or 'error'
                'released_addons': self.released_addons,
                'dev_addons': self.dev_addons,
                'startup_scripts': self.startup_scripts,
                'regular_scripts': self.regular_scripts,
                'dev_startup_scripts': self.dev_startup_scripts,
                'dev_regular_scripts': self.dev_regular_scripts,
            }

    def create_instance(self) -> Result:
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

        def get_blender_config_status() -> Result:
            blender_config = self.data_path / self.setup_blender_config_path
            blender_disabled_config = self.data_path / self.setup_disabled_blender_config_path
            if blender_config.exists() and not blender_disabled_config.exists():
                return Result(True, '', 'enabled')
            elif not blender_config.exists() and blender_disabled_config.exists():
                return Result(True, '', 'disabled')
            elif not blender_config.exists() and not blender_disabled_config.exists():
                return Result(True, '', 'not_set')
            else:
                return Result(False, f'Blender both enabled and disabled config directories found', 'error')

        def verify_component_dict(component_dict) -> Result:
            if len(component_dict) == 0:
                return Result(True)
            results = []
            for hash_, rel_path in component_dict.items():
                if not (self.data_path / rel_path).exists():
                    results.append(Result(False, f'Component {rel_path} not found'))
            return ResultList(results).to_result()

        results = []
        # Check Blender config
        result = get_blender_config_status()
        self.setup_json['blender_config'] = result.data
        results.append(result)

        # Check addons
        results.append(verify_component_dict(self.setup_json['released_addons']))
        results.append(verify_component_dict(self.setup_json['dev_addons']))

        # Check scripts
        results.append(verify_component_dict(self.setup_json['startup_scripts']))
        results.append(verify_component_dict(self.setup_json['regular_scripts']))
        results.append(verify_component_dict(self.setup_json['dev_startup_scripts']))
        results.append(verify_component_dict(self.setup_json['dev_regular_scripts']))

        # Update the setup config
        result = self.save(save_dill=False)  # Don't save dill file here, it may not be saved by the repo yet
        if not result:
            return result

        result = ResultList(results).to_result()
        if result:
            return Result(True, 'Blender setup instance created successfully', self)
        else:
            return result

    def change_blender_config(self, status) -> Result:
        blender_config_path = self.data_path / self.setup_blender_config_path
        blender_disabled_config_path = self.data_path / self.setup_disabled_blender_config_path
        if blender_config_path.exists() and blender_disabled_config_path.exists():
            result = Result(False, f'Both Blender config and disabled config directories found', 'error')
        # Delete both config and disabled config
        if status == 'not_set':
            result = (SF.remove_target_path(self.data_path / self.setup_blender_config_path) and
                      SF.remove_target_path(self.data_path / self.setup_disabled_blender_config_path))
            if result:
                result = Result(True, '', 'not_set')
            else:
                result = Result(False, f'Error deleting both Blender config or disabled config directories', 'error')
        # Enable Blender config
        elif status == 'enabled':
            if blender_config_path.exists() and not blender_disabled_config_path.exists():  # Already enabled
                result = Result(True, '', 'enabled')
            elif not blender_config_path.exists() and blender_disabled_config_path.exists():  # Restore from disabled
                try:
                    shutil.move(blender_disabled_config_path, blender_config_path)
                    result = Result(True, '', 'enabled')
                except Exception as e:
                    result = Result(False, f'Error moving {blender_disabled_config_path} to {blender_config_path}',
                                    'error')
            elif not blender_config_path.exists() and not blender_disabled_config_path.exists():  # Create new
                result = SF.create_target_dir(blender_config_path)
                if result:
                    result = Result(True, '', 'enabled')
                else:
                    result = Result(False, f'Error creating {blender_config_path}', 'error')
        # Disable Blender config
        elif status == 'disabled':
            if blender_config_path.exists() and not blender_disabled_config_path.exists():  # Disable
                try:
                    shutil.move(blender_config_path, blender_disabled_config_path)
                    result = Result(True, '', 'disabled')
                except Exception as e:
                    result = Result(False, f'Error moving {blender_config_path} to {blender_disabled_config_path}',
                                    'error')
            elif not blender_config_path.exists() and blender_disabled_config_path.exists():  # Already disabled
                result = Result(True, '', 'disabled')
            elif not blender_config_path.exists() and not blender_disabled_config_path.exists():  # Neither exists
                result = Result(True, '', 'not_set')
        self.setup_json['blender_config'] = result.data

        # Update the setup config
        save_result = self.save()
        if not save_result:
            return save_result

        return result

    def _get_component_belonging_attr(self, component: Component) -> (dict, Path) or (None, None):
        for key, val in self.component_class_dict.items():
            class_list = val['classes']
            if component.__class__ in class_list:
                if hasattr(self, key):
                    return getattr(self, key), val['dir']
        return None, None

    def add_component(self, component: Component) -> Result:
        attr, dir = self._get_component_belonging_attr(component)
        if None not in (attr, dir):
            if hash(component) not in attr:
                result = component.deploy(self.data_path / dir)
                if not result:
                    return result
                deployed_path = result.data
                attr[hash(component)] = deployed_path.relative_to(self.data_path).as_posix()

                # Update the setup config
                result = self.save()
                if not result:
                    return result


                return Result(True)
            else:
                return Result(False, f'Component {component} already exists in the setup')
        else:
            return Result(False, f'Component {component} is not supported in the setup')

    def remove_component(self, component: Component) -> Result:

        # Update the setup config
        result = self.save()
        if not result:
            return result

    def update_component(self, component: Component) -> Result:

        # Update the setup config
        result = self.save()
        if not result:
            return result

    def save(self, save_dill=True) -> Result:
        # Save setup config file
        setup_json_path = self.data_path / self.setup_json_path
        try:
            with open(setup_json_path, 'w') as f:
                json.dump(self.setup_json, f, indent=4)
        except Exception as e:
            return Result(False, f'Error writing to {setup_json_path}')
        # Save dill file
        if save_dill:
            result = self.resave_to_disk()
            if not result:
                return result
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
