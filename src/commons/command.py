import os
import subprocess

from commons.common import Result, blog


def run_command(command, os_evn=None, expected_success_data_format=None) -> Result:
    try:
        blog(1, f'Running command: {command}')
        if os_evn is not None:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True, env=os.environ)
        else:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        if result.returncode == 0:
            if expected_success_data_format is None:
                return Result(True, result.stdout, result)
            else:
                return Result(True, result.stdout, expected_success_data_format(result.stdout))
        else:
            blog(4, f'Error running command: {command}, {result.stderr}')
            return Result(False, result.stderr, result)
    except subprocess.CalledProcessError as e:
        blog(4, f'Error running command: {command}, {e}')
        return Result(False, 'Error: {e}', e)
