from unittest import TestCase
from unittest.mock import patch, Mock

from bugfinder.dataset import CWEClassificationDataset
from tests import patch_paths
from bugfinder.features.reduction.univariate_select import (
    FeatureSelector as UnivariateSelect,
)
import pandas as pd
import numpy as np


class TestFeatureSelectorSelectFeature(TestCase):
    class MockGenericUnivariateSelect:
        def fit_transform(self, input_features, input_results):
            return np.ones((50, 5))

    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.features.reduction.univariate_select.LOGGER",
            ],
        )
        dataset = Mock(spec=CWEClassificationDataset)
        self.dataset_processing = UnivariateSelect(dataset)
        self.kwargs = {
            "input_features": pd.DataFrame(np.random.rand(50, 15)),
            "input_results": np.random.randint(0, 1, (50,)),
            "dry_run": False,
            "function": "chi2",
            "mode": "k_best",
            "param": 5,
        }

    @patch(
        "bugfinder.features.reduction.univariate_select"
        ".retrieve_original_columns_name"
    )
    @patch(
        "bugfinder.features.reduction.univariate_select.feature_selection"
        ".GenericUnivariateSelect"
    )
    def test_int_mode_return_output_features(
        self,
        mock_generic_univariate_select,
        mock_retrieve_original_columns_name,
    ):
        mock_generic_univariate_select.return_value = self.MockGenericUnivariateSelect()
        mock_retrieve_original_columns_name.return_value = range(5)

        output_features = self.dataset_processing.select_feature(**self.kwargs)
        self.assertEqual(output_features.shape, (50, 5))

    @patch(
        "bugfinder.features.reduction.univariate_select"
        ".retrieve_original_columns_name"
    )
    @patch(
        "bugfinder.features.reduction.univariate_select.feature_selection"
        ".GenericUnivariateSelect"
    )
    def test_float_mode_return_output_features(
        self,
        mock_generic_univariate_select,
        mock_retrieve_original_columns_name,
    ):
        self.kwargs["mode"] = "mock_float_mode"
        mock_generic_univariate_select.return_value = self.MockGenericUnivariateSelect()
        mock_retrieve_original_columns_name.return_value = range(5)

        output_features = self.dataset_processing.select_feature(**self.kwargs)
        self.assertEqual(output_features.shape, (50, 5))
