from pathlib import Path
from zipfile import ZipFile

from packaging.version import Version
import shutil

from components.blender_addon import BlenderAddonManager

from testing_common import TESTDATA, is_dillable, get_repo


def test_blender_released_addon_classes():
    repo = get_repo()
    deploy_dir = Path(TESTDATA['temp_dir']) / 'deploy'
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)

    # Test non-single-file addon
    test_addon_jsons = [TESTDATA['blender_addon|zip'], TESTDATA['blender_addon|zip_no_top_dir'],
                        TESTDATA['blender_addon|dir']]
    for test_addon_json in test_addon_jsons:
        # Test creating addon
        result = BlenderAddonManager.create_blender_addon(test_addon_json['path'])
        assert result, 'BlenderAddonManager should be able to create a BlenderAddon object'
        addon = result.data
        result = repo.add_component(addon)
        assert result, 'Error adding BlenderAddon to repo'
        # Test BlenderAddon attributes
        assert addon.name == test_addon_json['name'], 'BlenderAddon name does not match'
        assert addon.version == Version(test_addon_json['version']), 'BlenderAddon version does not match'
        assert addon.blender_version_min == Version(test_addon_json['blender_version_min']), \
            'BlenderAddon blender_version_min does not match'
        assert addon.description == test_addon_json['description'], \
            'BlenderAddon description does not match'
        # Test copying addon
        for addon in repo.blender_addon_repo.pool.values():
            assert addon.data_path.exists(), 'BlenderAddon data path not copied to repo'
        with ZipFile(addon.data_path, 'r') as z:
            init_files = [f for f in z.namelist() if f.endswith('__init__.py')]
            assert all(['/' in f or '\\' in f for f in init_files]), 'Addon should have top dir'
        # Test deploying addon
        result = addon.deploy(deploy_dir)
        assert result, 'Error deploying BlenderAddon as a symlink'
        deployed_addon_path = deploy_dir / addon.name
        assert deployed_addon_path.exists(), 'Zipped addon should be deployed to deploy dir'
        repo.remove_component(addon)
        assert len(repo.blender_addon_repo.pool) == 0, 'BlenderAddon should be removed from repo'
        if deployed_addon_path.is_dir():
            shutil.rmtree(deployed_addon_path)
        else:
            deployed_addon_path.unlink()

        assert is_dillable(addon), 'BlenderAddon should be dillable'

    # Test single-file addon
    test_addon_jsons = [TESTDATA['blender_addon|single_file_zip'],
                        TESTDATA['blender_addon|single_file_zip_one_level_down'],
                        TESTDATA['blender_addon|single_file_dir']]
    for test_addon_json in test_addon_jsons:
        # Test creating addon
        result = BlenderAddonManager.create_blender_addon(test_addon_json['path'])
        assert result, 'BlenderAddonManager should be able to create a BlenderAddon object'
        addon = result.data
        result = repo.add_component(addon)
        assert result, 'Error adding BlenderAddon to repo'
        # Test BlenderAddon attributes
        assert addon.name == test_addon_json['name'], 'BlenderAddon name does not match'
        assert addon.version == Version(test_addon_json['version']), 'BlenderAddon version does not match'
        assert addon.blender_version_min == Version(test_addon_json['blender_version_min']), \
            'BlenderAddon blender_version_min does not match'
        assert addon.description == test_addon_json['description'], \
            'BlenderAddon description does not match'
        # Test copying addon
        for addon in repo.blender_addon_repo.pool.values():
            assert addon.data_path.exists(), 'BlenderAddon data path not copied to repo'
        with ZipFile(addon.data_path, 'r') as z:
            assert len(z.namelist()) == 1, 'Single-file addon should have only one file'
            assert '/' not in z.namelist()[0] and '\\' not in z.namelist()[0], \
                'Single-file addon should not have top dir'
            addon_py_file = Path(z.namelist()[0])
        # Test deploying addon
        result = addon.deploy(deploy_dir)
        assert result, 'Error deploying BlenderAddon as a symlink'
        deployed_addon_path = deploy_dir / addon_py_file.name
        assert deployed_addon_path.exists(), 'Zipped addon should be deployed to deploy dir'
        repo.remove_component(addon)
        assert len(repo.blender_addon_repo.pool) == 0, 'BlenderAddon should be removed from repo'
        if deployed_addon_path.is_dir():
            shutil.rmtree(deployed_addon_path)
        else:
            deployed_addon_path.unlink()

        assert is_dillable(addon), 'BlenderAddon should be dillable'


def test_blender_dev_addon_classes():
    repo = get_repo()
    deploy_dir = Path(TESTDATA['temp_dir']) / 'deploy'
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)

    # Test non-single-file addon
    test_addon_json = TESTDATA['blender_dev_addon|dir']
    # Test creating addon
    result = BlenderAddonManager.create_blender_dev_addon(test_addon_json['path'])
    assert result, 'BlenderAddonManager should be able to create a BlenderAddon object'
    addon = result.data
    result = repo.add_component(addon)
    assert result, 'Error adding BlenderAddon to repo'
    # Test BlenderAddon attributes
    assert addon.name == test_addon_json['name'], 'BlenderAddon name does not match'
    assert addon.version == Version(test_addon_json['version']), 'BlenderAddon version does not match'
    assert addon.blender_version_min == Version(test_addon_json['blender_version_min']), \
        'BlenderAddon blender_version_min does not match'
    assert addon.description == test_addon_json['description'], \
        'BlenderAddon description does not match'
    # Test deploying addon
    result = addon.deploy(deploy_dir)
    assert result, 'Error deploying BlenderAddon as a symlink'
    deployed_addon_path = deploy_dir / addon.symlinked_dir_name
    assert deployed_addon_path.exists(), 'Addon should be deployed to deploy dir'

    assert is_dillable(addon), 'BlenderAddon should be dillable'

    # Test single-file addon
    test_addon_json = TESTDATA['blender_dev_addon|single_file']
    # Test creating addon
    result = BlenderAddonManager.create_blender_dev_addon(test_addon_json['path'])
    assert result, 'BlenderAddonManager should be able to create a BlenderAddon object'
    addon = result.data
    result = repo.add_component(addon)
    assert result, 'Error adding BlenderAddon to repo'
    # Test BlenderAddon attributes
    assert addon.name == test_addon_json['name'], 'BlenderAddon name does not match'
    assert addon.version == Version(test_addon_json['version']), 'BlenderAddon version does not match'
    assert addon.blender_version_min == Version(test_addon_json['blender_version_min']), \
        'BlenderAddon blender_version_min does not match'
    assert addon.description == test_addon_json['description'], \
        'BlenderAddon description does not match'
    # Test deploying addon
    result = addon.deploy(deploy_dir)
    assert result, 'Error deploying BlenderAddon as a symlink'
    deployed_addon_path = deploy_dir / addon.symlinked_single_file_name
    assert deployed_addon_path.exists(), 'Addon should be deployed to deploy dir'

    assert is_dillable(addon), 'BlenderAddon should be dillable'
