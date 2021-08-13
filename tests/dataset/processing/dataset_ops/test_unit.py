import os
from os import remove
from os.path import join
from shutil import rmtree
from unittest import TestCase
from unittest.mock import patch, Mock

from bugfinder import settings
from bugfinder.dataset import CWEClassificationDataset
from bugfinder.dataset.processing.dataset_ops import (
    CopyDataset,
    ExtractSampleDataset,
    InverseDataset,
    RightFixer,
)
from tests import directory_shasum, patch_paths


class TestCopyDatasetExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.dataset.processing.dataset_ops.LOGGER",
                "bugfinder.dataset.LOGGER",
                "bugfinder.dataset.CWEClassificationDataset.process",
            ],
        )

        self.input_dataset_path = "./tests/fixtures/dataset01"
        self.output_dataset_path = "./tests/fixtures/dataset01_copy"
        dataset = CWEClassificationDataset(self.input_dataset_path)

        self.dataset_processing = CopyDataset(dataset)

    def tearDown(self) -> None:
        try:
            remove(join(self.input_dataset_path, settings.SUMMARY_FILE))
            rmtree(self.output_dataset_path)
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_dataset_checksums_are_equal(self):
        input_checksum = directory_shasum(self.input_dataset_path)
        self.dataset_processing.execute(self.output_dataset_path)

        output_checksum = directory_shasum(self.output_dataset_path)

        self.assertEqual(input_checksum, output_checksum)

    def test_cannot_overwrite_without_force_true(self):
        self.dataset_processing.execute(self.output_dataset_path)

        with self.assertRaises(FileExistsError):
            self.dataset_processing.execute(self.output_dataset_path, False)

    def test_can_overwrite_with_force_true(self):
        self.dataset_processing.execute(self.output_dataset_path)
        self.dataset_processing.execute(self.output_dataset_path, True)


class TestExtractSampleDatasetExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.dataset.processing.dataset_ops.LOGGER",
                "bugfinder.dataset.LOGGER",
            ],
        )

        self.input_dataset_path = "./tests/fixtures/dataset03"
        self.output_dataset_path = "./tests/fixtures/dataset03_copy"
        self.sample_nb = 5
        dataset = CWEClassificationDataset(self.input_dataset_path)

        self.dataset_processing = ExtractSampleDataset(dataset)

    def tearDown(self) -> None:
        try:
            remove(join(self.input_dataset_path, settings.SUMMARY_FILE))
            rmtree(self.output_dataset_path)
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_cannot_overwrite_without_force_true(self):
        self.dataset_processing.execute(self.output_dataset_path, self.sample_nb)
        with self.assertRaises(FileExistsError):
            self.dataset_processing.execute(
                self.output_dataset_path, self.sample_nb, force=False
            )

    def test_can_overwrite_with_force_true(self):
        self.dataset_processing.execute(self.output_dataset_path, self.sample_nb)
        self.dataset_processing.execute(
            self.output_dataset_path, self.sample_nb, force=True
        )

    def test_number_of_samples_is_correct(self):
        self.dataset_processing.execute(self.output_dataset_path, self.sample_nb)

        output_dataset = CWEClassificationDataset(self.output_dataset_path)
        self.assertEqual(len(output_dataset.test_cases), self.sample_nb)

    def test_shuffle_creates_different_sets(self):
        max_tries = 5
        self.dataset_processing.execute(
            self.output_dataset_path, self.sample_nb, shuffle=True
        )

        test_case_01 = CWEClassificationDataset(self.output_dataset_path).test_cases

        while max_tries != 0:
            self.dataset_processing.execute(
                self.output_dataset_path, self.sample_nb, shuffle=True, force=True
            )
            test_case_02 = CWEClassificationDataset(self.output_dataset_path).test_cases
            try:
                self.assertEqual(test_case_01, test_case_02)
                max_tries -= 1
            except AssertionError:
                return

        raise AssertionError("test cases lists are equal")

    def test_no_shuffle_creates_same_sets(self):
        self.dataset_processing.execute(
            self.output_dataset_path, self.sample_nb, shuffle=False
        )
        test_case_01 = CWEClassificationDataset(self.output_dataset_path).test_cases

        self.dataset_processing.execute(
            self.output_dataset_path, self.sample_nb, shuffle=False, force=True
        )
        test_case_02 = CWEClassificationDataset(self.output_dataset_path).test_cases

        self.assertEqual(test_case_01, test_case_02)


class TestInverseDatasetExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.dataset.processing.dataset_ops.LOGGER",
                "bugfinder.dataset.LOGGER",
            ],
        )

        self.input_dataset_path = "./tests/fixtures/dataset03"
        self.from_dataset_path = "./tests/fixtures/dataset01"
        self.output_dataset_path = "./tests/fixtures/dataset_copy"

        self.dataset = CWEClassificationDataset(self.input_dataset_path)
        self.dataset_processing = InverseDataset(self.dataset)

    def tearDown(self) -> None:
        try:
            remove(join(self.input_dataset_path, settings.SUMMARY_FILE))
            remove(join(self.from_dataset_path, settings.SUMMARY_FILE))
            rmtree(self.output_dataset_path)
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_cannot_overwrite_without_force_true(self):
        self.dataset_processing.execute(
            self.output_dataset_path, self.from_dataset_path
        )

        with self.assertRaises(FileExistsError):
            self.dataset_processing.execute(
                self.output_dataset_path, self.from_dataset_path, force=False
            )

    def test_can_overwrite_with_force_true(self):
        self.dataset_processing.execute(
            self.output_dataset_path, self.from_dataset_path
        )
        self.dataset_processing.execute(
            self.output_dataset_path, self.from_dataset_path, force=True
        )

    @patch("bugfinder.dataset.processing.dataset_ops.exists")
    def test_from_path_not_exists_fails(self, mock_exists):
        mock_exists.return_value = False

        with self.assertRaises(FileNotFoundError):
            self.dataset_processing.execute("mock_dir", self.from_dataset_path)

    @patch("bugfinder.dataset.processing.dataset_ops.isdir")
    def test_from_path_is_not_dir_fails(self, mock_isdir):
        mock_isdir.return_value = False

        with self.assertRaises(NotADirectoryError):
            self.dataset_processing.execute("mock_dir", self.from_dataset_path)

    def test_number_of_samples_is_correct(self):
        self.dataset_processing.execute(
            self.output_dataset_path, self.from_dataset_path
        )

        output_dataset = CWEClassificationDataset(self.output_dataset_path)
        from_dataset = CWEClassificationDataset(self.from_dataset_path)

        self.assertEqual(
            len(output_dataset.test_cases),
            len(self.dataset.test_cases) - len(from_dataset.test_cases),
        )

    def test_samples_names_are_correct(self):
        self.dataset_processing.execute(
            self.output_dataset_path, self.from_dataset_path
        )

        output_dataset = CWEClassificationDataset(self.output_dataset_path)
        from_dataset = CWEClassificationDataset(self.from_dataset_path)

        self.assertEqual(
            output_dataset.test_cases,
            self.dataset.test_cases.difference(from_dataset.test_cases),
        )


class TestRightFixer(TestCase):
    def tearDown(self) -> None:
        try:
            remove(join(self.input_dataset_path, settings.SUMMARY_FILE))
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_right_are_fixed(self):
        patch_paths(
            self,
            [
                "bugfinder.dataset.processing.dataset_ops.LOGGER",
                "bugfinder.dataset.LOGGER",
            ],
        )

        self.input_dataset_path = "./tests/fixtures/dataset01"
        sample_uid = 20000
        sample_gid = 25000

        self.dataset = CWEClassificationDataset(self.input_dataset_path)
        self.dataset_processing = RightFixer(self.dataset)

        self.dataset_processing.execute(
            command_args=". %s %s" % (sample_uid, sample_gid)
        )

        self.assertEqual(os.stat(self.input_dataset_path).st_uid, sample_uid)
        self.assertEqual(os.stat(self.input_dataset_path).st_gid, sample_gid)

        self.dataset_processing.execute(
            command_args=". %s %s" % (os.getuid(), os.getgid())
        )

        self.assertEqual(os.stat(self.input_dataset_path).st_uid, os.getuid())
        self.assertEqual(os.stat(self.input_dataset_path).st_gid, os.getgid())
