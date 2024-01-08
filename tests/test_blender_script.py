from pathlib import Path
import shutil

from components.blender_script import (BlenderRegularScript, BlenderStartupScript, BlenderDevRegularScript,
                                       BlenderDevStartupScript, BlenderScriptManager)

from testing_common import TESTDATA, is_dillable


def test_blender_regular_script_class():
    copy_to_dir = Path(__file__).parent / 'test_blender_scripts'
    deploy_to_dir = Path(__file__).parent / 'test_blender_scripts' / 'deploy'
    script_path = Path(TESTDATA['blender_script|regular|0'])
    result = BlenderScriptManager.create_blender_script(script_path, 'regular', repo_dir=copy_to_dir)
    assert result, 'BlenderScriptManager should be able to create a BlenderRegularScript object'
    script = result.data
    assert script.name == script_path.stem, 'Script name should be the same as the file name'
    copied_script = copy_to_dir / script_path.name
    assert copied_script.exists(), 'Startup script should be copied to repo dir'
    script.deploy(deploy_to_dir)
    deployed_path = deploy_to_dir / script.regular_script_deploy_subdir / script_path.name
    assert deployed_path.exists(), 'Regular script should be deployed to deploy dir'
    assert is_dillable(script), 'BlenderRegularScript should be dillable'

    if copy_to_dir.exists():
        shutil.rmtree(copy_to_dir)


def test_blender_startup_script_class():
    copy_to_dir = Path(__file__).parent / 'test_blender_scripts'
    deploy_to_dir = Path(__file__).parent / 'test_blender_scripts' / 'deploy'
    script_path = Path(TESTDATA['blender_script|startup|0'])
    result = BlenderScriptManager.create_blender_script(script_path, 'startup', repo_dir=copy_to_dir)
    assert result, 'BlenderScriptManager should be able to create a BlenderStartupScript object'
    script = result.data
    assert script.name == script_path.stem, 'Script name should be the same as the file name'
    copied_script = copy_to_dir / script_path.name
    assert copied_script.exists(), 'Startup script should be copied to repo dir'
    script.deploy(deploy_to_dir)
    deployed_path = deploy_to_dir / script.startup_script_deploy_subdir / script_path.name
    assert deployed_path.exists(), 'Startup script should be deployed to deploy dir'
    assert is_dillable(script), 'BlenderStartupScript should be dillable'

    if copy_to_dir.exists():
        shutil.rmtree(copy_to_dir)

def test_blender_dev_regular_script_class():
    copy_to_dir = Path(__file__).parent / 'test_blender_scripts'
    deploy_to_dir = Path(__file__).parent / 'test_blender_scripts' / 'deploy'
    script_path = Path(TESTDATA['blender_script|regular|0'])
    result = BlenderScriptManager.create_blender_dev_script(script_path, 'regular')
    assert result, 'BlenderScriptManager should be able to create a BlenderDevRegularScript object'
    script = result.data
    assert script.name == script_path.stem, 'Script name should be the same as the file name'
    script.deploy(deploy_to_dir)
    deployed_path = deploy_to_dir / script.regular_script_deploy_subdir / script_path.name
    assert deployed_path.exists(), 'DevRegular script should be deployed to deploy dir'
    assert is_dillable(script), 'BlenderDevRegularScript should be dillable'

    if copy_to_dir.exists():
        shutil.rmtree(copy_to_dir)

def test_blender_dev_startup_script_class():
    copy_to_dir = Path(__file__).parent / 'test_blender_scripts'
    deploy_to_dir = Path(__file__).parent / 'test_blender_scripts' / 'deploy'
    script_path = Path(TESTDATA['blender_script|startup|0'])
    result = BlenderScriptManager.create_blender_dev_script(script_path, 'startup')
    assert result, 'BlenderScriptManager should be able to create a BlenderDevStartupScript object'
    script = result.data
    assert script.name == script_path.stem, 'Script name should be the same as the file name'
    script.deploy(deploy_to_dir)
    deployed_path = deploy_to_dir / script.startup_script_deploy_subdir / script_path.name
    assert deployed_path.exists(), 'Dev startup script should be deployed to deploy dir'
    assert is_dillable(script), 'BlenderDevStartupScript should be dillable'

    if copy_to_dir.exists():
        shutil.rmtree(copy_to_dir)
