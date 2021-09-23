"""
"""
import pandas as pd
from sklearn.feature_selection import VarianceThreshold

from bugfinder.features.reduction import AbstractFeatureSelector
from bugfinder.settings import LOGGER
from bugfinder.utils.feature_selection import retrieve_original_columns_name


class FeatureSelector(AbstractFeatureSelector):
    def select_feature(
        self, input_features, input_results, dry_run, threshold
    ) -> pd.DataFrame:
        LOGGER.debug(f"Running VarianceThreshold with threshold value {threshold}...")

        variance_op = VarianceThreshold(threshold=(threshold * (1 - threshold)))
        output_features_np = variance_op.fit_transform(input_features, input_results)

        output_features = pd.DataFrame(
            output_features_np,
            columns=retrieve_original_columns_name(variance_op, input_features.columns),
            index=input_features.index,
        )
        LOGGER.info(
            f"Applied VarianceThreshold of {threshold}, retrieved "
            f"{output_features.shape[1]}/{input_features.shape[1]} features."
        )
        return output_features