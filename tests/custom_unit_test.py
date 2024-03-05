"""
Adds addition method to unittest for IO checks.

Author: Mustafa Bayramov
spyroot@gmail.com
mbayramo@stanford.edu
"""

import unittest


class CustomTestCase(unittest.TestCase):
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
