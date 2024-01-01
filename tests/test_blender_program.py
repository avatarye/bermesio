from pathlib import Path

from packaging.version import Version

from testing_common import TESTDATA, is_dillable

from components.blender_program import BlenderProgram


def test_blender_program_class():
    # This test will only succeed if Blender is installed at the given path.
    blender_exe_path = Path(TESTDATA['blender_program|0|blender_exe_path'])
    blender_program = BlenderProgram(blender_exe_path)
    python_exe_path = Path(TESTDATA['blender_program|0|python_exe_path'])
    assert blender_program.python_exe_path == python_exe_path
    assert blender_program.python_version == Version(TESTDATA['blender_program|0|python_version'])
    assert blender_program.blender_version == Version(TESTDATA['blender_program|0|blender_version'])
    assert len(blender_program.python_packages.package_dict) == 12

    # Test dill-ability
    assert is_dillable(blender_program), 'BlenderProgram should be picklable'
    dill_file_path = Path(__file__).parent / 'test_blender_program.dill'
    blender_program.save_to_disk(dill_file_path)
    if dill_file_path.exists():
        restored = BlenderProgram.load_from_disk(dill_file_path)
        assert restored.is_verified, 'BlenderProgram should be verified after loading from disk'
        assert restored.python_exe_path == python_exe_path
        assert restored.python_version == Version(TESTDATA['blender_program|0|python_version'])
        assert restored.blender_version_min == Version(TESTDATA['blender_program|0|blender_version'])
        assert len(restored.python_packages.package_dict) == 12
        dill_file_path.unlink()
