from pathlib import Path

from packaging.version import Version
import shutil

from components.blender_addon import (BlenderZippedAddon, BlenderDirectoryAddon, BlenderSingleFileAddon,
                                      BlenderDevDirectoryAddon, BlenderDevSingleFileAddon, BlenderAddonManager)

from testing_common import TESTDATA, is_dillable


def test_blender_zipped_addon_class():
    copy_to_dir = Path(__file__).parent / 'test_blender_addon'
    deploy_to_dir = Path(__file__).parent / 'test_blender_addon' /'deploy'
    # Scenario 1: addon_path is a zip file
    addon_path = Path(TESTDATA['blender_addon|zip|path'])
    result = BlenderAddonManager.create_blender_addon(addon_path, repo_dir=copy_to_dir)
    assert result, 'BlenderAddonManager should be able to create BlenderZippedAddon'
    addon = result.data
    assert addon.name == TESTDATA['blender_addon|zip|name']
    assert addon.version == Version(TESTDATA['blender_addon|zip|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|zip|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|zip|description']
    copied_addon_path = copy_to_dir / addon.repo_zip_file_name
    assert copied_addon_path.exists(), 'BlenderZippedAddon should be able to copy itself to a directory'
    addon.deploy(deploy_to_dir)
    deployed_addon_paths = [f for f in deploy_to_dir.iterdir() if f.is_dir()]
    assert len(deployed_addon_paths) == 1, 'BlenderZippedAddon should be able to deploy itself to a directory'
    assert is_dillable(addon), 'BlenderZippedAddon should be picklable'
    if copied_addon_path.exists():
        shutil.rmtree(copied_addon_path.parent)

    # Scenario 2: addon_path is a zip file without a top dir
    addon_path = Path(TESTDATA['blender_addon|zip_no_top_dir|path'])
    result = BlenderAddonManager.create_blender_addon(addon_path, repo_dir=copy_to_dir)
    assert result, 'BlenderAddonManager should be able to create BlenderZippedAddon'
    addon = result.data
    assert addon.name == TESTDATA['blender_addon|zip_no_top_dir|name']
    assert addon.version == Version(TESTDATA['blender_addon|zip_no_top_dir|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|zip_no_top_dir|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|zip_no_top_dir|description']
    copied_addon_path = copy_to_dir / addon.repo_zip_file_name
    assert copied_addon_path.exists(), 'BlenderZippedAddon should be able to copy itself to a directory'
    addon.deploy(deploy_to_dir)
    deployed_addon_paths = [f for f in deploy_to_dir.iterdir() if f.is_dir()]
    assert len(deployed_addon_paths) == 1, 'BlenderZippedAddon should be able to deploy itself to a directory'
    assert is_dillable(addon), 'BlenderZippedAddon should be picklable'
    if copied_addon_path.exists():
        shutil.rmtree(copied_addon_path.parent)

    # Scenario 3: addon_path is a single file zip file
    addon_path = Path(TESTDATA['blender_addon|single_file_zip|path'])
    result = BlenderAddonManager.create_blender_addon(addon_path, repo_dir=copy_to_dir)
    assert result, 'BlenderAddonManager should be able to create BlenderZippedAddon'
    addon = result.data
    assert addon.name == TESTDATA['blender_addon|single_file_zip|name']
    assert addon.version == Version(TESTDATA['blender_addon|single_file_zip|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|single_file_zip|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|single_file_zip|description']
    copied_addon_path = copy_to_dir / addon.repo_zip_file_name
    assert copied_addon_path.exists(), 'BlenderZippedAddon should be able to copy itself to a directory'
    addon.deploy(deploy_to_dir)
    deployed_addon_paths = [f for f in deploy_to_dir.iterdir() if f.suffix == '.py']
    assert len(deployed_addon_paths) == 1, 'BlenderZippedAddon should be able to deploy itself to a directory'
    assert is_dillable(addon), 'BlenderZippedAddon should be picklable'
    if copied_addon_path.exists():
        shutil.rmtree(copied_addon_path.parent)

    # Scenario 4: addon_path is a single file zip file with the file at one level down
    addon_path = Path(TESTDATA['blender_addon|single_file_zip_one_level_down|path'])
    result = BlenderAddonManager.create_blender_addon(addon_path, repo_dir=copy_to_dir)
    assert result, 'BlenderAddonManager should be able to create BlenderZippedAddon'
    addon = result.data
    assert addon.name == TESTDATA['blender_addon|single_file_zip_one_level_down|name']
    assert addon.version == Version(TESTDATA['blender_addon|single_file_zip_one_level_down|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|single_file_zip_one_level_down|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|single_file_zip_one_level_down|description']
    copied_addon_path = copy_to_dir / addon.repo_zip_file_name
    assert copied_addon_path.exists(), 'BlenderZippedAddon should be able to copy itself to a directory'
    addon.deploy(deploy_to_dir)
    deployed_addon_paths = [f for f in deploy_to_dir.iterdir() if f.suffix == '.py']
    assert len(deployed_addon_paths) == 1, 'BlenderZippedAddon should be able to deploy itself to a directory'
    assert is_dillable(addon), 'BlenderZippedAddon should be picklable'
    if copied_addon_path.exists():
        shutil.rmtree(copied_addon_path.parent)


def test_blender_directory_addon_class():
    copy_to_dir = Path(__file__).parent / 'test_blender_addon'
    deploy_to_dir = Path(__file__).parent / 'test_blender_addon' /'deploy'
    # Scenario 1: addon_path is a regular addon
    addon_path = Path(TESTDATA['blender_addon|dir|path'])
    result = BlenderAddonManager.create_blender_addon(addon_path, repo_dir=copy_to_dir)
    assert result, 'BlenderAddonManager should be able to create BlenderDirectoryAddon'
    addon = result.data
    assert addon.name == TESTDATA['blender_addon|dir|name']
    assert addon.version == Version(TESTDATA['blender_addon|dir|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|dir|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|dir|description']
    copied_addon_path = copy_to_dir / addon.repo_zip_file_name
    assert copied_addon_path.exists(), 'BlenderDirectoryAddon should be able to copy itself to a directory'
    addon.deploy(deploy_to_dir)
    deployed_addon_paths = [f for f in deploy_to_dir.iterdir() if f.is_dir()]
    assert len(deployed_addon_paths) == 1, 'BlenderZippedAddon should be able to deploy itself to a directory'
    assert is_dillable(addon), 'BlenderDirectoryAddon should be picklable'
    if copied_addon_path.exists():
        shutil.rmtree(copied_addon_path.parent)

    # Scenario 2: addon_path is a single-file addon
    addon_path = Path(TESTDATA['blender_addon|single_file_dir|path'])
    result = BlenderAddonManager.create_blender_addon(addon_path, repo_dir=copy_to_dir)
    assert result, 'BlenderAddonManager should be able to create BlenderDirectoryAddon'
    addon = result.data
    assert addon.name == TESTDATA['blender_addon|single_file_dir|name']
    assert addon.version == Version(TESTDATA['blender_addon|single_file_dir|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|single_file_dir|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|single_file_dir|description']
    copied_addon_path = copy_to_dir / addon.repo_zip_file_name
    assert copied_addon_path.exists(), 'BlenderDirectoryAddon should be able to copy itself to a directory'
    assert addon.addon_path == copied_addon_path
    addon.deploy(deploy_to_dir)
    deployed_addon_paths = [f for f in deploy_to_dir.iterdir() if f.suffix == '.py']
    assert len(deployed_addon_paths) == 1, 'BlenderDirectoryAddon should be able to deploy itself to a directory'
    assert is_dillable(addon), 'BlenderDirectoryAddon should be picklable'
    if copied_addon_path.exists():
        shutil.rmtree(copied_addon_path.parent)


def test_blender_single_file_addon_class():
    copy_to_dir = Path(__file__).parent / 'test_blender_addon'
    deploy_to_dir = Path(__file__).parent / 'test_blender_addon' /'deploy'
    addon_path = Path(TESTDATA['blender_addon|single_file|path'])
    result = BlenderAddonManager.create_blender_addon(addon_path, repo_dir=copy_to_dir)
    assert result, 'BlenderAddonManager should be able to create BlenderSingleFileAddon'
    addon = result.data
    assert addon.name == TESTDATA['blender_addon|single_file|name']
    assert addon.version == Version(TESTDATA['blender_addon|single_file|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|single_file|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|single_file|description']
    copied_addon_path = copy_to_dir / addon.repo_zip_file_name
    assert copied_addon_path.exists(), 'BlenderSingleFileAddon should be able to copy itself to a directory'
    assert addon.addon_path == copied_addon_path
    addon.deploy(deploy_to_dir)
    deployed_addon_paths = [f for f in deploy_to_dir.iterdir() if f.suffix == '.py']
    assert len(deployed_addon_paths) == 1, 'BlenderSingleFileAddon should be able to deploy itself to a directory'
    assert is_dillable(addon), 'BlenderSingleFileAddon should be picklable'
    if copied_addon_path.exists():
        shutil.rmtree(copied_addon_path.parent)


def test_blender_dev_directory_addon_class():
    deploy_to_dir = Path(__file__).parent / 'test_blender_addon' /'deploy'

    addon_path = Path(TESTDATA['blender_addon|dev_dir|path'])
    result = BlenderAddonManager.create_blender_dev_addon(addon_path)
    assert result, 'BlenderAddonManager should be able to create BlenderDevDirectoryAddon'
    addon = result.data
    assert addon.name == TESTDATA['blender_addon|dev_dir|name']
    assert addon.version == Version(TESTDATA['blender_addon|dev_dir|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|dev_dir|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|dev_dir|description']
    addon.deploy(deploy_to_dir)
    deployed_addon_paths = [f for f in deploy_to_dir.iterdir() if f.is_dir()]
    assert len(deployed_addon_paths) == 1, 'BlenderZippedAddon should be able to symlink to a directory'
    assert is_dillable(addon), 'BlenderDevDirectoryAddon should be picklable'
    if deploy_to_dir.exists():
        shutil.rmtree(deploy_to_dir.parent)


def test_blender_dev_single_file_addon_class():
    deploy_to_dir = Path(__file__).parent / 'test_blender_addon' /'deploy'

    addon_path = Path(TESTDATA['blender_addon|single_file|path'])
    result = BlenderAddonManager.create_blender_dev_addon(addon_path)
    assert result, 'BlenderAddonManager should be able to create BlenderDevSingleFileAddon'
    addon = result.data
    assert addon.name == TESTDATA['blender_addon|single_file|name']
    assert addon.version == Version(TESTDATA['blender_addon|single_file|version'])
    assert addon.blender_version_min == Version(TESTDATA['blender_addon|single_file|blender_version_min'])
    assert addon.description == TESTDATA['blender_addon|single_file|description']
    addon.deploy(deploy_to_dir)
    deployed_addon_paths = [f for f in deploy_to_dir.iterdir() if f.is_file()]
    assert len(deployed_addon_paths) == 1, 'BlenderDevSingleFileAddon should be able to symlink to a file'
    assert is_dillable(addon), 'BlenderDevSingleFileAddon should be picklable'
    if deploy_to_dir.exists():
        shutil.rmtree(deploy_to_dir.parent)


def test_blender_addon_manager_class():
    # Regular addon types
    result = BlenderAddonManager.detect_addon_type(Path(TESTDATA['blender_addon|zip|path']))
    assert result and result.data == BlenderZippedAddon, 'detect_addon_type should return BlenderZippedAddon'
    result = BlenderAddonManager.detect_addon_type(Path(TESTDATA['blender_addon|dir|path']))
    assert result and result.data == BlenderDirectoryAddon, 'detect_addon_type should return BlenderDirectoryAddon'
    result = BlenderAddonManager.detect_addon_type(Path(TESTDATA['blender_addon|single_file_dir|path']))
    assert result and result.data == BlenderDirectoryAddon, 'detect_addon_type should return BlenderDirectoryAddon'
    result = BlenderAddonManager.detect_addon_type(Path(TESTDATA['blender_addon|zip_no_top_dir|path']))
    assert result and result.data == BlenderZippedAddon, 'detect_addon_type should return BlenderZippedAddon'
    result = BlenderAddonManager.detect_addon_type(Path(TESTDATA['blender_addon|single_file_zip|path']))
    assert result and result.data == BlenderZippedAddon, 'detect_addon_type should return BlenderZippedAddon'
    result = BlenderAddonManager.detect_addon_type(Path(TESTDATA['blender_addon|single_file|path']))
    assert result and result.data == BlenderSingleFileAddon, 'detect_addon_type should return BlenderSingleFileAddon'

    # Dev addon types
    result = BlenderAddonManager.detect_dev_addon_type(Path(TESTDATA['blender_addon|dev_dir|path']))
    assert result and result.data == BlenderDevDirectoryAddon, 'detect_addon_type should return BlenderDevDirectoryAddon'
    result = BlenderAddonManager.detect_dev_addon_type(Path(TESTDATA['blender_addon|single_file|path']))
    assert result and result.data == BlenderDevSingleFileAddon, 'detect_addon_type should return BlenderDevSingleFileAddon'


