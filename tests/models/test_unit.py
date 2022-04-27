from unittest import TestCase
from unittest.mock import patch, Mock

import pandas as pd

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.models import ClassifierModel
from tests import patch_paths


class MockModel(Mock):
    __name__ = "MockModel"

    @staticmethod
    def train(*args, **kwargs):
        return None

    @staticmethod
    def evaluate(*args, **kwargs):
        return {"precision": 0.5, "recall": 0.5}

    @staticmethod
    def predict(*args, **kwargs):
        return [{"classes": [1]}]


class MockClassifierModel(ClassifierModel):
    def init_model(self, name, **kwargs):
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
        patch_paths(self, ["bugfinder.models.LOGGER"])

        self.dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset.classes = ["class_0", "class_1"]
        self.dataset.summary = {"training": list()}
        self.dataset.model_dir = "mock_model_dir"
        self.dataset.features = pd.read_csv(
            "tests/fixtures/dataset01/features/features.1.csv"
        )
        self.dataset_processing = MockClassifierModel(self.dataset)
        self.dataset_processing.model_cls = self.dataset_processing.init_model(
            "mock_name"
        )

    def test_exception_raised_if_model_class_is_none(self):
        self.dataset_processing.model_cls = None

        with self.assertRaises(Exception):
            self.dataset_processing.execute("mock_name")

    def test_columns_are_correct(self):
        expected_columns = ["feat000", "feat001", "feat002", "feat003"]

        self.dataset_processing.execute("mock_name")

        self.assertListEqual(list(self.dataset_processing.columns), expected_columns)

    @patch("tests.models.test_unit.MockClassifierModel.init_model")
    def test_init_model_called(self, mock_init_model):
        mock_init_model.return_value = self.dataset_processing.model_cls
        self.dataset_processing.execute("mock_name")

        self.assertTrue(mock_init_model.called)

    @patch("tests.models.test_unit.MockModel.train")
    def test_model_train_called(self, mock_train):
        mock_train.return_value = None
        self.dataset_processing.execute("mock_name")

        self.assertTrue(mock_train.called)

    @patch("tests.models.test_unit.MockModel.predict")
    def test_model_predict_called(self, mock_predict):
        mock_predict.return_value = [{"classes": [1]}]
        self.dataset_processing.execute("mock_name")

        self.assertTrue(mock_predict.called)
