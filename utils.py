
import os
import sys
import subprocess
import traceback
from enum import IntEnum
from error_code import ErrorCode
from typing import *


class PLATFORM(IntEnum):
    MAC = 1
    LINUX = 2
    WINDOWS = 3


class TestUtils:
    search_cmd = {
        PLATFORM.MAC: 'which',
        PLATFORM.LINUX: 'whereis',
        PLATFORM.WINDOWS: 'where'}

    # --------------------------------------------------------------------------
    @staticmethod
    def get_absolute_path() -> str:
        """
        :return: the absolute path of this file
        """
        try:
            the_path = __file__
        except AttributeError:
            sys.exit("__file__ is not defined in current Python environment")

        # In case it's a pyc file, find the accompanying .py file if possible
        if the_path.endswith('.pyc') and os.path.exists(the_path[:-1]):
            the_path = the_path[:-1]

        # sort out the symlink
        the_path = os.path.realpath(the_path)
        return os.path.dirname(the_path)

    # --------------------------------------------------------------------------
    @staticmethod
    def execute_single_command(the_command: str, show_shell: bool = False) -> Any:
        """
        execute one shell command
        :param the_command: the command string
        :param show_shell:
        :return: return code, command stdin and stderr outputs
        """
        if the_command is None:
            raise Exception(ErrorCode.emptyParameter)
        elif not isinstance(the_command, str):
            raise Exception(ErrorCode.badParameterType)

        pro = subprocess.Popen(the_command.split(' '),
                               shell=show_shell,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        cmd_output, cmd_err = pro.communicate()
        return pro.returncode, cmd_output, cmd_err

    # --------------------------------------------------------------------------
    @staticmethod
    def execute_multiple_commands(the_commands: str, show_shell: bool = True) -> Any:
        """
        Execute multiple commands in a single line and are hooked with pipes
        :param the_commands:
        :param show_shell:
        :return:
        """
        if the_commands is None:
            raise Exception(ErrorCode.emptyParameter)
        elif not isinstance(the_commands, str):
            raise Exception(ErrorCode.badParameterType)

        try:
            proc = subprocess.check_output(the_commands, shell=show_shell)
            one_line = proc.decode('utf-8')
            lines = one_line.split('\n')
            return ErrorCode.ok, lines
        except subprocess.CalledProcessError:
            traceback.print_exc()
            return ErrorCode.executeShellCommand, None
