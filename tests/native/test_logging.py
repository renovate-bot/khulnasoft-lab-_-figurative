import unittest
import logging

from figurative.utils.log import get_verbosity, set_verbosity, DEFAULT_LOG_LEVEL


class FigurativeLogger(unittest.TestCase):
    """Make sure we set the logging levels correctly"""

    _multiprocess_can_split_ = True

    def test_logging(self):
        set_verbosity(1)
        self.assertEqual(get_verbosity("figurative.native.cpu.abstractcpu"), logging.WARNING)
        self.assertEqual(get_verbosity("figurative.ethereum.abi"), logging.INFO)

        set_verbosity(0)
        self.assertEqual(get_verbosity("figurative.native.cpu.abstractcpu"), DEFAULT_LOG_LEVEL)
        self.assertEqual(get_verbosity("figurative.ethereum.abi"), DEFAULT_LOG_LEVEL)
