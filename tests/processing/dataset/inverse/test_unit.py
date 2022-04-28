from os import remove
from os.path import join
from unittest import TestCase

from shutil import rmtree
from unittest.mock import patch

from bugfinder import settings
from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.processing.dataset.inverse import InverseDataset
from tests import patch_paths


class TestInverseDatasetExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.processing.dataset.inverse.LOGGER",
                "bugfinder.base.dataset.LOGGER",
                "bugfinder.utils.containers.LOGGER",
            ],
        )

        self.input_dataset_path = "./tests/fixtures/dataset03"
        self.from_dataset_path = "./tests/fixtures/dataset01"
        self.output_dataset_path = "./tests/fixtures/dataset_copy"

        self.dataset = CodeWeaknessClassificationDataset(self.input_dataset_path)
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

    @patch("bugfinder.processing.dataset.inverse.exists")
    def test_from_path_not_exists_fails(self, mock_exists):
        mock_exists.return_value = False

        with self.assertRaises(FileNotFoundError):
            self.dataset_processing.execute("mock_dir", self.from_dataset_path)

    @patch("bugfinder.processing.dataset.inverse.isdir")
    def test_from_path_is_not_dir_fails(self, mock_isdir):
        mock_isdir.return_value = False

        with self.assertRaises(NotADirectoryError):
            self.dataset_processing.execute("mock_dir", self.from_dataset_path)

    def test_number_of_samples_is_correct(self):
        self.dataset_processing.execute(
            self.output_dataset_path, self.from_dataset_path
        )

        output_dataset = CodeWeaknessClassificationDataset(self.output_dataset_path)
        from_dataset = CodeWeaknessClassificationDataset(self.from_dataset_path)

        self.assertEqual(
            len(output_dataset.test_cases),
            len(self.dataset.test_cases) - len(from_dataset.test_cases),
        )

    def test_samples_names_are_correct(self):
        self.dataset_processing.execute(
            self.output_dataset_path, self.from_dataset_path
        )

        output_dataset = CodeWeaknessClassificationDataset(self.output_dataset_path)
        from_dataset = CodeWeaknessClassificationDataset(self.from_dataset_path)

        self.assertEqual(
            output_dataset.test_cases,
            self.dataset.test_cases.difference(from_dataset.test_cases),
        )
