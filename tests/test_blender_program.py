from pathlib import Path

from packaging.version import Version

from testing_common import TESTDATA, is_dillable, get_repo

from components.blender_program import BlenderProgram


def test_blender_program_class():
    repo = get_repo()

    blender_exe_path = Path(TESTDATA['blender_program|0|blender_dir_path'])
    result = BlenderProgram(blender_exe_path, name='Blender_4.02_Win').create_instance()
    blender_program = result.data
    assert blender_program.python_version == Version(TESTDATA['blender_program|0|python_version'])
    assert blender_program.blender_version == Version(TESTDATA['blender_program|0|blender_version'])
    assert len(blender_program.python_packages.package_dict) == 12

    result = repo.add_component(blender_program)
    assert result, 'Error adding BlenderProgram to repo'
    assert hash(blender_program) in repo.blender_program_repo.pool, 'BlenderProgram not added to sub-repo\'s pool'
    assert blender_program.data_path.exists(), 'BlenderProgram data path not copied to repo'

    # Test dill-ability
    assert is_dillable(blender_program), 'BlenderProgram should be picklable'
