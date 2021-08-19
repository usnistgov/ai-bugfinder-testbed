"""
"""
import pandas as pd
from sklearn import feature_selection

from bugfinder.features.reduction import AbstractFeatureSelector
from bugfinder.settings import LOGGER
from bugfinder.utils.feature_selection import retrieve_original_columns_name


class FeatureSelector(AbstractFeatureSelector):
    def select_feature(
        self, input_features, input_results, function, mode, param
    ) -> pd.DataFrame:
        # Need to cast parameter to 'int' for some of the modes
        if mode in ["k_best", "percentile"]:
            param = int(param)

        LOGGER.debug(
            f"Running UnivariateSelect with scoring_fn {str(function)}, using mode "
            f"{str(mode)} with param {param}..."
        )

        univariate_op = feature_selection.GenericUnivariateSelect(
            score_func=getattr(feature_selection, function), mode=mode, param=param
        )
        output_features_np = univariate_op.fit_transform(input_features, input_results)

        output_features = pd.DataFrame(
            output_features_np,
            columns=retrieve_original_columns_name(
                univariate_op, input_features.columns
            ),
            index=input_features.index,
        )
        LOGGER.info(
            f"Applied UnivariateSelect with scoring_fn {str(function)}, using mode "
            f"{str(mode)} with param {param}: retrieved {len(output_features.columns)} "
            f"features."
        )
        return output_features
