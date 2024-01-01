from packaging.version import Version
import shutil

from components.blender_addon import BlenderZippedAddon, BlenderDirectoryAddon, BlenderSingleFileAddon

from testing_common import *


def test_blender_zipped_addon_class():
    copy_to_dir = Path(__file__).parent / 'test_blender_zipped_addon'
    # Scenario 1: addon_path is a zip file
    addon_path = Path(TESTDATA['blender_addon|zip|path'])
    addon = BlenderZippedAddon(addon_path, repo_dir=copy_to_dir)
    assert addon.name == TESTDATA['blender_addon|zip|name']
    assert addon.version == Version(TESTDATA['blender_addon|zip|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|zip|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|zip|description']
    copied_addon_path = copy_to_dir / addon.repo_zip_file_name
    assert copied_addon_path.exists(), 'BlenderZippedAddon should be able to copy itself to a directory'
    assert is_dillable(addon), 'BlenderZippedAddon should be picklable'
    if copied_addon_path.exists():
        shutil.rmtree(copied_addon_path.parent)

    # Scenario 2: addon_path is a zip file without a top dir
    addon_path = Path(TESTDATA['blender_addon|zip_no_top_dir|path'])
    addon = BlenderZippedAddon(addon_path, repo_dir=copy_to_dir)
    assert addon.name == TESTDATA['blender_addon|zip_no_top_dir|name']
    assert addon.version == Version(TESTDATA['blender_addon|zip_no_top_dir|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|zip_no_top_dir|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|zip_no_top_dir|description']
    copied_addon_path = copy_to_dir / addon.repo_zip_file_name
    assert copied_addon_path.exists(), 'BlenderZippedAddon should be able to copy itself to a directory'
    assert is_dillable(addon), 'BlenderZippedAddon should be picklable'
    if copied_addon_path.exists():
        shutil.rmtree(copied_addon_path.parent)

    # Scenario 3: addon_path is a single file zip file
    addon_path = Path(TESTDATA['blender_addon|single_file_zip|path'])
    addon = BlenderZippedAddon(addon_path, repo_dir=copy_to_dir)
    assert addon.name == TESTDATA['blender_addon|single_file_zip|name']
    assert addon.version == Version(TESTDATA['blender_addon|single_file_zip|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|single_file_zip|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|single_file_zip|description']
    copied_addon_path = copy_to_dir / addon.repo_zip_file_name
    assert copied_addon_path.exists(), 'BlenderZippedAddon should be able to copy itself to a directory'
    assert is_dillable(addon), 'BlenderZippedAddon should be picklable'
    if copied_addon_path.exists():
        shutil.rmtree(copied_addon_path.parent)


def test_blender_directory_addon_class():
    copy_to_dir = Path(__file__).parent / 'test_blender_zipped_addon'
    # Scenario 1: addon_path is a dir
    addon_path = Path(TESTDATA['blender_addon|dir|path'])
    addon = BlenderDirectoryAddon(addon_path, repo_dir=copy_to_dir)
    assert addon.name == TESTDATA['blender_addon|dir|name']
    assert addon.version == Version(TESTDATA['blender_addon|dir|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|dir|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|dir|description']
    copied_addon_path = copy_to_dir / addon.repo_zip_file_name
    assert copied_addon_path.exists(), 'BlenderZippedAddon should be able to copy itself to a directory'
    assert is_dillable(addon), 'BlenderZippedAddon should be picklable'
    if copied_addon_path.exists():
        shutil.rmtree(copied_addon_path.parent)

    # Scenario 2: addon_path is a dir with single file
    copy_to_dir = Path(__file__).parent / 'test_blender_zipped_addon'
    addon_path = Path(TESTDATA['blender_addon|single_file_dir|path'])
    addon = BlenderDirectoryAddon(addon_path, repo_dir=copy_to_dir)
    assert addon.name == TESTDATA['blender_addon|single_file_dir|name']
    assert addon.version == Version(TESTDATA['blender_addon|single_file_dir|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|single_file_dir|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|single_file_dir|description']
    copied_addon_path = copy_to_dir / addon.repo_zip_file_name
    assert copied_addon_path.exists(), 'BlenderZippedAddon should be able to copy itself to a directory'
    assert addon.addon_path == copied_addon_path
    assert is_dillable(addon), 'BlenderZippedAddon should be picklable'
    if copied_addon_path.exists():
        shutil.rmtree(copied_addon_path.parent)


def test_blender_single_file_addon_class():
    copy_to_dir = Path(__file__).parent / 'test_blender_zipped_addon'
    addon_path = Path(TESTDATA['blender_addon|single_file|path'])
    addon = BlenderSingleFileAddon(addon_path, repo_dir=copy_to_dir)
    assert addon.name == TESTDATA['blender_addon|single_file|name']
    assert addon.version == Version(TESTDATA['blender_addon|single_file|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|single_file|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|single_file|description']
    copied_addon_path = copy_to_dir / addon.repo_zip_file_name
    assert copied_addon_path.exists(), 'BlenderZippedAddon should be able to copy itself to a directory'
    assert addon.addon_path == copied_addon_path
    assert is_dillable(addon), 'BlenderZippedAddon should be picklable'
    if copied_addon_path.exists():
        shutil.rmtree(copied_addon_path.parent)
