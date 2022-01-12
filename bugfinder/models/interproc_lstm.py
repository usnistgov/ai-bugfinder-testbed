""" Classifier LSTM that read interprocedural sequences of nodes
"""

import tensorflow as tf

# from sklearn.metrics import classification_report
# from sklearn.model_selection import train_test_split

from bugfinder.dataset.processing import DatasetProcessing, DatasetProcessingCategory
from bugfinder.settings import LOGGER
from bugfinder.models.sequential import SequentialModel
from bugfinder.dataset.processing.interproc_utils import process_features


class InterprocLSTMTraining(SequentialModel):
    def __init__(self, dataset):
        super().__init__(dataset)

        self.metadata["category"] = str(DatasetProcessingCategory.TRAINING)
        self.model_cls = tf.keras.models.Sequential

    def init_model(self, layers, model_dir, **kwargs):
        return self.model_cls(layers=layers)

    def execute(
        self,
        name,
        batch_size=100,
        max_items=None,
        epochs=1,
        result_focus=None,
        keep_best_model=False,
        reset=False,
        **kwargs,
    ):
        if self.model_cls is None:
            raise Exception("Parameter 'model_cls' is undefined")
        if "features_file" not in kwargs:
            raise Exception("Mandatory parameter 'features_file' is missing")
        if "feature_map_file" not in kwargs:
            raise Exception("Mandatory parameter 'feature_map_file' is missing")

        # FIXME
        self.processing_stats["last_results"] = {}

        input_train, input_test, output_train, output_test = process_features(
            kwargs["features_file"], kwargs["feature_map_file"], test_data_ratio=0.33
        )

        # Initialize model dir and backup dir
        # FIXME make sure your model can save to/load from the 'model_dir'
        # model_dir = join(self.dataset.model_dir, name)
        # if reset and exists(model_dir):
        #     LOGGER.info("Removing %s..." % model_dir)
        #     rmtree(model_dir)
        #
        # model_dir_bkp = "%s.bkp" % model_dir

        # FIXME add your layers here
        layers = [
            tf.keras.layers.InputLayer(input_shape=input_train.shape[-2:]),
            # Masking layer to avoid training on padding
            tf.keras.layers.Masking(mask_value=0.0),
            # Shape [batch, path, features] => [batch, time, lstm_units]
            tf.keras.layers.LSTM(
                16, return_sequences=True, dropout=0.33, recurrent_dropout=0.33
            ),
            # Shape => [batch, path, features]
            # tf.keras.layers.Dense(units=16)
        ]
        model = self.init_model(layers, None, **kwargs)
        model.compile(
            loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"]
        )
        model.summary()
        LOGGER.info(input_train.shape)
        LOGGER.info(output_train.shape)

        # # Backup the existing model if needs be
        # if exists(model_dir_bkp):
        #     rmtree(model_dir_bkp)

        # Train the model for the given number of epochs
        for epoch_num in range(epochs):
            LOGGER.info(f"Training dataset for epoch {epoch_num+1}/{epochs}")
            model.fit(
                x=input_train,
                y=output_train,
                epochs=1,
                validation_split=0.33,
                shuffle=True,
                use_multiprocessing=True,
            )

        # Evaluate the model and save the predictions
        LOGGER.info(
            model.evaluate(
                x=input_test, y=output_test, use_multiprocessing=True, return_dict=True,
            )
        )
