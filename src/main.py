import os
import packaging.version
from pathlib import Path
import subprocess
import sys

from PyQt6.QtWidgets import QApplication
import virtualenv

from commons.common import Result as R
from config import CONFIG



def create_env(python_path, env_path):
    if not env_path.exists():
        os.makedirs(env_path)
    options = [env_path.as_posix(), '--python', python_path.as_posix()]
    result = virtualenv.cli_run(options)
    match_blender_python_packages(env_path, python_path)
    return result

def launch_blender(blender_path, env_path):
    if sys.platform == "win32":
        activate_script = env_path / 'Scripts' / 'activate.bat'
        command = f'cmd.exe /c "{activate_script} && "{blender_path}"'
    else:
        activate_script = env_path / 'bin' / 'activate'
        command = f'source {activate_script} && "{blender_path}"'
    return run_command(command)


if __name__ == '__main__':
    blender_exe_path = Path(r'c:\TechDepot\AvatarTools\Blender\Launcher\stable\blender-4.0.1-windows-x64\blender.exe')
    python_path = Path(r'c:\TechDepot\AvatarTools\Blender\Launcher\stable\blender-4.0.1-windows-x64\4.0\python\bin\python.exe')
    env_path = Path(r'c:\TechDepot\Github\bermesio\_data\venvs\venv_blender_4.0.1_1')
    # result = create_env(python_path, env_path)
    launch_blender(blender_exe_path, env_path)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName(CONFIG.app_name)
    app.setApplicationVersion(CONFIG.app_version)
    app.setQuitOnLastWindowClosed(False)

    # Launch the application
    sys.exit()