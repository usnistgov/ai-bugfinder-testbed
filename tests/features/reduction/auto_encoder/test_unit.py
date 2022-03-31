from unittest import TestCase

import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

from bugfinder.dataset import CodeWeaknessClassificationDataset
from bugfinder.features.reduction.auto_encoder import FeatureSelector as AutoEncoder
from tests import patch_paths


class TestFeatureExtractorTrainEncoder(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.features.reduction.auto_encoder.keras.Sequential.fit",
                "bugfinder.features.reduction.auto_encoder.LOGGER",
            ],
        )

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing = AutoEncoder(dataset)
        self.input_features = pd.DataFrame(np.random.rand(50, 15))

    def test_encoder_output_shape_is_correct(self):
        encoder = self.dataset_processing.train_encoder(self.input_features, 5, [10])
        self.assertEqual(encoder.variables[0].shape, (15, 10))
        self.assertEqual(encoder.variables[2].shape, (10, 5))


class TestFeatureExtractorSelectFeature(TestCase):
    class MockEncoder:
        def __init__(self, output_shape):
            super().__init__()
            self.output_shape = output_shape

        def save(self, encoder_path):
            return None

        def predict(self, input_features: np.array) -> np.array:
            return np.ones(self.output_shape)

    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.features.reduction.auto_encoder.keras.Sequential.fit",
                "bugfinder.features.reduction.auto_encoder.LOGGER",
            ],
        )

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing = AutoEncoder(dataset)
        self.kwargs = {
            "input_features": pd.DataFrame(np.random.rand(50, 15)),
            "input_results": np.random.randint(0, 1, (50,)),
            "dry_run": False,
            "dimension": 5,
            "layers": "5, 10",
            "encoder_path": "mock_encoder_path",
        }
        self.mock_encoder_obj = self.MockEncoder(output_shape=(50, 5))

    @patch("bugfinder.features.reduction.auto_encoder.FeatureSelector.train_encoder")
    @patch("bugfinder.features.reduction.auto_encoder.exists")
    def test_train_encoder_if_model_does_not_exist(
        self, mock_exists, mock_train_encoder
    ):
        mock_exists.return_value = False
        mock_train_encoder.return_value = self.mock_encoder_obj

        self.dataset_processing.select_feature(**self.kwargs)
        self.assertTrue(mock_train_encoder.called)

    @patch.object(MockEncoder, "save")
    @patch("bugfinder.features.reduction.auto_encoder.FeatureSelector.train_encoder")
    @patch("bugfinder.features.reduction.auto_encoder.exists")
    def test_do_not_save_encoder_for_dry_runs(
        self, mock_exists, mock_train_encoder, mock_encoder_save
    ):
        mock_exists.return_value = False
        mock_train_encoder.return_value = self.mock_encoder_obj
        self.kwargs["dry_run"] = True

        self.dataset_processing.select_feature(**self.kwargs)
        self.assertFalse(mock_encoder_save.called)

    @patch.object(MockEncoder, "save")
    @patch("bugfinder.features.reduction.auto_encoder.FeatureSelector.train_encoder")
    @patch("bugfinder.features.reduction.auto_encoder.exists")
    def test_save_encoder_for_regular_runs(
        self, mock_exists, mock_train_encoder, mock_encoder_save
    ):
        mock_exists.return_value = False
        mock_train_encoder.return_value = self.mock_encoder_obj

        self.dataset_processing.select_feature(**self.kwargs)
        self.assertTrue(mock_encoder_save.called)

    @patch("bugfinder.features.reduction.auto_encoder.keras.models.load_model")
    @patch("bugfinder.features.reduction.auto_encoder.exists")
    def test_reload_encoder_if_model_exists(self, mock_exists, mock_load_model):
        mock_exists.return_value = True
        mock_load_model.return_value = self.mock_encoder_obj

        self.dataset_processing.select_feature(**self.kwargs)
        self.assertTrue(mock_load_model.called)

    @patch.object(MockEncoder, "predict")
    @patch("bugfinder.features.reduction.auto_encoder.keras.models.load_model")
    @patch("bugfinder.features.reduction.auto_encoder.exists")
    def test_encoder_predict_is_called(
        self, mock_exists, mock_load_model, mock_predict
    ):
        mock_exists.return_value = True
        mock_load_model.return_value = self.mock_encoder_obj
        mock_predict.return_value = np.random.rand(50, 5)

        self.dataset_processing.select_feature(**self.kwargs)
        self.assertTrue(mock_predict.called)

    @patch("bugfinder.features.reduction.auto_encoder.keras.models.load_model")
    @patch("bugfinder.features.reduction.auto_encoder.exists")
    def test_output_feature_returned(self, mock_exists, mock_load_model):
        mock_exists.return_value = True
        mock_load_model.return_value = self.mock_encoder_obj

        output_features = self.dataset_processing.select_feature(**self.kwargs)
        self.assertTrue(
            (
                output_features.to_numpy() == self.mock_encoder_obj.predict(np.zeros(1))
            ).all()
        )
