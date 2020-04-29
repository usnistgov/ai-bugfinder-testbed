from unittest import TestCase
from unittest.mock import patch, Mock

import tensorflow as tf

from bugfinder.dataset import CWEClassificationDataset
from bugfinder.models import ClassifierModel

import pandas as pd

from tests import patch_paths


class MockModel(Mock):
    def train(self, *args, **kwargs):
        return None

    def evaluate(self, *args, **kwargs):
        return {
            "precision": 0.5,
            "recall": 0.5
        }


class MockClassifierModel(ClassifierModel):
    def init_model(self):
        return MockModel()


class TestClassifierModelInit(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = MockClassifierModel(None)

    def test_model_cls_initialized(self):
        self.assertEqual(self.dataset_processing.model_cls, None)

    def test_train_fn_initialized(self):
        self.assertEqual(self.dataset_processing.train_fn, None)

    def test_test_fn_initialized(self):
        self.assertEqual(self.dataset_processing.test_fn, None)

    def test_colmuns_initialized(self):
        self.assertEqual(self.dataset_processing.columns, None)


class TestClassifierModelExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(self, [
            "bugfinder.models.LOGGER"
        ])

        self.dataset = Mock(spec=CWEClassificationDataset)
        self.dataset.features = pd.read_csv(
            "tests/fixtures/dataset01/features/features.csv"
        )
        self.dataset_processing = MockClassifierModel(self.dataset)
        self.dataset_processing.model_cls = self.dataset_processing.init_model()

    def test_exception_raised_if_model_class_is_none(self):
        self.dataset_processing.model_cls = None

        with self.assertRaises(Exception):
            self.dataset_processing.execute()

    def test_columns_are_correct(self):
        expected_columns = ["feat000", "feat001", "feat002", "feat003"]
        
        self.dataset_processing.execute()

        self.assertListEqual(list(self.dataset_processing.columns), expected_columns)

    @patch("tests.models.test_unit.MockClassifierModel.init_model")
    def test_init_model_called(self, mock_init_model):
        mock_init_model.return_value = self.dataset_processing.model_cls
        self.dataset_processing.execute()

        self.assertTrue(mock_init_model.called)

    @patch("tests.models.test_unit.MockModel.train")
    def test_model_train_called(self, mock_train):
        mock_train.return_value = None
        self.dataset_processing.execute()

        self.assertTrue(mock_train.called)

    @patch("tests.models.test_unit.MockModel.evaluate")
    def test_model_evaluate_called(self, mock_evaluate):
        mock_evaluate.return_value = {
            "precision": 0.5,
            "recall": 0.5
        }
        self.dataset_processing.execute()

        self.assertTrue(mock_evaluate.called)
