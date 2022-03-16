""" Module for the auto-encoder
"""
from copy import deepcopy
from os.path import exists

import pandas as pd
from tensorflow import keras

from bugfinder.features.reduction import AbstractFeatureSelector
from bugfinder.settings import LOGGER


class FeatureSelector(AbstractFeatureSelector):
    """Feature selection with auto-encoder"""

    def train_encoder(self, input_features, dimension, hidden_layers):
        """Training function for the auto-encoder."""
        reverse_hidden_layers = deepcopy(hidden_layers)
        reverse_hidden_layers.reverse()

        encoder = keras.Sequential(
            [keras.Input(shape=(input_features.shape[1],))]
            + [
                keras.layers.Dense(layer_dim, activation="relu")
                for layer_dim in hidden_layers
            ]
            + [keras.layers.Dense(dimension, activation="relu")]
        )

        decoder = keras.Sequential(
            [keras.Input(shape=(dimension,))]
            + [
                keras.layers.Dense(layer_dim, activation="relu")
                for layer_dim in reverse_hidden_layers
            ]
            + [keras.layers.Dense(input_features.shape[1], activation="sigmoid")]
        )

        autoencoder = keras.Sequential(
            [keras.Input(shape=(input_features.shape[1],)), encoder, decoder]
        )
        autoencoder.compile(optimizer="adam", loss="mse")

        # Shuffle input features.
        features = input_features.sample(frac=1)

        # Split samples to train and test data set.
        training_samples = int(features.shape[0] * 0.75)
        training_set = features.iloc[:training_samples, :]
        test_set = features.iloc[training_samples:, :]

        # Fitting the auto-encoder. Input and output should be the same.
        autoencoder.fit(
            training_set,
            training_set,
            epochs=50,
            shuffle=True,
            validation_data=(test_set, test_set),
        )

        # Return the trained encoder.
        return encoder

    def select_feature(
        self, input_features, input_results, dry_run, dimension, layers, encoder_path
    ) -> pd.DataFrame:
        """Feature selection algorithm"""
        layers = layers.split(",")
        arch = deepcopy(layers)
        arch.append(dimension)

        LOGGER.debug(
            "Applying AutoEncoder at %s with architecture %s, selecting %d features...",
            encoder_path,
            str(arch),
            dimension,
        )

        if not exists(encoder_path):
            encoder = self.train_encoder(input_features, dimension, layers)

            if not dry_run:
                encoder.save(encoder_path)
        else:
            encoder = keras.models.load_model(encoder_path)

        output_features_np = encoder.predict(input_features)
        output_features = pd.DataFrame(
            output_features_np,
            columns=[f"enc{idx}" for idx in range(output_features_np.shape[1])],
            index=input_features.index,
        )
        LOGGER.info(
            "Applied AutoEncoder at %s with architecture %s and computed %d out of %d "
            "features.",
            encoder_path,
            str(arch),
            output_features.shape[1],
            input_features.shape[1],
        )
        return output_features
