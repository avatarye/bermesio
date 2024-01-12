from pathlib import Path

from packaging.version import Version

from testing_common import TESTDATA, is_dillable, get_repo

from components.blender_program import BlenderProgramManager


def test_blender_program_class():
    repo = get_repo()

    # Add creating a BlenderProgram object
    blender_dir_path = Path(TESTDATA['blender_program|0|blender_dir_path'])
    result = BlenderProgramManager.create(blender_dir_path, name='Blender_4.02_Win')
    blender_program = result.data
    assert blender_program.python_version == Version(TESTDATA['blender_program|0|python_version'])
    assert blender_program.blender_version == Version(TESTDATA['blender_program|0|blender_version'])
    assert len(blender_program.python_packages.package_dict) == 12

    # Add BlenderProgram to repo
    result = repo.add_component(blender_program)
    assert result, 'Error adding BlenderProgram to repo'
    assert hash(blender_program) in repo.blender_program_repo.pool, 'BlenderProgram not added to sub-repo\'s pool'
    assert blender_program.data_path.exists(), 'BlenderProgram data path not copied to repo'

    # Test dill-ability
    assert is_dillable(blender_program), 'BlenderProgram should be picklable'
