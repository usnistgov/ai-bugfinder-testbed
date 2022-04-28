from unittest import TestCase
from unittest.mock import patch, Mock

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from tests import patch_paths
from bugfinder.features.reduction.variance_threshold import (
    FeatureSelector as VarianceThreshold,
)
import pandas as pd
import numpy as np


class TestFeatureSelectorSelectFeature(TestCase):
    class MockVarianceThreshold:
        def fit_transform(self, input_features, input_results):
            return np.ones((50, 5))

    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.features.reduction.variance_threshold.LOGGER",
            ],
        )
        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing = VarianceThreshold(dataset)
        self.kwargs = {
            "input_features": pd.DataFrame(np.random.rand(50, 15)),
            "input_results": np.random.randint(0, 1, (50,)),
            "dry_run": False,
            "threshold": 0.5,
        }

    @patch(
        "bugfinder.features.reduction.variance_threshold"
        ".retrieve_original_columns_name"
    )
    @patch("bugfinder.features.reduction.variance_threshold.VarianceThreshold")
    def test_return_output_features(
        self,
        mock_variance_threshold,
        mock_retrieve_original_columns_name,
    ):
        mock_variance_threshold.return_value = self.MockVarianceThreshold()
        mock_retrieve_original_columns_name.return_value = range(5)

        output_features = self.dataset_processing.select_feature(**self.kwargs)
        self.assertEqual(output_features.shape, (50, 5))
