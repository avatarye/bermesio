from dataclasses import dataclass
import logging
import os
from pathlib import Path
import re
import shutil
import sys

from bermesio.config import Config


# region Result Type

@dataclass
class Result:
    """
    A class representing the result of a function call. It is suitable for propagating result from a chain of functions
    with message generated by system and result. In case of a success, the data field will contain the result of the
    function call. In case of a failure, the data field will contain the exception raised by the function call.
    """

    ok: bool
    message: str or [str] = ''
    data: any = None
    error_log_level: int = 3

    def __init__(self, ok: bool, message: str or [str] = '', data: any = None, if_log_success=False, if_log_error=True,
                 error_log_level: int = 3):
        self.ok = ok
        self.message = message
        self.data = data

        if if_log_success and self.ok:
            blog(2, self.message)  # Always log success at level 2
        self.error_log_level = error_log_level
        if if_log_error and not self.ok:
            blog(self.error_log_level, self.message)

    def __str__(self):
        return f'{"Success" if self.ok else "Failure"}: {self.message}, {self.data}'

    def __bool__(self):
        return self.ok


class ResultList:
    """
    A class representing a list of Result objects. It is useful for handling a list of Result objects from processing a
    list of items which return Result objects.
    """

    ok: bool
    message: [str] = []
    data: [any] = []
    error_log_level: int = 3

    def __init__(self, result_list: [Result], if_log_success=False, if_log_error=True, error_log_level: int = 3):
        self.result_list = result_list
        self.ok = all([result.ok for result in result_list])
        self.messages = [result.message for result in result_list]
        self.success_messages = [result.message for result in result_list if result.ok]
        self.error_messages = [result.message for result in result_list if not result.ok]
        self.data = [result.data for result in result_list]
        self.success_data = [result.data for result in result_list if result.ok]
        self.error_data = [result.data for result in result_list if not result.ok]

        if if_log_success and not self.ok:
            blog(2, ';'.join(self.success_messages))
        self.error_log_level = error_log_level
        if if_log_error and not self.ok:
            blog(self.error_log_level, ';'.join(self.error_messages))

    def to_result(self) -> Result:
        """Convert to a Result object."""
        return Result(self.ok, self.messages, self.data, error_log_level=self.error_log_level)

    def __str__(self):
        return (f'{"Success" if self.ok else "Failure"}: {len(self.success_messages)} successes, '
                f'{len(self.error_messages)} errors, {self.data}')

    def __bool__(self):
        return self.ok

# endregion


# region Global logger

class _LoggerLTFilter(logging.Filter):
    """Less-than filter for Logger"""

    def __init__(self, level: int, name: str = ""):
        super(_LoggerLTFilter, self).__init__(name)
        self.max_level = level

    def filter(self, record):
        # non-zero return means we log this message
        return 1 if record.levelno < self.max_level else 0


class _LoggerGTFilter(logging.Filter):
    """Greater-than filter for Logger"""

    def __init__(self, level: int, name: str = ""):
        super(_LoggerGTFilter, self).__init__(name)
        self.level = level

    def filter(self, record):
        # non-zero return means we log this message
        return 1 if record.levelno > self.level else 0


class Logger:
    """
    Serves as a global logger for all downstream functions. Common simpleton pattern is not in this class because
    Python's logging class itself keeps a global reference to the logger based on the name. It is recommended to use
    this class as shown in the snippet below:

    Example:
        >>> log = Logger('YourAppName', level=logging.DEBUG, include_time=True).log
        >>> log('info', 'This is an info message')
        >>> log(2, 'This is an info message')
        >>> log('debug', 'This is a debug message')
        >>> log(1, 'This is a debug message')
    """

    logger = None

    levels = {5: 'critical', 4: 'error', 3: 'warning', 2: 'info', 1: 'debug'}

    def __init__(self, logger_name, level=logging.DEBUG, include_time=False):
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.propagate = False  # Prevent duplicate logging by the root logger
        # Logger and handler of the logging module is globally persistent, so check before create new ones.
        if len(logger.handlers) == 0:
            if include_time:
                formatter = logging.Formatter('%(asctime)s - [%(name)s %(levelname)s]: %(message)s')
            else:
                formatter = logging.Formatter('[%(name)s %(levelname)s]: %(message)s')
            # Use 2 handlers to output messages via stdout and stderr respectively to have desired text colors in DCC
            # console
            handler_out = logging.StreamHandler(sys.stdout)
            handler_out.setLevel(logging.DEBUG)
            handler_out.addFilter(_LoggerLTFilter(logging.ERROR))
            handler_out.setFormatter(formatter)
            logger.addHandler(handler_out)

            handler_err = logging.StreamHandler(sys.stderr)
            handler_err.setLevel(logging.WARNING)
            handler_err.addFilter(_LoggerGTFilter(logging.WARNING))
            handler_err.setFormatter(formatter)
            logger.addHandler(handler_err)
        self.logger = logger

    def log(self, level: int or str, message: str):
        """
        The main log function for this logger class.

        :param level: logging level, can be an integer or a string
        :param message: message to be logged
        """
        assert self.logger is not None, 'Logger is not initialized'
        if isinstance(level, int):
            level = self.levels.get(level, None)
        assert isinstance(level, str) and level in dir(self.logger), f'Incorrect logging level, {level}'
        getattr(self.logger, level)(message)


