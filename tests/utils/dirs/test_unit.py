"""
"""
import unittest
from unittest.mock import patch

from bugfinder.utils.dirs import copy_dir


class TestCopyDir(unittest.TestCase):
    def mock_return_true_for_input(self, directory):
        return directory == self.input

    @classmethod
    def setUpClass(cls) -> None:
        cls.input = "input"
        cls.output = "output"

    def setUp(self) -> None:
        patch_exists = patch("bugfinder.utils.dirs.exists")
        patch_isdir = patch("bugfinder.utils.dirs.isdir")
        patch_rmtree = patch("bugfinder.utils.dirs.rmtree")
        patch_copytree = patch("bugfinder.utils.dirs.copytree")
        patch_logger = patch("bugfinder.utils.dirs.LOGGER")

        self.mock_exists = patch_exists.start()
        self.mock_isdir = patch_isdir.start()
        self.mock_rmtree = patch_rmtree.start()
        self.mock_copytree = patch_copytree.start()
        self.mock_logger = patch_logger.start()

        self.mock_rmtree.return_value = True
        self.mock_copytree.return_value = True

        self.addCleanup(patch_exists.stop)
        self.addCleanup(patch_isdir.stop)
        self.addCleanup(patch_rmtree.stop)
        self.addCleanup(patch_copytree.stop)
        self.addCleanup(patch_logger.stop)

    def test_returns_true(self):
        self.mock_exists.side_effect = self.mock_return_true_for_input
        self.mock_isdir.return_value = True

        self.assertTrue(copy_dir(self.input, self.output))

    def test_src_is_not_dir_returns_false(self):
        self.mock_exists.side_effect = self.mock_return_true_for_input
        self.mock_isdir.return_value = False

        self.assertFalse(copy_dir(self.input, self.output))

    def test_src_does_not_exist_returns_false(self):
        self.mock_exists.return_value = False
        self.mock_isdir.return_value = True

        self.assertFalse(copy_dir(self.input, self.output))

    def test_src_exists_returns_true(self):
        self.mock_exists.return_value = True
        self.mock_isdir.return_value = True

        self.assertTrue(copy_dir(self.input, self.output))
