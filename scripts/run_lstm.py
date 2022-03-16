"""
LSTM implementation
"""

from os.path import dirname, join
import sys

sys.path.append(join(dirname(__file__), ".."))

import argparse
import logging
import os

from tensorflow import keras
from bugfinder.settings import LOGGER
from bugfinder.dataset.processing.lstm_utils import process_csv


# TODO: integrate this function in the LSTMClassifierTraining class
def build_model(neurons, input_size):
    LOGGER.info("Building model...")

    model = keras.models.Sequential()

    model.add(
        keras.layers.Bidirectional(
            keras.layers.LSTM(neurons, activation="tanh", return_sequences=True),
            input_shape=(input_size, 1),
        )
    )
    model.add(keras.layers.Bidirectional(keras.layers.LSTM(neurons)))
    model.add(keras.layers.Dense(64, activation="tanh"))
    model.add(keras.layers.Dense(1, activation="sigmoid"))

    LOGGER.info("Compiling model...")

    model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"])

    return model


# TODO: remove this main function and integrate it with the processing queue
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("dataset_path", help="path to the file with the features")

    parser.add_argument(
        "--neurons",
        "-n",
        required=False,
        default=128,
        type=int,
        help="numbers of neurons used in the LSTM layers",
    )

    parser.add_argument(
        "--batch_size",
        "-b",
        required=False,
        default=64,
        type=int,
        help="batch size for model training",
    )

    parser.add_argument(
        "--epochs",
        "-e",
        required=False,
        default=20,
        type=int,
        help="number of epochs for model training",
    )

    args = parser.parse_args()

    x_train, y_train, x_test, y_test = process_csv(args.dataset_path)

    LOGGER.info("Building the model structure...")

    model = build_model(args.neurons, x_train.shape[1])

    LOGGER.info("Training the model...")

    print(x_train.shape)
    model.summary()

    history = model.fit(
        x_train, y_train, batch_size=args.batch_size, epochs=args.epochs, verbose=1
    )

    LOGGER.info("Training complete")
