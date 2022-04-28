""" Classifier LSTM that read interprocedural sequences of nodes
"""

import json
import numpy as np
import tensorflow as tf

from bugfinder.dataset.processing import ProcessingCategory
from bugfinder.models.sequential import SequentialModel
from bugfinder.settings import LOGGER


class InterprocLSTMTraining(SequentialModel):
    def __init__(self, dataset):
        super().__init__(dataset)

        self.metadata["category"] = str(ProcessingCategory.TRAINING)
        self.model_cls = tf.keras.models.Sequential

    def init_model(self, layers, model_dir, **kwargs):
        return self.model_cls(layers=layers)

    def process_features(features_file, feature_map_file, test_data_ratio=0.33):

        assert 0.0 <= test_data_ratio <= 1.0

        LOGGER.info("Loading feature map...")
        with open(feature_map_file, "rt") as fmap_file:
            fmap = json.load(fmap_file)

        LOGGER.info("Loading features...")
        with open(features_file, "rt") as feat_file:
            feat = json.load(feat_file)

        # Map node types (ASTv3) to one-hot tensors
        nmap = dict(zip(fmap.keys(), np.eye(len(fmap))))
        # TODO Save mapping for later use

        # Calculate the max number of inflows, outflows and path length
        max_inflow = max([max(v) for v in fmap.values()])
        max_outflow = max([len(s["outflow"]) for f in feat.values() for s in f])
        max_pathlen = max([len(path) for path in feat.values()])
        LOGGER.info(f"Longest seq.: {max_pathlen}")

        # x: ast, inflow, outflow, end_of_path for each step
        x_len = len(fmap) + max_inflow * (1 + len(fmap)) + max_outflow + 1
        LOGGER.info(f"Feature size: {x_len}x{max_pathlen}")
        # y: sink for each step
        y_len = 1
        x = np.zeros((len(feat), max_pathlen, x_len))
        y = np.zeros((len(feat), max_pathlen, y_len))
        for p_idx, path in enumerate(feat.values()):
            for s_idx, step in enumerate(path):
                _x = x[p_idx][s_idx]
                _y = y[p_idx][s_idx]
                _x_idx, _y_idx = 0, 0
                # Append a flag describing if the current node/step is a sink
                _y[_y_idx] = 1.0 if step["sink"] else 0.0
                # Convert node's AST to one-hot tensor
                _x[_x_idx : _x_idx + len(fmap)] = nmap[step["ast"]]
                _x_idx += len(fmap)
                # Calculate the largest data size to enable scaling
                max_size = float(
                    max(
                        max(step["outflow"]) if step["outflow"] else 0.0,
                        max([ifl["size"] for ifl in step["inflow"]])
                        if step["inflow"]
                        else 0.0,
                    )
                )
                for i_idx in range(max_inflow):
                    if i_idx < len(step["inflow"]):
                        inflow = step["inflow"][i_idx]
                        # Inflow tensor: [size, multiplexed one-hot tensor of inflow node's AST]
                        # Size is scaled between 0. and 1.
                        _x[_x_idx] = (
                            float(inflow["size"]) / max_size if max_size > 0.0 else 0.0
                        )
                        # Append the current inflow tensor to the full input tensor
                        for ast in inflow["nodes"]:
                            # Multiplex one-hot vector of all inflow nodes' AST
                            _x[_x_idx + 1 : _x_idx + len(fmap) + 1] += nmap[ast]
                    _x_idx += len(fmap) + 1
                for o_idx in range(max_outflow):
                    if o_idx < len(step["outflow"]):
                        outflow_size = step["outflow"][o_idx]
                        # Outflow tensor: [size]
                        _x[_x_idx] = (
                            float(outflow_size) / max_size if max_size > 0.0 else 0.0
                        )
                    _x_idx += 1
                # Append a flag describing whether this step is the last in the path
                _x[_x_idx] = 0.0
                _x_idx += 1
                assert _x_idx == x_len
            # Flip the flag to indicate this was the last step in the path
            _x[-1] = 1.0

        # Split the dataset
        rvals = np.random.rand(len(feat))
        split = rvals < np.percentile(rvals, int(100.0 * (1.0 - test_data_ratio)))
        x_train, x_test = x[split], x[~split]
        y_train, y_test = y[split], y[~split]

        return x_train, x_test, y_train, y_test

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

        input_train, input_test, output_train, output_test = self.process_features(
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
                x=input_test,
                y=output_test,
                use_multiprocessing=True,
                return_dict=True,
            )
        )
