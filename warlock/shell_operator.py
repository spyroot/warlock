import json
import subprocess
from typing import Dict


class ShellOperator:

    @staticmethod
    def run_command(cmd):
        """Run k8s command.
        :param cmd:
        :return:
        """
        result = subprocess.run(
            cmd, capture_output=True, text=True, shell=True
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        else:
            raise Exception(f"Command '{cmd}' failed with error: {result.stderr.strip()}")

    @staticmethod
    def run_command_json(
            cmd: str,
            expect_error: str = None
    ) -> Dict:
        """
        Execute a shell command that should return a JSON and parse the output to a Python dict.

        If an expected error substring is provided and encountered,
        return an empty dictionary instead of raising an exception.

        :param cmd: Command to execute.
        :param expect_error: Substring of the error message that, if found, will not raise an exception but return an empty dict.
        :return: A dictionary with the command output or an empty dictionary for expected errors.
        """
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            # json.JSONDecodeError propagated up
            return json.loads(result.stdout)
        else:
            error_message = result.stderr.strip()
            if expect_error and expect_error in error_message:
                return {}
            else:
                raise Exception(f"Command '{cmd}' failed with error: {error_message}")
