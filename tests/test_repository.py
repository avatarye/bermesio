from pathlib import Path
import shutil

from testing_common import TESTDATA, is_dillable

from components.repository import Repository
from components.blender_addon import (BlenderZippedAddon, BlenderDirectoryAddon, BlenderSingleFileAddon,
                                      BlenderDevDirectoryAddon, BlenderDevSingleFileAddon)
from components.blender_program import BlenderProgram
from components.blender_script import BlenderStartupScript, BlenderRegularScript
from components.blender_setup import BlenderSetup
from components.blender_venv import BlenderVenv
from components.python_dev_library import PythonDevLibrary
from components.profile import Profile


def test_repository_class():
    repo_dir = Path(__file__).parent / 'test_repository'
    if repo_dir.exists():
        shutil.rmtree(repo_dir)

    # repo = Repository(repo_dir=repo_dir)
    repo = Repository()
    repo.init_sub_repos()
    assert repo.is_repository_path_ready, 'Repository path is not ready'
    assert repo.has_internet_connection, 'No internet connection'
    # Test adding Blender program
    result = repo.create_component(BlenderProgram, TESTDATA['blender_program|0|blender_exe_path'])
    assert result, 'Error creating BlenderProgram'
    blender_program = result.data
    # Test adding Blender venv
    blender_venv = BlenderVenv(TESTDATA['blender_venv|0|blender_venv_path'])
    result = repo.add_component(blender_venv)
    assert result.ok, 'Error adding BlenderVenv'
    repo.match_venv_to_blender_program()  # Match the venv's Blender program to the one in repo
    assert blender_venv.blender_program == blender_program, 'BlenderVenv does not match BlenderProgram'
    # Test adding addon
    sub_repo_dir = repo.blender_addon_repo.path
    zipped_addon = BlenderZippedAddon(TESTDATA['blender_addon|zip|path'], repo_dir=sub_repo_dir)
    result = repo.add_component(zipped_addon)
    assert result.ok, 'Error creating BlenderZippedAddon'
    result = repo.create_component(BlenderZippedAddon, TESTDATA['blender_addon|zip|path'], repo_dir=sub_repo_dir)
    assert not result.ok, 'Error detecting existing BlenderAddon'
    result = repo.create_component(BlenderDirectoryAddon, TESTDATA['blender_addon|dir|path'], repo_dir=sub_repo_dir)
    assert not result.ok, 'Error detecting existing BlenderAddon'
    result = repo.create_component(BlenderSingleFileAddon, TESTDATA['blender_addon|single_file|path'],
                                   repo_dir=sub_repo_dir)
    assert result.ok, 'Error creating BlenderSingleFileAddon'
    # Test adding script
    sub_repo_dir = repo.blender_script_repo.path
    script_path = Path(TESTDATA['blender_script|startup|0'])
    result = repo.create_component(BlenderStartupScript, script_path, repo_dir=sub_repo_dir)
    assert result.ok, 'Error creating BlenderStartupScript'
    blender_script = BlenderRegularScript(Path(TESTDATA['blender_script|regular|0']), repo_dir=sub_repo_dir)
    result = repo.add_component(blender_script)
    assert result.ok, 'Error adding BlenderRegularScript'

    # Test updating component
    new_addon = BlenderDirectoryAddon(TESTDATA['blender_addon|dir|path'], repo_dir=sub_repo_dir)
    result = repo.update_component(new_addon)
    assert result.ok, 'Error updating BlenderAddon'
    assert new_addon.uuid in repo.blender_addon_repo.pool, 'Error updating BlenderAddon'
    assert zipped_addon.uuid not in repo.blender_addon_repo.pool, 'Error updating BlenderAddon'

    # Test removing component
    result = repo.remove_component(zipped_addon)
    assert not result.ok, 'Addon has been updated with new_addon, shouldn\' exist for removal'
    result = repo.remove_component(new_addon)
    assert new_addon.uuid not in repo.blender_addon_repo.pool, 'Error removing BlenderAddon'

    # Test loading component from disk
    Repository._instance, Repository._is_initialized = None, False  # Reset the singleton
    repo = Repository(repo_dir=repo_dir)
    assert len(repo.blender_addon_repo.pool) == 1, 'Error loading BlenderAddon from disk'
    assert len(repo.blender_program_repo.pool) == 1, 'Error loading BlenderAddon from disk'
    assert len(repo.blender_venv_repo.pool) == 1, 'Error loading BlenderAddon from disk'
    assert len(repo.blender_script_repo.pool) == 2, 'Error loading BlenderAddon from disk'

    # Test dill-ability
    assert is_dillable(repo), 'Repository should be picklable'

    if repo_dir.exists():
        shutil.rmtree(repo_dir)
