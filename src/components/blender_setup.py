from commons.common import Result, Dillable, blog, SharedFunctions as SF
from components.blender_addon import (BlenderZippedAddon, BlenderDirectoryAddon, BlenderSingleFileAddon,
                                      BlenderDevDirectoryAddon, BlenderDevSingleFileAddon, BlenderAddonManager)
from components.blender_script import (BlenderRegularScript, BlenderStartupScript, BlenderDevRegularScript,
                                       BlenderDevStartupScript, BlenderScriptManager)


class BlenderSetup(Dillable):

    def __init__(self, name, depot_setup_dir, init_dict=None):
        super().__init__()
        self.name = self._get_validated_setup_name(name)

    def _get_validated_setup_name(self, name) -> str:
        if SF.is_valid_name_for_path(name):
            return name
        else:
            raise ValueError(f'Invalid setup name {name}')



class BlenderSetupManager:

    def __new__(cls):
        raise NotImplementedError

    @classmethod
    def create_blender_setup(cls, name, depot_setup_dir, init_dict=None):
        return BlenderSetup(name, depot_setup_dir, init_dict)