blog = Logger(f'{Config.app_name}', level=logging.DEBUG, include_time=True).log

# endregion


# region Shared functions

class SharedFunctions:
    """A static class that contains shared functions across the application."""

    def __new__(cls, *args, **kwargs):
        raise Exception('This class should not be instantiated.')

    @staticmethod
    def is_valid_name_for_path(name: str) -> bool:
        """
        Check if a name is valid, i.e. only contains alphanumeric, underscore, period, and hyphen, and can be used as
        a file or directory name.

        :param name: the name to be checked

        :return: True if the name is valid, otherwise False
        """
        pattern = re.compile(r'^[a-zA-Z0-9_.-]*$')
        return True if pattern.match(name) else False

    @staticmethod
    def create_target_dir(target_dir: str or Path) -> Result:
        """
        A static method that creates a directory.
        :param target_dir:
        :return:
        """
        target_dir = Path(target_dir)
        if not target_dir.exists():
            try:
                target_dir.mkdir(parents=True)
            except OSError as e:
                return Result(False, f'Error creating {target_dir}: {e}')
            if target_dir.exists():
                return Result(True, f'{target_dir} created', target_dir)
            else:
                return Result(False, f'Error creating {target_dir}')
        else:
            return Result(True, f'{target_dir} already exists', target_dir)

    @staticmethod
    def remove_target_path(target_path: str or Path) -> Result:
        """
        A static method that removes a file or a directory.

        :param target_path: a Path object or a string representing the target path

        :return: a Result object
        """
        target_path = Path(target_path)
        if target_path.exists():
            try:
                if target_path.is_file():
                    os.remove(target_path)
                else:
                    shutil.rmtree(target_path)
            except OSError as e:
                return Result(False, f'Error removing {target_path}: {e}')
            if target_path.exists():
                return Result(False, f'Error removing {target_path}')
            else:
                return Result(True, f'{target_path} removed')
        else:
            return Result(True, f'{target_path} not found')

    @staticmethod
    def ready_target_path(target_path: str or Path, ensure_parent_dir=True, delete_existing=False) -> Result:
        """
        Ready the target path for writing.

        :param target_path: a Path object or a string representing the target path
        :param ensure_parent_dir: a flag indicating whether to ensure the parent directory exists
        :param delete_existing: a flag indicating whether to delete the existing file or directory

        :return: a Result object
        """
        target_path = Path(target_path)
        # Ensure target path uses a valid name
        if not SharedFunctions.is_valid_name_for_path(target_path.name):
            return Result(False, f'Invalid name: {target_path.name}')
        # Ensure parent directory exists
        parent_path = target_path.parent
        if ensure_parent_dir and not parent_path.exists():
            result = SharedFunctions.create_target_dir(parent_path)
            if not result.ok:
                return result
        # Ensure target path is ready
        if parent_path.exists():
            if target_path.exists() and delete_existing:
                result = SharedFunctions.remove_target_path(target_path)
                if not result.ok:
                    return result
            if not target_path.exists():
                return Result(True, f'{target_path} ready')
            else:
                return Result(False, f'Error readying {target_path}')
        else:
            return Result(False, f'Parent directory is not ready at {parent_path}')

# endregion