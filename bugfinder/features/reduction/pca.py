"""
"""
import pandas as pd
from sklearn.decomposition import PCA

from bugfinder.features.reduction import AbstractFeatureSelector
from bugfinder.settings import LOGGER


class FeatureSelector(AbstractFeatureSelector):
    def select_feature(
        self, input_features, input_results, dry_run, dimension
    ) -> pd.DataFrame:
        LOGGER.info(f"Running PCA to output {dimension} features...")
        pca_op = PCA(n_components=dimension)
        pca_op.fit(input_features)

        output_features = pd.DataFrame(
            pca_op.transform(input_features),
            columns=["pca%d" % i for i in range(dimension)],
            index=input_features.index,
        )
        LOGGER.info(
            f"PCA operation terminated, computed {output_features.shape[1]} "
            f"out of {input_features.shape[1]} features"
        )
        return output_features
