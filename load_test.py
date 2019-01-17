import signal
import platform
import os
import sys
import subprocess
import traceback
from enum import Enum
from error_code import ErrorCode
from utils import *


class LoadTest:
    # --------------------------------------------------------------------------
    @staticmethod
    def check_load_tool_settings(tool_name, expected_exit_code):
        os_type = platform.platform()
        if "darwin" in os_type.lower():
            my_machine = PLATFORM.MAC
        elif "linux" in os_type.lower():
            my_machine = PLATFORM.LINUX
        elif "windows" in os_type.lower():
            my_machine = PLATFORM.WINDOWS

        required_version = 30
        current_version = sys.version_info.major * 10 + sys.version_info.minor
        if current_version < required_version:
            raise Exception(ErrorCode.pythonVersionTooOld, "Python 3.0 is required, and you are running v{}.{}".format(
                sys.version_info.major, sys.version_info.minor))

        # Let's check where the load test tool is installed
        ret, output, out_err = TestUtils.execute_single_command("{} {}"
                            .format(TestUtils.search_cmd[my_machine], tool_name))

        if ret != 0:
            raise Exception(ErrorCode.toolNotInstalled)
        else:
            print('\n{} is installed at {}\n'.format(tool_name, output.decode('utf-8')))

        ret, output, out_err = TestUtils.execute_single_command("{} --help".format(tool_name))
        if ret != expected_exit_code:
            raise Exception(ErrorCode.toolNotProperlyInstalled, "Error executing {}".format(tool_name))

        return 0

