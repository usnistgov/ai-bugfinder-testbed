from os import remove
from os.path import join
from unittest import TestCase

from shutil import rmtree

from bugfinder import settings
from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.processing.dataset.extract import ExtractSampleDataset
from tests import patch_paths


class TestExtractSampleDatasetExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.processing.dataset.extract.LOGGER",
                "bugfinder.base.dataset.LOGGER",
                "bugfinder.utils.containers.LOGGER",
            ],
        )

        self.input_dataset_path = "./tests/fixtures/dataset03"
        self.output_dataset_path = "./tests/fixtures/dataset03_copy"
        self.sample_nb = 5
        dataset = CodeWeaknessClassificationDataset(self.input_dataset_path)

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

        output_dataset = CodeWeaknessClassificationDataset(self.output_dataset_path)
        self.assertEqual(len(output_dataset.test_cases), self.sample_nb)

    def test_shuffle_creates_different_sets(self):
        max_tries = 5
        self.dataset_processing.execute(
            self.output_dataset_path, self.sample_nb, shuffle=True
        )

        test_case_01 = CodeWeaknessClassificationDataset(
            self.output_dataset_path
        ).test_cases

        while max_tries != 0:
            self.dataset_processing.execute(
                self.output_dataset_path, self.sample_nb, shuffle=True, force=True
            )
            test_case_02 = CodeWeaknessClassificationDataset(
                self.output_dataset_path
            ).test_cases
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
        test_case_01 = CodeWeaknessClassificationDataset(
            self.output_dataset_path
        ).test_cases

        self.dataset_processing.execute(
            self.output_dataset_path, self.sample_nb, shuffle=False, force=True
        )
        test_case_02 = CodeWeaknessClassificationDataset(
            self.output_dataset_path
        ).test_cases

        self.assertEqual(test_case_01, test_case_02)
