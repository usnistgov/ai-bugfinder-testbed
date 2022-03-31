from unittest import TestCase
from unittest.mock import patch, Mock

from bugfinder.dataset import CodeWeaknessClassificationDataset
from tests import patch_paths
from bugfinder.features.reduction.sequential_feature_selector import (
    FeatureSelector as SequentialFeatureSelector,
)
import pandas as pd
import numpy as np

from tests.features.reduction.test_unit import MockEstimator


class TestFeatureSelectorSelectFeature(TestCase):
    class MockSequentialFeatureExtractor:
        def fit(self, input_features, input_results):
            return np.ones((50, 5))

    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.features.reduction.sequential_feature_selector.LOGGER",
            ],
        )
        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing = SequentialFeatureSelector(dataset)
        self.kwargs = {
            "input_features": pd.DataFrame(np.random.rand(50, 15)),
            "input_results": np.random.randint(0, 1, (50,)),
            "dry_run": False,
            "model": "mock_model",
            "direction": "forward",
            "features": 5,
        }
        self.selection_estimators = {
            "mock_model": {
                "package": "sklearn.linear_model",
                "class": "LogisticRegression",
                "kwargs": {},
            }
        }

    @patch(
        "bugfinder.features.reduction.sequential_feature_selector"
        ".retrieve_original_columns_name"
    )
    @patch(
        "bugfinder.features.reduction.sequential_feature_selector"
        ".SequentialFeatureSelector"
    )
    @patch("bugfinder.features.reduction.sequential_feature_selector.getattr")
    @patch("bugfinder.features.reduction.sequential_feature_selector.import_module")
    @patch(
        "bugfinder.features.reduction.sequential_feature_selector.selection_estimators"
    )
    def test_return_output_features(
        self,
        mock_selection_estimators,
        mock_import_module,
        mock_getattr,
        mock_sequential_feature_selector,
        mock_retrieve_original_columns_name,
    ):
        mock_selection_estimators.return_value = self.selection_estimators
        mock_import_module.return_value = None
        mock_getattr.return_value = MockEstimator
        mock_sequential_feature_selector.return_value = (
            self.MockSequentialFeatureExtractor()
        )
        mock_retrieve_original_columns_name.return_value = range(5)

        output_features = self.dataset_processing.select_feature(**self.kwargs)
        self.assertEqual(output_features.shape, (50, 5))
