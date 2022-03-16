""" Module to select feature based on a specific estimator
"""
from importlib import import_module

import pandas as pd
from sklearn.feature_selection import SelectFromModel

from bugfinder.features.reduction import AbstractFeatureSelector
from bugfinder.settings import LOGGER
from bugfinder.utils.feature_selection import (
    selection_estimators,
    retrieve_original_columns_name,
)


class FeatureSelector(AbstractFeatureSelector):
    """Feature selector based on a specific estimator"""

    def select_feature(
        self, input_features, input_results, dry_run, model
    ) -> pd.DataFrame:
        """Feature selection algorithm"""
        LOGGER.debug("Running SelectFromModel with model %s...", model)

        # Load package
        estimator_info = selection_estimators()[model]
        package = import_module(estimator_info["package"])

        # Load class and build using the provided input data
        estimator = getattr(package, estimator_info["class"])(
            **estimator_info["kwargs"]
        )
        estimator = estimator.fit(input_features, input_results)

        # Select output feature using scikit-learn
        select_from_model_op = SelectFromModel(estimator, prefit=True)
        output_features_np = select_from_model_op.transform(input_features)

        output_features = pd.DataFrame(
            output_features_np,
            columns=retrieve_original_columns_name(
                select_from_model_op, input_features.columns
            ),
            index=input_features.index,
        )
        LOGGER.info(
            "Applied SelectFromModel with model %s: retrieved %d/%d features.",
            model,
            len(output_features.columns),
            input_features.shape[1],
        )
        return output_features
