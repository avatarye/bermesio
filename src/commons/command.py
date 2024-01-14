import os
import subprocess

from commons.common import Result, blog


def run_command(command, os_env=None, expected_success_data_format=None) -> Result:
    """
    Run a command in the shell and return the result. Note, this blocks the main thread.

    :param command: a string of the command to run
    :param os_env: a dict of the environment variables to use
    :param expected_success_data_format: a function to format the success data

    :return: a Result object indicating if the command is successful, the message generated during the command, and the
             result object returned by subprocess.run()
    """
    try:
        blog(1, f'Running command: {command}')
        if os_env is not None:
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


def popen_command(command, os_env=None) -> Result:
    try:
        blog(1, f'Running command in Popen: {command}')
        env = os.environ.copy()
        if os_env is not None:
            env.update(os_env)
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   env=env)
        return Result(True, "", process)
    except subprocess.CalledProcessError as e:
        blog(4, f'Error running command: {command}, {e}')
        return Result(False, f'Error: {e}', None)
