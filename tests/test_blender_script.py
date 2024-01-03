from pathlib import Path

from components.blender_script import BlenderStartupScript, BlenderRegularScript

from testing_common import TESTDATA, is_dillable


def test_blender_regular_script_class():
    script_path = Path(TESTDATA['blender_script|regular|0'])
    script = BlenderRegularScript(script_path)
    assert script.name == script_path.stem

    assert is_dillable(script), 'BlenderRegularScript should be dillable'


def test_blender_startup_script_class():
    script_path = Path(TESTDATA['blender_script|startup|0'])
    script = BlenderStartupScript(script_path)
    assert script.name == script_path.stem

    assert is_dillable(script), 'BlenderStartupScript should be dillable'
