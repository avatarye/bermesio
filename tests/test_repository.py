from pathlib import Path
import random
import shutil

from testing_common import TESTDATA, is_dillable, get_repo

from bermesio.components.repository import Repository
from bermesio.components.blender_addon import (BlenderAddonManager, BlenderZippedAddon, BlenderDirectoryAddon,
                                      BlenderDevDirectoryAddon, BlenderDevSingleFileAddon, BlenderSingleFileAddon)
from bermesio.components.blender_program import BlenderProgramManager, BlenderProgram
from bermesio.components.blender_script import (BlenderScriptManager, BlenderRegularScript, BlenderStartupScript,
                                       BlenderDevRegularScript, BlenderDevStartupScript)
from bermesio.components.blender_setup import BlenderSetupManager, BlenderSetup
from bermesio.components.blender_venv import BlenderVenvManager, BlenderVenv
from bermesio.components.profile import ProfileManager, Profile
from bermesio.components.python_dev_library import PythonDevLibraryManager, PythonDevLibrary
from bermesio.components.python_package import PythonPyPIPackage


def test_repository_class_creation_functions():
    # If use default temporary test repo dir, which will be cleared automatically before testing
    if False:
        repo = get_repo()
    # This is used to create example repo for testing
    else:
        repo_dir = Path(TESTDATA['example_repo'])
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
        repo = get_repo(repo_dir)

    # Test readiness
    assert repo.is_repository_path_ready, 'Repository path is not ready'
    assert repo.has_internet_connection, 'No internet connection'
    # Test adding BlenderProgram and BlenderVenv
    result = repo.create_component(BlenderProgram, TESTDATA['blender_program|0|blender_dir_path'],
                                   name='Blender_4.02_Win')
    assert result, 'Error creating BlenderProgram'
    blender_program = result.data
    result = BlenderVenvManager.create_venv_from_blender_program(
        blender_program, repo.blender_venv_repo.storage_save_dir / 'TestBlenderVenv', name='TestBlenderVenv'
    )
    assert result, 'Error creating BlenderVenv'
    blender_venv = result.data
    result = repo.add_component(blender_venv)
    assert result, 'Error adding BlenderVenv'
    repo.match_venv_to_blender_program_in_repo(blender_venv)  # Match the venv's Blender program to the one in repo
    assert blender_venv.blender_program == blender_program, 'BlenderVenv does not match BlenderProgram'
    blender_venv.install_bpy_package()
    blender_venv.install_site_package(PythonPyPIPackage('shapely'))
    # Test adding addon
    result = repo.create_component(BlenderZippedAddon, TESTDATA['blender_addon|zip|path'])
    zipped_addon = result.data
    result = repo.create_component(BlenderZippedAddon, TESTDATA['blender_addon|zip|path'])
    assert not result, 'Error detecting existing BlenderAddon'
    result = repo.create_component(BlenderDirectoryAddon, TESTDATA['blender_addon|dir|path'])
    assert not result, 'Error detecting existing BlenderAddon'
    result = repo.create_component(BlenderSingleFileAddon, TESTDATA['blender_addon|single_file|path'])
    assert result, 'Error creating BlenderSingleFileAddon'
    assert len(repo.blender_released_addon_repo.pool) == 2, 'Error creating BlenderSingleFileAddon'
    result = repo.create_component(BlenderDevSingleFileAddon, TESTDATA['blender_dev_addon|single_file|path'])
    assert result, 'Error creating BlenderDevSingleFileAddon'
    result = repo.create_component(BlenderDevDirectoryAddon, TESTDATA['blender_dev_addon|dir|path'])
    assert result, 'Error creating BlenderDevDirectoryAddon'
    assert len(repo.blender_dev_addon_repo.pool) == 2, 'Error creating BlenderSingleFileAddon'
    # Test adding script
    result = repo.create_component(BlenderStartupScript, Path(TESTDATA['blender_script|startup|0']), 'startup')
    assert result, 'Error creating BlenderStartupScript'
    result = repo.create_component(BlenderRegularScript, Path(TESTDATA['blender_script|regular|0']), 'regular')
    assert result, 'Error adding BlenderRegularScript'
    assert len(repo.blender_released_script_repo.pool) == 2, 'Error adding BlenderRegularScript'
    result = repo.create_component(BlenderDevStartupScript, Path(TESTDATA['blender_dev_script|startup|0']), 'startup')
    assert result, 'Error creating BlenderDevStartupScript'
    result = repo.create_component(BlenderDevRegularScript, Path(TESTDATA['blender_dev_script|regular|0']), 'regular')
    assert result, 'Error adding BlenderDevRegularScript'
    assert len(repo.blender_dev_script_repo.pool) == 2, 'Error adding BlenderDevRegularScript'
    # Test adding Python dev library
    result = repo.create_component(PythonDevLibrary, Path(TESTDATA['python_dev_library|0|path']),
                                   name=TESTDATA['python_dev_library|0|library_name'])
    assert result, 'Error creating PythonDevLibrary'
    assert len(repo.python_dev_library_repo.pool) == 1, 'Error creating PythonDevLibrary'
    blender_venv.install_dev_library(result.data)

    # Test adding BlenderSetup
    blender_setup_name = f'TempBlenderSetup'
    result = repo.create_component(BlenderSetup, repo.blender_setup_repo.storage_save_dir, blender_setup_name)
    assert result, 'Error creating BlenderSetup'
    blender_setup = result.data
    blender_config_path = blender_setup.data_path / blender_setup.setup_blender_config_path
    result = blender_setup.add_blender_config()
    assert result and blender_config_path.exists(), 'Error adding Blender config'
    result = blender_setup.add_component(list(repo.blender_program_repo.pool.values())[0])
    assert not result, 'BlenderProgram shouldn\'t be added to BlenderSetup'
    result = blender_setup.add_component(list(repo.blender_released_addon_repo.pool.values())[0])
    assert result, 'Error adding BlenderAddon to BlenderSetup'
    result = blender_setup.add_component(list(repo.blender_released_addon_repo.pool.values())[1])
    assert result, 'Error adding BlenderAddon to BlenderSetup'
    result = blender_setup.add_component(list(repo.blender_dev_addon_repo.pool.values())[0])
    assert result, 'Error adding BlenderDevAddon to BlenderSetup'
    result = blender_setup.add_component(list(repo.blender_dev_addon_repo.pool.values())[1])
    assert result, 'Error adding BlenderDevAddon to BlenderSetup'
    result = blender_setup.add_component(list(repo.blender_released_script_repo.pool.values())[0])
    assert result, 'Error adding BlenderScript to BlenderSetup'
    result = blender_setup.add_component(list(repo.blender_released_script_repo.pool.values())[1])
    assert result, 'Error adding BlenderScript to BlenderSetup'

    # Test adding Profile
    profile_name = f'TempProfile'
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


