""" Tests for file operations
"""
from os.path import splitext, exists, join
from shutil import rmtree, copytree
from unittest import TestCase

from bugfinder.dataset import CWEClassificationDataset
from bugfinder.dataset.processing.file_ops import DatasetFileRemover, RemoveCppFiles, \
    RemoveInterproceduralTestCases
from tests import patch_paths


class TestDatasetFileRemoverRemoveFile(TestCase):
    class SampleDatasetFileRemover(DatasetFileRemover):
        def is_needed_file(self, filepath):
            return splitext(filepath)[1] != ".h"

        def process_file(self, filepath):
            if splitext(filepath)[1] in [".c", ".cpp"]:
                self._remove_file(filepath)

    def setUp(self) -> None:
        patch_paths(self, [
            "bugfinder.dataset.processing.file_ops.LOGGER",
            "bugfinder.dataset.LOGGER"
        ])

        dataset_path = "./tests/fixtures/dataset01"
        self.tmp_dataset_path = "./tests/fixtures/dataset_copy"

        copytree(dataset_path, self.tmp_dataset_path)

        self.dataset = CWEClassificationDataset(self.tmp_dataset_path)
        self.dataset_processing = self.SampleDatasetFileRemover(self.dataset)

    def tearDown(self) -> None:
        try:
            rmtree(self.tmp_dataset_path)
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_files_are_removed(self):
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
        self.dataset_processing.execute()
        self.assertTrue(exists(join(self.tmp_dataset_path, "class01/tc03")))

    def test_directory_with_ignored_extension_is_removed(self):
        self.dataset_processing.execute()
        self.assertFalse(exists(join(self.tmp_dataset_path, "class01/tc02")))

    def test_empty_directory_is_removed(self):
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


class TestRemoveCppFilesProcessFile(TestCase):
    def setUp(self) -> None:
        patch_paths(self, [
            "bugfinder.dataset.processing.file_ops.LOGGER",
            "bugfinder.dataset.LOGGER"
        ])

        dataset_path = "./tests/fixtures/dataset01"
        self.tmp_dataset_path = "./tests/fixtures/dataset_copy"

        copytree(dataset_path, self.tmp_dataset_path)

        self.dataset = CWEClassificationDataset(self.tmp_dataset_path)
        self.dataset_processing = RemoveCppFiles(self.dataset)

    def tearDown(self) -> None:
        try:
            rmtree(self.tmp_dataset_path)
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_cpp_files_are_removed(self):
        self.dataset_processing.execute()
        self.assertFalse(exists(join(self.tmp_dataset_path, "class02/tc04")))


class TestRemoveInterproceduralTestCasesProcessFile(TestCase):
    def setUp(self) -> None:
        patch_paths(self, [
            "bugfinder.dataset.processing.file_ops.LOGGER",
            "bugfinder.dataset.LOGGER"
        ])

        dataset_path = "./tests/fixtures/dataset01"
        self.tmp_dataset_path = "./tests/fixtures/dataset_copy"

        copytree(dataset_path, self.tmp_dataset_path)

        self.dataset = CWEClassificationDataset(self.tmp_dataset_path)
        self.dataset_processing = RemoveInterproceduralTestCases(self.dataset)

    def tearDown(self) -> None:
        try:
            rmtree(self.tmp_dataset_path)
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_correct_regexp_files_are_removed(self):
        self.dataset_processing.execute()
        self.assertFalse(exists(join(self.tmp_dataset_path, "class03/tc01")))
