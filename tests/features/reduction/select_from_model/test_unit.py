from unittest import TestCase
from unittest.mock import patch, Mock

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from tests import patch_paths
from bugfinder.features.reduction.select_from_model import (
    FeatureSelector as SelectFromModel,
)
import pandas as pd
import numpy as np

from tests.features.reduction.test_unit import MockEstimator


class TestFeatureSelectorSelectFeature(TestCase):
    class MockSelectFromModel:
        def transform(self, input_features):
            return np.ones((50, 5))

    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.features.reduction.select_from_model.LOGGER",
            ],
        )
        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing = SelectFromModel(dataset)
        self.kwargs = {
            "input_features": pd.DataFrame(np.random.rand(50, 15)),
            "input_results": np.random.randint(0, 1, (50,)),
            "dry_run": False,
            "model": "mock_model",
        }
        self.selection_estimators = {
            "mock_model": {
                "package": "sklearn.linear_model",
                "class": "LogisticRegression",
                "kwargs": {},
            }
        }

    @patch(
        "bugfinder.features.reduction.select_from_model"
        ".retrieve_original_columns_name"
    )
    @patch("bugfinder.features.reduction.select_from_model.SelectFromModel")
    @patch("bugfinder.features.reduction.select_from_model.getattr")
    @patch("bugfinder.features.reduction.select_from_model.import_module")
    @patch("bugfinder.features.reduction.select_from_model.selection_estimators")
    def test_return_output_features(
        self,
        mock_selection_estimators,
        mock_import_module,
        mock_getattr,
        mock_select_from_model,
        mock_retrieve_original_columns_name,
    ):
        mock_selection_estimators.return_value = self.selection_estimators
        mock_import_module.return_value = None
        mock_getattr.return_value = MockEstimator
        mock_select_from_model.return_value = self.MockSelectFromModel()
        mock_retrieve_original_columns_name.return_value = range(5)

        output_features = self.dataset_processing.select_feature(**self.kwargs)
        self.assertEqual(output_features.shape, (50, 5))
