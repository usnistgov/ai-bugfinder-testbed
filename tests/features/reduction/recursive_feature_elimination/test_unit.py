from unittest import TestCase
from unittest.mock import Mock, patch

from bugfinder.dataset import CodeWeaknessClassificationDataset
from tests import patch_paths
import numpy as np
import pandas as pd
from bugfinder.features.reduction.recursive_feature_elimination import (
    FeatureSelector as RecursiveFeatureElimination,
)
from tests.features.reduction.test_unit import MockEstimator


class TestFeatureSelectorSelectFeature(TestCase):
    class MockRFE:
        def fit(self, input_features, input_results):
            return np.ones((50, 5))

    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.features.reduction.recursive_feature_elimination.LOGGER",
            ],
        )
        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing = RecursiveFeatureElimination(dataset)
        self.kwargs = {
            "input_features": pd.DataFrame(np.random.rand(50, 15)),
            "input_results": np.random.randint(0, 1, (50,)),
            "dry_run": False,
            "model": "mock_model",
            "cross_validation": True,
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
        "bugfinder.features.reduction.recursive_feature_elimination"
        ".retrieve_original_columns_name"
    )
    @patch("bugfinder.features.reduction.recursive_feature_elimination.RFECV")
    @patch("bugfinder.features.reduction.recursive_feature_elimination.RFE")
    @patch("bugfinder.features.reduction.recursive_feature_elimination.getattr")
    @patch("bugfinder.features.reduction.recursive_feature_elimination.import_module")
    @patch(
        "bugfinder.features.reduction.recursive_feature_elimination.selection_estimators"
    )
    def test_rfe_operator_with_cross_validation(
        self,
        mock_selection_estimators,
        mock_import_module,
        mock_getattr,
        mock_rfe,
        mock_rfecv,
        mock_retrieve_original_columns_name,
    ):
        mock_selection_estimators.return_value = self.selection_estimators
        mock_import_module.return_value = None
        mock_getattr.return_value = MockEstimator
        mock_rfe.return_value = self.MockRFE()
        mock_rfecv.return_value = self.MockRFE()
        mock_retrieve_original_columns_name.return_value = range(5)

        output_features = self.dataset_processing.select_feature(**self.kwargs)
        self.assertEqual(output_features.shape, (50, 5))

    @patch(
        "bugfinder.features.reduction.recursive_feature_elimination"
        ".retrieve_original_columns_name"
    )
    @patch("bugfinder.features.reduction.recursive_feature_elimination.RFECV")
    @patch("bugfinder.features.reduction.recursive_feature_elimination.RFE")
    @patch("bugfinder.features.reduction.recursive_feature_elimination.getattr")
    @patch("bugfinder.features.reduction.recursive_feature_elimination.import_module")
    @patch(
        "bugfinder.features.reduction.recursive_feature_elimination.selection_estimators"
    )
    def test_rfe_operator_without_cross_validation(
        self,
        mock_selection_estimators,
        mock_import_module,
        mock_getattr,
        mock_rfe,
        mock_rfecv,
        mock_retrieve_original_columns_name,
    ):
        mock_selection_estimators.return_value = self.selection_estimators
        mock_import_module.return_value = None
        mock_getattr.return_value = MockEstimator
        mock_rfe.return_value = self.MockRFE()
        mock_rfecv.return_value = self.MockRFE()
        mock_retrieve_original_columns_name.return_value = range(5)

        self.kwargs["cross_validation"] = False

        output_features = self.dataset_processing.select_feature(**self.kwargs)
        self.assertEqual(output_features.shape, (50, 5))
