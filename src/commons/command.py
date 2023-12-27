import os
import subprocess

from commons.common import Result as R


def run_command(command, os_evn=None, expected_success_data_format=None) -> R:
    try:
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
            return R(False, result.stderr, result)
    except subprocess.CalledProcessError as e:
        return R(False, 'Error: {e}', e)
