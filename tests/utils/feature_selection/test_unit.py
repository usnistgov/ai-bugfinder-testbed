from os.path import join
from unittest.mock import Mock

import unittest
from sklearn.feature_selection import VarianceThreshold
import pandas as pd

from bugfinder import settings
from bugfinder.utils.feature_selection import (
    retrieve_original_columns_name,
    selection_estimators,
)


class TestRetrieveOriginalColumnsName(unittest.TestCase):
    def test_get_support_fail_throws_exception(self):
        mock_selection_model = Mock(spec=VarianceThreshold)
        mock_selection_model.get_support.side_effect = Exception(
            "get_support exception"
        )

        with self.assertRaises(Exception):
            retrieve_original_columns_name(mock_selection_model, [])

    def test_non_existing_index_throws_exception(self):
        mock_selection_model = Mock(spec=VarianceThreshold)
        mock_selection_model.get_support.return_value = [0, 1, 2]

        with self.assertRaises(Exception):
            retrieve_original_columns_name(mock_selection_model, [])

    def test_success_returns_correct_items(self):
        mock_selection_model = Mock(spec=VarianceThreshold)
        mock_selection_model.get_support.return_value = [0, 1, 2]

        result = retrieve_original_columns_name(
            mock_selection_model, ["a", "b", "c", "d"]
        )

        self.assertEqual(result, ["a", "b", "c"])


class TestSelectionEstimators(unittest.TestCase):
    def test_all_entry_contains_expected_keys(self):
        expected_keys = ["package", "class", "kwargs"]
        result = selection_estimators()

        for value in result.values():
            for expected_key in expected_keys:
                self.assertIn(expected_key, value.keys())
