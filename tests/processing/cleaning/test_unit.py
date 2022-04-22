""" Tests for file operations
"""
from os.path import splitext, exists, join
from unittest import TestCase

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.processing.cleaning import AbstractFileRemover
from shutil import rmtree, copytree

from tests import patch_paths


class CppFileRemover(AbstractFileRemover):
    def match_file(self, filepath) -> bool:
        return splitext(filepath)[1] in [".c", ".cpp"]


class AllFileRemover(AbstractFileRemover):
    def match_file(self, filepath) -> bool:
        return True


class TestAbstractFileRemoverProcessFile(TestCase):
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

    def tearDown(self) -> None:
        try:
            rmtree(self.tmp_dataset_path)
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_files_are_removed(self):
        self.dataset_processing = CppFileRemover(self.dataset)

        removed_c_files = [
            "class01/tc02/item.c",
            "class01/tc03/item.c",
            "class02/tc01/item.c",
            "class02/tc03/item.c",
            "class02/tc04/item.c",
            "class03/tc01/item.c",
        ]
        self.dataset_processing.execute()

        for c_file in removed_c_files:
            self.assertFalse(exists(join(self.tmp_dataset_path, c_file)))

    def test_non_empty_directory_is_kept(self):
        self.dataset_processing = CppFileRemover(self.dataset)
        self.dataset_processing.execute()
        self.assertTrue(exists(join(self.tmp_dataset_path, "class01/tc03")))

    def test_empty_directory_is_removed(self):
        self.dataset_processing = AllFileRemover(self.dataset)
        self.dataset_processing.execute()

        removed_dirs = [
            "class01/tc02",
            "class02/tc01",
            "class02/tc03",
            "class02/tc04",
            "class03/tc01",
        ]

        for d in removed_dirs:
            self.assertFalse(exists(join(self.tmp_dataset_path, d)))
