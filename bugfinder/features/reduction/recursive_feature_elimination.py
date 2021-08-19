"""
"""
from importlib import import_module

import pandas as pd
from sklearn.feature_selection import RFECV, RFE

from bugfinder.features.reduction import AbstractFeatureSelector
from bugfinder.settings import LOGGER
from bugfinder.utils.feature_selection import (
    selection_estimators,
    retrieve_original_columns_name,
)


class FeatureSelector(AbstractFeatureSelector):
    def select_feature(
        self, input_features, input_results, model, cross_validation, features
    ) -> pd.DataFrame:
        LOGGER.debug(
            f"Running RecursiveFeatureElimination with model {model}, selecting "
            f"{features} features (cross_validation={cross_validation})..."
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
        model, model_kwargs = (
            (RFECV, {"min_features_to_select": features})
            if cross_validation
            else (RFE, {"n_features_to_select": features})
        )
        rfe_model_op = model(estimator, **model_kwargs)
        output_features_np = rfe_model_op.fit(input_features, input_results)

        output_features = pd.DataFrame(
            output_features_np,
            columns=retrieve_original_columns_name(
                rfe_model_op, input_features.columns
            ),
            index=input_features.index,
        )
        LOGGER.info(
            f"Applied RecursiveFeatureElimination with model {model}, selecting "
            f"{features} features (cross_validation={cross_validation}): retrieved "
            f"{len(output_features.columns)} features."
        )
        return output_features
