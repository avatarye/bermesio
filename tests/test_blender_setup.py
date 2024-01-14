from pathlib import Path
import random
import shutil

from testing_common import TESTDATA, is_dillable, get_repo

from components.blender_setup import BlenderSetupManager, BlenderSetup


def test_blender_setup_class():
    repo = get_repo(Path(TESTDATA['test_repo']))

    # Test creating a BlenderSetup object
    repo_dir = repo.blender_setup_repo.storage_save_dir
    blender_setup_name = f'TempBlenderSetup_{str(random.randint(0, 1000)).zfill(4)}'
    result = BlenderSetupManager.create(repo_dir, blender_setup_name)
    assert result, 'Error creating BlenderSetup'
    blender_setup = result.data

    # Test change Blender config
    result = repo.add_component(blender_setup)
    assert result, 'Error adding BlenderSetup to repo'
    blender_config_path = blender_setup.data_path / blender_setup.setup_blender_config_path
    result = blender_setup.add_blender_config()
    assert result and blender_config_path.exists(), 'Error adding Blender config'
    result = blender_setup.remove_blender_config()
    assert result and not blender_config_path.exists(), 'Error removing Blender config'

    # Test adding and removing components
    result = blender_setup.add_component(list(repo.blender_program_repo.pool.values())[0])
    assert not result, 'BlenderProgram shouldn\'t be added to BlenderSetup'
    result = blender_setup.add_component(list(repo.blender_addon_repo.pool.values())[0])
    assert result, 'Error adding BlenderAddon to BlenderSetup'
    result = blender_setup.add_component(list(repo.blender_addon_repo.pool.values())[1])
    assert result, 'Error adding BlenderAddon to BlenderSetup'
    result = blender_setup.add_component(list(repo.blender_dev_addon_repo.pool.values())[0])
    assert result, 'Error adding BlenderDevAddon to BlenderSetup'
    result = blender_setup.add_component(list(repo.blender_dev_addon_repo.pool.values())[1])
    assert result, 'Error adding BlenderDevAddon to BlenderSetup'

    result = blender_setup.add_component(list(repo.blender_script_repo.pool.values())[0])
    assert result, 'Error adding BlenderScript to BlenderSetup'
    result = blender_setup.add_component(list(repo.blender_script_repo.pool.values())[1])
    assert result, 'Error adding BlenderScript to BlenderSetup'
    result = blender_setup.remove_component(list(repo.blender_script_repo.pool.values())[0])
    assert result, 'Error removing BlenderScript to BlenderSetup'
    result = blender_setup.remove_component(list(repo.blender_script_repo.pool.values())[1])
    assert result, 'Error removing BlenderScript to BlenderSetup'

    result = blender_setup.add_component(list(repo.blender_dev_script_repo.pool.values())[0])
    assert result, 'Error adding BlenderDevScript to BlenderSetup'
    result = blender_setup.add_component(list(repo.blender_dev_script_repo.pool.values())[1])
    assert result, 'Error adding BlenderDevScript to BlenderSetup'

    # Test dill-ability
    assert is_dillable(blender_setup), 'BlenderSetup should be picklable'

    shutil.rmtree(blender_setup.data_path)
    (repo.component_save_dir / blender_setup.dill_save_path).unlink()
