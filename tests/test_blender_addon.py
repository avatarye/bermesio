from packaging.version import Version

from components.blender_addon import BlenderZippedAddon, BlenderDirectoryAddon

from testing_common import *


def test_blender_zipped_addon_class():
    addon_path = r'c:\TechDepot\AvatarTools\Blender\Addons\Fluent\fluent_1_5_2.zip'
    addon = BlenderZippedAddon(addon_path)
    assert addon.name == 'Fluent'
    assert addon.version == Version('1.5.2')
    assert addon.blender_version == Version('2.91.0')
    assert addon.description == 'Hard surface modeling tools'
    assert is_dillable(addon), 'BlenderZippedAddon should be picklable'


def test_blender_directory_addon_class():
    addon_path = r'c:\TechDepot\AvatarTools\Blender\Addons\Fluent\fluent'
    addon = BlenderDirectoryAddon(addon_path)
    assert addon.name == 'Fluent'
    assert addon.version == Version('1.5.2')
    assert addon.blender_version == Version('2.91.0')
    assert addon.description == 'Hard surface modeling tools'
    assert is_dillable(addon), 'BlenderDirectoryAddon should be picklable'
