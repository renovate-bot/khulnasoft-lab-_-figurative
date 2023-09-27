import unittest

import os

from figurative.native import Figurative


class RustTest(unittest.TestCase):
    BIN_PATH = os.path.join(os.path.dirname(__file__), "binaries", "hello_world")

    def setUp(self):
        self.m = Figurative.linux(self.BIN_PATH)

    def test_hello_world(self):
        self.m.run()
