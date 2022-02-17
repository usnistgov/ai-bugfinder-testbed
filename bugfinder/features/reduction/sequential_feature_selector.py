""" Module for sequential feature selector
"""
from importlib import import_module

import pandas as pd
from sklearn.feature_selection import SequentialFeatureSelector

from bugfinder.features.reduction import AbstractFeatureSelector
from bugfinder.settings import LOGGER
from bugfinder.utils.feature_selection import (
    selection_estimators,
    retrieve_original_columns_name,
)


class FeatureSelector(AbstractFeatureSelector):
    """Sequential feature selector"""

    def select_feature(
        self, input_features, input_results, dry_run, model, direction, features
    ) -> pd.DataFrame:
        """Feature selection algorithm."""
        LOGGER.debug(
            "Running SequentialFeatureSelector with model %s, running %s "
            "and selecting %d/%d features...",
            model,
            direction,
            features,
            input_features.shape[1],
        )

        # Load package
        estimator_info = selection_estimators()[model]
        package = import_module(estimator_info["package"])

        # Load class and build using the provided input data
        estimator = getattr(package, estimator_info["class"])(
            **estimator_info["kwargs"]
        )
        estimator = estimator.fit(input_features, input_results)

        # Select output feature using scikit-learn
        sfs_model_op = SequentialFeatureSelector(
            estimator, n_features_to_select=features, direction=direction
        )
        output_features_np = sfs_model_op.fit(input_features, input_results)

        output_features = pd.DataFrame(
            output_features_np,
            columns=retrieve_original_columns_name(
                sfs_model_op, input_features.columns
            ),
            index=input_features.index,
        )
        LOGGER.info(
            "Applied SequentialFeatureSelector with model %s, running %s "
            "and selected %d/%d features.",
            model,
            direction,
            output_features.shape[1],
            input_features.shape[1],
        )
        return output_features
