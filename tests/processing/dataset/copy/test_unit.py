from os import remove
from os.path import join
from unittest import TestCase

from shutil import rmtree

from bugfinder import settings
from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.processing.dataset.copy import CopyDataset
from tests import directory_shasum, patch_paths


class TestCopyDatasetExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.processing.dataset.copy.LOGGER",
                "bugfinder.base.dataset.LOGGER",
                "bugfinder.utils.containers.LOGGER",
                "bugfinder.base.dataset.CodeWeaknessClassificationDataset.process",
            ],
        )

        self.input_dataset_path = "./tests/fixtures/dataset01"
        self.output_dataset_path = "./tests/fixtures/dataset01_copy"
        dataset = CodeWeaknessClassificationDataset(self.input_dataset_path)

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
