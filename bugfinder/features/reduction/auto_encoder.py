"""
"""
from copy import deepcopy
from os.path import exists

import pandas as pd
from tensorflow import keras

from bugfinder.features.reduction import AbstractFeatureSelector
from bugfinder.settings import LOGGER


class FeatureSelector(AbstractFeatureSelector):
    def train_encoder(self, input_features, dimension, hidden_layers):
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

        features = input_features.sample(frac=1)
        training_samples = int(features.shape[0] * 0.75)
        training_set = features.iloc[:training_samples, :]
        test_set = features.iloc[training_samples:, :]

        autoencoder.fit(
            training_set,
            training_set,
            epochs=50,
            shuffle=True,
            validation_data=(test_set, test_set),
        )

        return encoder

    def select_feature(
        self, input_features, input_results, dry_run, dimension, layers, encoder_path
    ) -> pd.DataFrame:
        layers = layers.split(",")
        arch = deepcopy(layers)
        arch.append(dimension)

        LOGGER.debug(
            f"Applying AutoEncoder at {encoder_path} with architecture {str(arch)}, "
            f"selecting {dimension} features (location: {encoder_path})..."
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
            f"Applied AutoEncoder at {encoder_path} with architecture {str(arch)} and "
            f"computed {output_features.shape[1]} out of {input_features.shape[1]} "
            f"features."
        )
        return output_features
