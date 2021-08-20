"""
"""
import pandas as pd
from sklearn.feature_selection import SelectFromModel

from bugfinder.features.reduction import AbstractFeatureSelector
from bugfinder.settings import LOGGER
from bugfinder.utils.feature_selection import (
    selection_estimators,
    retrieve_original_columns_name,
)
from importlib import import_module


class FeatureSelector(AbstractFeatureSelector):
    def select_feature(
        self, input_features, input_results, dry_run, model
    ) -> pd.DataFrame:
        LOGGER.debug(f"Running SelectFromModel with model {model}...")

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
            f"Applied SelectFromModel with model {model}: retrieved "
            f"{len(output_features.columns)} features."
        )
        return output_features
