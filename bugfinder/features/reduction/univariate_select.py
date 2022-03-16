""" Module for univariate feature selection
"""
import pandas as pd
from sklearn import feature_selection

from bugfinder.features.reduction import AbstractFeatureSelector
from bugfinder.settings import LOGGER
from bugfinder.utils.feature_selection import retrieve_original_columns_name


class FeatureSelector(AbstractFeatureSelector):
    """Univariate feature selector"""

    def select_feature(
        self, input_features, input_results, dry_run, function, mode, param
    ) -> pd.DataFrame:
        """Feature selection algorithm"""
        # Need to cast parameter to 'int' for some of the modes
        if mode in ["k_best", "percentile"]:
            param = int(param)

        LOGGER.debug(
            "Running UnivariateSelect with scoring_fn %s, using mode "
            "%s with param %s...",
            str(function),
            str(mode),
            str(param),
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
            "Applied UnivariateSelect with scoring_fn %s, using mode "
            "%s with param %s: retrieved %d/%d features.",
            str(function),
            str(mode),
            str(param),
            len(output_features.columns),
            input_features.shape[1],
        )
        return output_features
