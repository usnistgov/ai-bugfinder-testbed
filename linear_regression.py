"""
"""
import logging

import numpy as np
import pandas as pd
import tensorflow as tf
from scipy.io import mmread
from sklearn.model_selection import train_test_split

from tools.dataset import CWEClassificationDataset as Dataset
from tools.dataset.processing.dataset_ops import *

LOGGER.setLevel(logging.INFO)

if __name__ == "__main__":
    cwe121_1000_dataset_path = "./data/cwe121_1000a"
    cwe121_1000_dataset = Dataset(cwe121_1000_dataset_path)

    features_csv_filename = "%s/features/features.csv" % \
                            cwe121_1000_dataset.path

    if not exists(features_csv_filename):
        LOGGER.info("Creating feature file...")
        features_filename = "%s/features/features.mtx" % \
                            cwe121_1000_dataset.path
        labels_filename = "%s/features/labels.txt" % cwe121_1000_dataset.path

        # Read labels and create pandas Dataframe
        labels = np.genfromtxt(labels_filename, delimiter=',', dtype=None)
        labels = pd.DataFrame(labels)

        # Read features and create pandas Dataframe
        features = mmread(features_filename).tocsr()
        features = pd.DataFrame(features.todense())
        features.columns = [str(c) for c in features.columns]

        # Remove empty columns
        non_empty_cols = list()

        for col in features:
            for item in features[col]:
                if item != 0:
                    non_empty_cols.append(col)
                    break

        empty_cols = [col for col in features if col not in non_empty_cols]

        # Create simple features
        simple_features = features.drop(empty_cols, axis=1)
        simple_features["results"] = labels["f0"].apply(
            lambda it: 1 if it else 0
        )

        simple_features.to_csv(features_csv_filename, index=False)

    LOGGER.info("Creating test train split...")
    feats = pd.read_csv(features_csv_filename)
    input_data = feats.drop("results", axis=1)
    output_data = feats["results"]

    X_train, X_test, y_train, y_test = train_test_split(
        input_data, output_data, test_size=0.33, random_state=101
    )

    feat_cols = list()
    feat_cols_append = feat_cols.append

    for x in X_train.columns:
        feat_cols_append(tf.feature_column.numeric_column(x))

    input_train_fn = tf.estimator.inputs.pandas_input_fn(
        x=X_train, y=y_train, shuffle=True, batch_size=100, num_epochs=100
    )

    lin_cls_model = tf.estimator.LinearClassifier(
        feature_columns=feat_cols, n_classes=2
    )

    LOGGER.info("Training classifier...")
    lin_cls_model.train(input_fn=input_train_fn, steps=100)

    # Test the model
    LOGGER.info("Testing classifier...")
    input_test_fn = tf.estimator.inputs.pandas_input_fn(
        x=X_test,
        y=y_test,
        batch_size=10,
        num_epochs=1,
        shuffle=False
    )
    results = lin_cls_model.evaluate(input_test_fn)

    print(results)



