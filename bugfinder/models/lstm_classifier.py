"""
LSTM implementation
"""
import tensorflow as tf

from tensorflow import keras

from bugfinder.models import ClassifierModel


class LSTMClassifierTraining(ClassifierModel):
    def __init__(self, dataset):
        super().__init__(dataset)
        self.model_cls = self.build_model(128, 50)

    def init_model(self, model_dir, **kwargs):
        return None

    # TODO: integrate this function in the LSTMClassifierTraining class
    def build_model(self, neurons, input_size):
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

        model.compile(
            loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"]
        )

        return model
