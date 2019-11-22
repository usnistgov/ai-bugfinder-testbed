"""
"""
import csv
from os.path import join
from shutil import copy
from sklearn.decomposition import TruncatedSVD

import pandas as pd
from tools.dataset.processing import DatasetProcessing
from tools.neo4j import Neo4J3Processing
from tools.settings import LOGGER


class GraphFeatureExtractor(Neo4J3Processing):
    pass


class ExecutePCA(DatasetProcessing):
    def execute(self, final_dimension):
        LOGGER.info("Running PCA for %d output features..." % final_dimension)

        drop_out_cols = ["result", "name"]

        copy(
            join(self.dataset.feats_dir, "features.csv"),
            join(
                self.dataset.feats_dir,
                "features.%d.csv" % self.dataset.feats_ver
            )
        )

        self.dataset.feats_ver += 1
        self.dataset.rebuild_index()

        input_data = self.dataset.features.drop(drop_out_cols, axis=1)
        pca_op = TruncatedSVD(n_components=final_dimension)
        pca_op.fit(input_data)

        output_features = pd.DataFrame(
            pca_op.transform(input_data),
            columns=["pca%d" % i for i in range(final_dimension)],
            index=input_data.index
        )

        for col in drop_out_cols:
            output_features[col] = self.dataset.features[col]

        output_features.to_csv(
            join(self.dataset.feats_dir, "features.csv"), index=False
        )

        LOGGER.info("Feature file created.")