def test_repository_class_component_functions():
    repo_dir = r'c:\TechDepot\Github\bermesio\_test_data\win32\repos\example_repo'
    repo = get_repo(repo_dir)

    # Test replacing and updating component
    # TODO: After BlenderSetup and Profile are implemented
    result = BlenderAddonManager.create_blender_addon(TESTDATA['blender_addon|zip|path'])
    new_addon = result.data
    result = repo.update_component(new_addon)
    assert not result, 'Same version of BlenderAddon shouldn\'t be updated'
    result = BlenderAddonManager.create_blender_addon(TESTDATA['blender_addon|zip_update|path'])
    new_addon = result.data
    result = repo.update_component(new_addon)
    assert result, 'Error updating BlenderAddon'

    # Test duplicating component
    # TODO: After BlenderSetup and Profile are implemented

    # Test removing component
    # TODO: After BlenderSetup and Profile are implemented
    result = repo.remove_component(zipped_addon)
    assert not result, 'Addon has been updated with new_addon, shouldn\' exist for removal'
    result = repo.remove_component(new_addon)
    assert new_addon.uuid not in repo.blender_released_addon_repo.pool, 'Error removing BlenderAddon'

    # Test loading component from disk
    # TODO: After BlenderSetup and Profile are implemented
    Repository._instance, Repository._is_initialized = None, False  # Reset the singleton
    repo = Repository(repo_dir=repo_dir)
    assert len(repo.blender_released_addon_repo.pool) == 1, 'Error loading BlenderAddon from disk'
    assert len(repo.blender_program_repo.pool) == 1, 'Error loading BlenderAddon from disk'
    assert len(repo.blender_venv_repo.pool) == 1, 'Error loading BlenderAddon from disk'
    assert len(repo.blender_released_script_repo.pool) == 2, 'Error loading BlenderAddon from disk'

    # Test dill-ability
    assert is_dillable(repo), 'Repository should be picklable'

    if repo_dir.exists():
        shutil.rmtree(repo_dir)


def test_repository_class_launch_functions():
    repo_dir = Path(TESTDATA['example_repo'])
    repo = get_repo(repo_dir)

    profile = list(repo.profile_repo.pool.values())[0]
    result = profile.launch_blender()
    assert result, 'Error launching Blender'
    result = profile.launch_venv()
    assert result, 'Error launching Blender Venv'
