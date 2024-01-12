from pathlib import Path
import shutil

from components.blender_script import BlenderScriptManager

from testing_common import TESTDATA, is_dillable, get_repo


def test_blender_released_script_class():
    repo = get_repo()
    deploy_dir = Path(TESTDATA['temp_dir']) / 'deploy'
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)

    # Test creating a BlenderRegularScript object
    result = BlenderScriptManager.create_blender_script(Path(TESTDATA['blender_script|regular|0']), 'regular')
    assert result, 'BlenderScriptManager should be able to create a BlenderRegularScript object'
    regular_script = result.data
    repo.add_component(regular_script)
    regular_script.deploy(deploy_dir)
    deployed_path = deploy_dir / regular_script.regular_script_deploy_subdir / regular_script.data_path.name
    assert deployed_path.exists(), 'Regular script should be deployed to deploy dir'

    # Test creating a BlenderStartupScript object
    result = BlenderScriptManager.create_blender_script(Path(TESTDATA['blender_script|startup|0']), 'startup')
    assert result, 'BlenderScriptManager should be able to create a BlenderStartupScript object'
    startup_script = result.data
    repo.add_component(startup_script)
    startup_script.deploy(deploy_dir)
    deployed_path = deploy_dir / startup_script.startup_script_deploy_subdir / startup_script.data_path.name
    assert deployed_path.exists(), 'Startup script should be deployed to deploy dir'

    # Test dill-ability
    assert is_dillable(regular_script), 'BlenderRegularScript should be picklable'
    assert is_dillable(startup_script), 'BlenderStartupScript should be picklable'


def test_blender_dev_script_class():
    repo = get_repo()
    deploy_dir = Path(TESTDATA['temp_dir']) / 'deploy'
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)

    # Test creating a BlenderRegularScript object
    result = BlenderScriptManager.create_blender_dev_script(Path(TESTDATA['blender_dev_script|regular|0']), 'regular')
    assert result, 'BlenderScriptManager should be able to create a BlenderDevRegularScript object'
    regular_script = result.data
    repo.add_component(regular_script)
    result = regular_script.deploy(deploy_dir)
    assert result, 'Error deploying BlenderDevRegularScript as a symlink'
    deployed_path = deploy_dir / regular_script.regular_script_deploy_subdir / regular_script.data_path.name
    assert deployed_path.exists(), 'Regular script should be deployed to deploy dir'

    # Test creating a BlenderStartupScript object
    result = BlenderScriptManager.create_blender_dev_script(Path(TESTDATA['blender_dev_script|startup|0']), 'startup')
    assert result, 'BlenderScriptManager should be able to create a BlenderDevStartupScript object'
    startup_script = result.data
    repo.add_component(startup_script)
    result = startup_script.deploy(deploy_dir)
    assert result, 'Error deploying BlenderDevStartupScript as a symlink'
    deployed_path = deploy_dir / startup_script.startup_script_deploy_subdir / startup_script.data_path.name
    assert deployed_path.exists(), 'Startup script should be deployed to deploy dir'

    # Test dill-ability
    assert is_dillable(regular_script), 'BlenderRegularScript should be picklable'
    assert is_dillable(startup_script), 'BlenderStartupScript should be picklable'
