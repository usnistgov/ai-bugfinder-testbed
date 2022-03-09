from os import remove
from os.path import join
from unittest import TestCase
from unittest.mock import patch

import pandas as pd

from bugfinder import settings
from bugfinder.dataset import CWEClassificationDataset, DatasetQueueRetCode
from bugfinder.dataset.processing import DatasetProcessing
from bugfinder.settings import DATASET_DIRS
from tests import MockDatasetProcessing, patch_paths


class TestCWEClassificationDatasetInit(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        patch_paths(
            cls(), [
                "bugfinder.dataset.LOGGER",
                "bugfinder.utils.processing.LOGGER"
            ]
        )

        with patch(
            "bugfinder.dataset.CWEClassificationDataset.rebuild_index"
        ) as mock_rebuild_index:
            mock_rebuild_index.return_value = None
            cls.dataset_path = "mock_dataset_path/"
            cls.dataset = CWEClassificationDataset(cls.dataset_path)

    def tearDown(self) -> None:
        try:
            remove(join(self.dataset_path, settings.SUMMARY_FILE))
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_path_is_correct(self):
        self.assertEqual(self.dataset.path, self.dataset_path)

    def test_joern_dir_is_correct(self):
        self.assertEqual(
            self.dataset.joern_dir, join(self.dataset_path, DATASET_DIRS["joern"])
        )

    def test_neo4j_dir_is_correct(self):
        self.assertEqual(
            self.dataset.neo4j_dir, join(self.dataset_path, DATASET_DIRS["neo4j"])
        )

    def test_feats_dir_is_correct(self):
        self.assertEqual(
            self.dataset.feats_dir, join(self.dataset_path, DATASET_DIRS["feats"])
        )

    def test_classes_is_empty(self):
        self.assertEqual(len(self.dataset.classes), 0)

    def test_test_cases_is_empty(self):
        self.assertEqual(len(self.dataset.test_cases), 0)

    def test_features_is_empty(self):
        self.assertEqual(self.dataset.features.shape, (0, 0))

    def test_feats_version_is_zero(self):
        self.assertEqual(self.dataset.feats_version, 1)

    def test_stats_is_empty(self):
        self.assertEqual(len(self.dataset.stats), 0)

    def test_ops_queue_is_empty(self):
        self.assertEqual(len(self.dataset.ops_queue), 0)


class TestCWEClassificationDatasetRebuildIndex(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, [
                "bugfinder.dataset.LOGGER",
                "bugfinder.utils.processing.LOGGER"
            ]
        )

    def tearDown(self) -> None:
        try:
            remove(join("./tests/fixtures/dataset01", settings.SUMMARY_FILE))
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors
        try:
            remove(join("./tests/fixtures/dataset02", settings.SUMMARY_FILE))
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_inexistant_dataset_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            CWEClassificationDataset("/dev/null/fake_dataset")

    def test_not_dir_dataset_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            CWEClassificationDataset("./tests/fixtures/dataset01/sample_file.txt")

    def test_indexed_classes_are_correct(self):
        dataset = CWEClassificationDataset("./tests/fixtures/dataset01")

        self.assertEqual(set(dataset.classes), {"class01", "class02", "class03"})

    def test_indexed_test_cases_are_correct(self):
        dataset = CWEClassificationDataset("./tests/fixtures/dataset01")

        self.assertEqual(
            dataset.test_cases,
            {
                "class01/tc02",
                "class01/tc03",
                "class02/tc01",
                "class02/tc03",
                "class02/tc04",
                "class03/tc01",
            },
        )

    def test_features_are_correct(self):
        dataset = CWEClassificationDataset("./tests/fixtures/dataset01")

        self.assertTrue(
            pd.read_csv("./tests/fixtures/dataset01/features/features.csv").equals(
                dataset.features
            )
        )

    def test_stats_are_correct(self):
        dataset = CWEClassificationDataset("./tests/fixtures/dataset01")

        self.assertEqual(set(dataset.stats), {1 / 3, 0.5, 1 / 6})

    def test_empty_dataset(self):
        dataset = CWEClassificationDataset("./tests/fixtures/dataset02")

        self.assertEqual(len(dataset.test_cases), 0)


class TestCWEClassificationDatasetGetFeaturesInfo(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, [
                "bugfinder.dataset.LOGGER",
                "bugfinder.utils.processing.LOGGER"
            ]
        )

    def tearDown(self) -> None:
        try:
            remove(join("./tests/fixtures/dataset01", settings.SUMMARY_FILE))
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors
        try:
            remove(join("./tests/fixtures/dataset02", settings.SUMMARY_FILE))
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_column_types_are_correct(self):
        dataset = CWEClassificationDataset("./tests/fixtures/dataset01")
        expected_result = {"non_empty_cols": 3, "empty_cols": 1}

        self.assertEqual(dataset.get_features_info(), expected_result)

    def test_unexisting_features_raises_error(self):
        dataset = CWEClassificationDataset("./tests/fixtures/dataset02")

        with self.assertRaises(IndexError):
            dataset.get_features_info()


class TestCWEClassificationDatasetQueueOperation(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, [
                "bugfinder.dataset.LOGGER",
                "bugfinder.utils.processing.LOGGER"
            ]
        )

        self.dataset_path = "./tests/fixtures/dataset01"
        self.dataset = CWEClassificationDataset(self.dataset_path)

    def tearDown(self) -> None:
        try:
            remove(join(self.dataset_path, settings.SUMMARY_FILE))
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_queue_size_increases(self):
        initial_queue_size = len(self.dataset.ops_queue)
        self.dataset.queue_operation(None)

        self.assertEqual(len(self.dataset.ops_queue), initial_queue_size + 1)

    def test_added_operation_is_last_operation(self):
        self.dataset.queue_operation(DatasetProcessing)
        self.assertIs(self.dataset.ops_queue[-1]["class"], DatasetProcessing)


class TestCWEClassificationDatasetProcess(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, [
                "bugfinder.dataset.LOGGER",
                "bugfinder.utils.processing.LOGGER"
            ]
        )

        self.dataset_path = "./tests/fixtures/dataset01"
        self.dataset = CWEClassificationDataset(self.dataset_path)

    def tearDown(self) -> None:
        try:
            remove(join(self.dataset_path, settings.SUMMARY_FILE))
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_empty_queue_returns_correct_code(self):
        self.assertEqual(self.dataset.process(), DatasetQueueRetCode.EMPTY_QUEUE)

    def test_operation_with_no_args_returns_correct_code(self):
        mock_operation = MockDatasetProcessing

        self.dataset.queue_operation(mock_operation)

        self.assertEqual(self.dataset.process(), DatasetQueueRetCode.OK)

    def test_operation_with_args_returns_correct_code(self):
        mock_operation = MockDatasetProcessing

        self.dataset.queue_operation(
            mock_operation, {"arg0": "value0", "arg1": "value1"}
        )

        self.assertEqual(self.dataset.process(), DatasetQueueRetCode.OK)

    @patch("tests.MockDatasetProcessing.execute")
    def test_failed_operation_returns_correct_code(self, mock_execute):
        mock_operation = MockDatasetProcessing
        mock_execute.side_effect = Exception()

        self.dataset.queue_operation(mock_operation)

        self.assertEqual(self.dataset.process(), DatasetQueueRetCode.OPERATION_FAIL)

    @patch("bugfinder.dataset.is_processing_stack_valid")
    def test_invalid_queue_returns_correct_code(self, mock_is_processing_stack_valid):
        mock_operation = MockDatasetProcessing
        mock_is_processing_stack_valid.return_value = False

        self.dataset.queue_operation(mock_operation)

        self.assertEqual(self.dataset.process(), DatasetQueueRetCode.INVALID_QUEUE)
