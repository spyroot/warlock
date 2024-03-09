"""
Adds addition method to unittest i.e.
typical assertions for IO checks, dir check, status code.

Author: Mustafa Bayramov
spyroot@gmail.com
mbayramo@stanford.edu
"""
import os
import subprocess
import time
import unittest
import requests


class ExtendedTestCase(unittest.TestCase):

    def assertCanRead(self, filepath, msg=None):
        """Custom assertion method to check if a file can be read."""
        try:
            with open(filepath, 'r') as file:
                file.read()
        except Exception as e:
            if msg is None:
                msg = f"Unable to read the file '{filepath}'. Error: {e}"
            self.fail(msg)

    def assertCannotRead(self, filepath, msg=None):
        """Asserts that a file cannot be read."""
        try:
            with open(filepath, 'r') as file:
                file.read()
            if msg is None:
                msg = f"Expected not to read the file '{filepath}' but read operation succeeded."
            self.fail(msg)
        except Exception:
            pass

    def assertFileContentEquals(self, filepath, expected_content, msg=None):
        """Asserts that a file's content matches the expected content."""
        try:
            with open(filepath, 'r') as file:
                content = file.read()
                self.assertEqual(content, expected_content, msg)
        except Exception as e:
            self.fail(f"Error reading file '{filepath}': {e}")

    def assertDirectoryIsEmpty(self, dirpath, msg=None):
        """Asserts that a directory is empty."""
        if not os.listdir(dirpath):
            return
        if msg is None:
            msg = f"Expected '{dirpath}' to be empty, but it wasn't."
        self.fail(msg)

    def assertDirectoryIsNotEmpty(
            self,
            dir_path,
            msg=None
    ):
        """Asserts that a directory is not empty."""
        if os.listdir(dir_path):
            return
        if msg is None:
            msg = f"Expected '{dir_path}' to not be empty, but it was."
        self.fail(msg)

    def assertProcessStartsAndStops(
            self,
            start_command,
            stop_command,
            check_string,
            process_timeout=5
    ):
        """Asserts that a process can start and then be stopped."""
        try:
            # Start the process
            subprocess.run(
                start_command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(process_timeout)
            process_check = subprocess.run(check_string, shell=True, stdout=subprocess.PIPE)
            self.assertTrue(process_check.stdout, "Process did not start as expected.")
            subprocess.run(stop_command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            self.fail(f"Process start/stop failed: {e}")

    def assertUrlIsReachable(
            self,
            url,
            status_code_range=(200, 299),
            msg=None
    ):
        """Asserts that a URL is reachable and responds with a status code within the specified range."""
        try:
            response = requests.get(url)
            if not status_code_range[0] <= response.status_code <= status_code_range[1]:
                if msg is None:
                    msg = (f"URL '{url}' returned a status code outside "
                           f"the expected range: {response.status_code}")
                self.fail(msg)
        except requests.exceptions.RequestException as e:
            self.fail(f"Error reaching URL '{url}': {e}")
