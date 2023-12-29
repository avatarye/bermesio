import os
import subprocess

from commons.common import Result as R, blog


def run_command(command, os_evn=None, expected_success_data_format=None) -> R:
    try:
        blog(1, f'Running command: {command}')
        if os_evn is not None:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, env=os.environ)
        else:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        if result.returncode == 0:
            if expected_success_data_format is None:
                return R(True, result.stdout, result)
            else:
                return R(True, result.stdout, expected_success_data_format(result.stdout))
        else:
            blog(4, f'Error running command: {command}, {result.stderr}')
            return R(False, result.stderr, result)
    except subprocess.CalledProcessError as e:
        blog(4, f'Error running command: {command}, {e}')
        return R(False, 'Error: {e}', e)
