from os import remove
from os.path import join
from unittest import TestCase

from unittest.mock import Mock

from bugfinder import settings
from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.base.processing.files import AbstractFileProcessing
from tests import patch_paths


class TestDatasetFileProcessingExecute(TestCase):
    class MockAbstractFileProcessing(AbstractFileProcessing):
        processed_file = []

        def process_file(self, filepath):
            self.processed_file.append(filepath)

        def match_file(self, filepath) -> bool:
            return True

    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.base.dataset.LOGGER"])

        self.dataset_path = "./tests/fixtures/dataset01"

    def tearDown(self) -> None:
        try:
            remove(join(self.dataset_path, settings.SUMMARY_FILE))
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_process_file_calls_equal_nb_of_files(self):
        dataset_obj = CodeWeaknessClassificationDataset(self.dataset_path)
        data_processing = self.MockAbstractFileProcessing(dataset_obj)
        data_processing.execute()

        self.assertEqual(
            data_processing.processed_file.sort(),
            [
                "./tests/fixtures/dataset01/class02/tc03/item.c",
                "./tests/fixtures/dataset01/class03/tc01/item.c",
                "./tests/fixtures/dataset01/class01/tc03/item.c",
                "./tests/fixtures/dataset01/class01/tc02/item.c",
                "./tests/fixtures/dataset01/class02/tc04/item.c",
                "./tests/fixtures/dataset01/class02/tc01/item.c",
            ].sort(),
        )

    def test_rebuild_index_is_called(self):
        dataset_obj = Mock(spec=CodeWeaknessClassificationDataset)
        dataset_obj.test_cases = list()
        data_processing = self.MockAbstractFileProcessing(dataset_obj)

        data_processing.execute()
        dataset_obj.rebuild_index.assert_called()
