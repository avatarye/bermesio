from pathlib import Path

from packaging.version import Version

from testing_common import TESTDATA, is_dillable

from components.blender_program import BlenderProgram, BlenderProgramManager


def test_blender_program_class():
    # This test will only succeed if Blender is installed at the given path.
    blender_exe_path = Path(TESTDATA['blender_program|0|blender_exe_path'])
    blender_program = BlenderProgram(blender_exe_path)
    python_exe_path = Path(TESTDATA['blender_program|0|python_exe_path'])
    assert blender_program.python_exe_path == python_exe_path
    assert blender_program.python_version == Version(TESTDATA['blender_program|0|python_version'])
    assert blender_program.blender_version == Version(TESTDATA['blender_program|0|blender_version'])
    assert len(blender_program.python_packages.package_dict) == 14

    # Test dill-ability
    assert is_dillable(blender_program), 'BlenderProgram should be picklable'
    dill_file_path = Path(__file__).parent
    result = blender_program.save_to_disk(dill_file_path)
    assert result, 'BlenderProgram should be saved to disk'
    assert blender_program.dill_save_path.exists(), 'BlenderProgram should be saved to disk'
    result = BlenderProgram.load_from_disk(blender_program.dill_save_path)
    assert result, 'BlenderProgram should be loaded from disk'
    restored = result.data
    assert restored.is_verified, 'BlenderProgram should be verified after loading from disk'
    assert restored.python_exe_path == python_exe_path
    assert restored.python_version == Version(TESTDATA['blender_program|0|python_version'])
    assert restored.blender_version == Version(TESTDATA['blender_program|0|blender_version'])
    assert len(restored.python_packages.package_dict) == 14
    blender_program.dill_save_path.unlink()


def test_blender_program_manager_class():
    result = BlenderProgramManager.create_blender_program(TESTDATA['blender_program|0|blender_exe_path'],
                                                          name='TestBlender')
    assert result, 'BlenderProgram should be created'
    blender_program = result.data
    assert blender_program.name == 'TestBlender', 'BlenderProgram should have the given name'