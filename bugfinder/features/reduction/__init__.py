from os.path import join, realpath

import pandas as pd
from abc import abstractmethod
from shutil import copy

from bugfinder.dataset.processing import DatasetProcessing
from bugfinder.settings import LOGGER


class AbstractFeatureSelector(DatasetProcessing):
    @abstractmethod
    def select_feature(self, *args, **kwargs) -> pd.DataFrame:
        raise NotImplementedError("Method 'select_feature' needs to be implemented.")

    def execute(self, *args, **kwargs):
        drop_out_cols = ["result", "name"]

        copy(
            join(self.dataset.feats_dir, "features.csv"),
            join(
                self.dataset.feats_dir, "features.%d.csv" % self.dataset.feats_version
            ),
        )

        self.dataset.rebuild_index()

        input_features = self.dataset.features.drop(drop_out_cols, axis=1)
        input_results = self.dataset.features["result"]
        output_features = self.select_feature(
            input_features, input_results, *args, **kwargs
        )

        for col in drop_out_cols:
            output_features[col] = self.dataset.features[col]

        output_features_filepath = realpath(
            join(self.dataset.feats_dir, "features.csv")
        )
        output_features.to_csv(output_features_filepath, index=False)

        LOGGER.info("Feature file saved to '%s'." % output_features_filepath)
