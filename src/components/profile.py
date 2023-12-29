
class Profile:

    def __init__(self):
        pass
    # os.environ['BLENDER_USER_SCRIPTS'] = r'c:\TechDepot\AvatarTools\Blender\Launcher\shared_scripts'
    # os.environ['BLENDER_USER_CONFIG'] = r'c:\Users\yong-\.source\config'

    def launch_blender(blender_path, env_path):
        if sys.platform == "win32":
            activate_script = env_path / 'Scripts' / 'activate.bat'
            command = f'cmd.exe /c "{activate_script} && "{blender_path}"'
        else:
            activate_script = env_path / 'bin' / 'activate'
            command = f'source {activate_script} && "{blender_path}"'
        return run_command(command)
