""" Tests for file operations
"""
from os.path import exists, join
from unittest import TestCase

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.processing.cleaning.remove_cpp_files import (
    RemoveCppFiles,
)
from shutil import rmtree, copytree

from tests import patch_paths


class TestRemoveCppFilesProcessFile(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.processing.cleaning.LOGGER",
                "bugfinder.base.dataset.LOGGER",
            ],
        )

        dataset_path = "./tests/fixtures/dataset01"
        self.tmp_dataset_path = "./tests/fixtures/dataset_copy"

        copytree(dataset_path, self.tmp_dataset_path)

        self.dataset = CodeWeaknessClassificationDataset(self.tmp_dataset_path)
        self.dataset_processing = RemoveCppFiles(self.dataset)

    def tearDown(self) -> None:
        try:
            rmtree(self.tmp_dataset_path)
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_cpp_files_are_removed(self):
        self.dataset_processing.execute()
        self.assertFalse(exists(join(self.tmp_dataset_path, "class02/tc04")))
