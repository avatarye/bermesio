import json
import os
from pathlib import Path
import shutil

from commons.common import Result, Dillable, blog, SharedFunctions as SF
from components.blender_addon import (BlenderAddon, BlenderZippedAddon, BlenderDirectoryAddon, BlenderSingleFileAddon,
                                      BlenderDevDirectoryAddon, BlenderDevSingleFileAddon, BlenderAddonManager)
from components.blender_script import (BlenderRegularScript, BlenderStartupScript, BlenderDevRegularScript,
                                       BlenderDevStartupScript, BlenderScriptManager)
from config import Config


class BlenderSetup(Dillable):

    # Config JSON file name
    setup_config_file_name = '.blender_setup.json'
    # Custom Blender config directory
    setup_blender_config_path = Path('config')
    # Addon directory
    setup_addon_path = Path('scripts/addons')
    # Startup script directory
    setup_startup_script_path = Path('scripts/startup')
    # Additional regular script directory, must be the same as BlenderScript class's
    setup_regular_scripts_path = Path(f'scripts/{Config.app_name.lower()}_scripts')

    config = {}

    def __init__(self, setup_path: str or Path):
        super().__init__()
        self.setup_path = Path(setup_path)
        if self.setup_path.exists():
            self.config = self._get_setup_config()
            self.name = self.setup_path.name
            self._verify_and_link_setup_components()

    def _get_setup_config(self) -> dict:
        config_path = self.setup_path / self.setup_config_file_name
        if config_path.exists():
            with open(self.setup_path / self.setup_config_file_name, 'r') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f'Blender setup config file not found at {config_path}')

    def _verify_and_link_setup_components(self):


        self.blender_config: Path = self._get_setup_config()
        self.blender_addons: [BlenderAddon] = self._get_blender_addons()
        self.dev_addons: [BlenderAddon] = self._get_dev_addons()
        self.regular_scripts: [BlenderRegularScript] = self._get_regular_scripts()
        self.startup_scripts: [BlenderStartupScript] = self._get_startup_scripts()
        self.dev_regular_scripts: [BlenderDevRegularScript] = self._get_dev_regular_scripts()
        self.dev_startup_scripts: [BlenderDevStartupScript] = self._get_dev_startup_scripts()

    def __str__(self):
        return f'BlenderSetup: {self.name}'

    def __eq__(self, other: 'BlenderSetup'):
        """
        The equality of 2 BlenderSetup objects is determined by the addon path instead of the instance itself. If the
        instance equality is required, use compare_uuid() from Dillable class.

        :param other: another BlenderSetup object

        :return: True if the Blender script path of this instance is the same as the other instance, otherwise False
        """
        if issubclass(other.__class__, BlenderSetup):
            return self.setup_path == other.setup_path
        return False

    def __hash__(self):
        return hash(self.setup_path.as_posix())


class BlenderSetupManager:

    def __new__(cls):
        raise NotImplementedError

    @classmethod
    def create_blender_setup(cls, setup_path, delete_existing=False) -> Result:
        pass
