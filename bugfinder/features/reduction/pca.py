""" Module containing principal component analysis (PCA) feature selector
"""
import pandas as pd
from sklearn.decomposition import PCA

from bugfinder.features.reduction import AbstractFeatureSelector
from bugfinder.settings import LOGGER


class FeatureSelector(AbstractFeatureSelector):
    """PCA feature selector"""

    def select_feature(
        self, input_features, input_results, dry_run, dimension
    ) -> pd.DataFrame:
        """Feature selection algorithm."""
        LOGGER.info("Running PCA to output %d features...", dimension)
        pca_op = PCA(n_components=dimension)
        pca_op.fit(input_features)

        output_features = pd.DataFrame(
            pca_op.transform(input_features),
            columns=["pca%d" % i for i in range(dimension)],
            index=input_features.index,
        )
        LOGGER.info(
            "PCA operation terminated, computed %d out of %d features",
            output_features.shape[1],
            input_features.shape[1],
        )
        return output_features
