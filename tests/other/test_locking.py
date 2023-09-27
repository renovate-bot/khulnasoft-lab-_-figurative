import unittest
from figurative.native import Figurative
from pathlib import Path


ms_file = str(
    Path(__file__).parent.parent.parent.joinpath("examples", "linux", "binaries", "multiple-styles")
)


class TestResume(unittest.TestCase):
    def test_resume(self):
        m = Figurative(ms_file, stdin_size=17)

        with m.locked_context() as ctx:
            self.assertNotIn("unlocked", str(m._lock))


if __name__ == "__main__":
    unittest.main()
