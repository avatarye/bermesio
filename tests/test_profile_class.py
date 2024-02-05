from pathlib import Path
import random
import shutil

from testing_common import TESTDATA, is_dillable, get_repo

from components.profile import ProfileManager, BlenderLaunchConfig, VenvLaunchConfig


def test_blender_setup_class():
    # repo = get_repo(Path(TESTDATA['test_repo']))
    repo = get_repo(r'c:\TechDepot\Github\bermesio\_test_data\win32\_temp\test_repo')

    # Test creating a BlenderSetup object
    profile_name = f'TempProfile_{str(random.randint(0, 1000)).zfill(4)}'
    result = ProfileManager.create(profile_name)
    assert result, 'Error creating BlenderSetup'
    profile = result.data
    result = repo.add_component(profile)
    assert result, 'Error adding BlenderSetup to repo'

    # Test adding components
    result = profile.add_component(list(repo.blender_program_repo.pool.values())[0])
    assert result, 'Error adding BlenderProgram to BlenderSetup'
    result = profile.add_component(list(repo.blender_setup_repo.pool.values())[0])
    assert result, 'Error adding BlenderSetup to BlenderSetup'
    result = profile.add_component(list(repo.blender_venv_repo.pool.values())[0])
    assert result, 'Error adding BlenderVendor to BlenderSetup'
    result = profile.add_component(list(repo.blender_released_addon_repo.pool.values())[0])
    assert not result, 'BlenderAddon shouldn\'t be added to BlenderSetup'

    # Test launching Blender
    blender_launch_config = BlenderLaunchConfig()
    blender_launch_config.if_use_blender_setup_config = True
    blender_launch_config.if_use_blender_setup_addons_scripts = True
    blender_launch_config.if_include_venv_site_packages = True
    blender_launch_config.if_include_venv_bpy = True
    blender_launch_config.if_include_venv_python_dev_libs = True
    profile.launch_blender(blender_launch_config)

    # Test launching Venv
    venv_launch_config = VenvLaunchConfig()
    venv_launch_config.if_include_site_packages = True
    venv_launch_config.if_include_bpy = True
    venv_launch_config.if_include_local_libs = True
    profile.launch_venv(venv_launch_config)

    # Test dill-ability
    assert is_dillable(profile), 'Profile should be picklable'

    (repo.component_save_dir / profile.dill_save_path).unlink()
