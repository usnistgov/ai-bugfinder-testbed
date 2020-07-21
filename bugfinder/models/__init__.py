""" Abstract classifier model for the dataset.
"""
from abc import abstractmethod
from os.path import join, exists
from shutil import rmtree, copytree

import tensorflow as tf
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from bugfinder.dataset.processing import DatasetProcessing, DatasetProcessingCategory
from bugfinder.settings import LOGGER
from bugfinder.utils.statistics import has_better_metrics


class ClassifierModel(DatasetProcessing):
    def __init__(self, dataset):
        super().__init__(dataset)

        self.metadata["category"] = str(DatasetProcessingCategory.TRAINING)
        self.model_cls = None
        self.train_fn = None
        self.test_fn = None
        self.columns = None

    @abstractmethod
    def init_model(self, name, **kwargs):
        raise NotImplementedError()

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
        last_results = None

        if self.model_cls is None:
            raise Exception("Parameter 'model_cls' is undefined")

        if result_focus is None:
            result_focus = ["f1-score"]

        output_data = self.dataset.features["result"]
        input_data = self.dataset.features.drop(["result", "name"], axis=1)

        # Renaming input columns to avoid forbidden characters
        input_data.columns = [
            "feat%03d" % feature_nb for feature_nb in range(len(input_data.columns))
        ]

        input_train, input_test, output_train, output_test = train_test_split(
            input_data, output_data, test_size=0.33, random_state=101
        )

        LOGGER.info(
            "Training %s on %d items over %d epochs. Testing on %d items, focusing on %s..."
            % (
                self.model_cls.__name__,
                len(input_train)
                if max_items is None
                else min(max_items, len(input_train)),
                epochs,
                len(input_test),
                ",".join(result_focus),
            )
        )

        self.columns = input_train.columns

        self.train_fn = tf.estimator.inputs.pandas_input_fn(
            x=input_train, y=output_train, shuffle=True, batch_size=batch_size,
        )
        self.test_fn = tf.estimator.inputs.pandas_input_fn(
            x=input_test, y=output_test, shuffle=False, batch_size=batch_size
        )

        # Initialize model dir and backup dir
        model_dir = join(self.dataset.model_dir, name)
        if reset and exists(model_dir):
            LOGGER.info("Removing %s..." % model_dir)
            rmtree(model_dir)

        model_dir_bkp = "%s.bkp" % model_dir

        # Initialize statistics
        self.processing_stats = {
            "samples": {"training": len(input_train), "testing": len(input_test)},
            "results": None,
        }

        if name in self.dataset.summary["training"] and not reset:
            last_results = self.dataset.summary["training"][name]["last_results"]

        # Check if results need to be recalculated
        need_evaluate_model = False
        if last_results is None and not reset and exists(model_dir):
            LOGGER.warning(
                "Summary tampered with, create baseline on current testing data..."
            )
            need_evaluate_model = True

        model = self.init_model(model_dir, **kwargs)

        if need_evaluate_model:  # Evaluate the model if needed
            preds_test = [
                int(pred["classes"][0]) for pred in model.predict(input_fn=self.test_fn)
            ]

            last_results = classification_report(
                output_test,
                preds_test,
                target_names=self.dataset.classes,
                output_dict=True,
            )["weighted avg"]

            LOGGER.info("Report generated for existing model.")

        # Backup the existing model if needs be
        if exists(model_dir_bkp):
            rmtree(model_dir_bkp)

        if last_results is not None and keep_best_model:
            copytree(model.model_dir, model_dir_bkp)

        # Train the model for the given number of epochs
        for epoch_num in range(epochs):
            LOGGER.info("Training dataset for epoch %d/%d..." % (epoch_num + 1, epochs))
            model.train(input_fn=self.train_fn, steps=max_items)

        # Evaluate the model and save the predictions
        preds_test = [
            int(pred["classes"][0]) for pred in model.predict(input_fn=self.test_fn)
        ]

        self.processing_stats["results"] = classification_report(
            output_test,
            preds_test,
            target_names=self.dataset.classes,
            output_dict=True,
        )

        current = {
            "precision": self.processing_stats["results"]["weighted avg"]["precision"]
            * 100,
            "recall": self.processing_stats["results"]["weighted avg"]["recall"] * 100,
            "f1-score": self.processing_stats["results"]["weighted avg"]["f1-score"]
            * 100,
        }

        last = {
            "precision": float("nan"),
            "recall": float("nan"),
            "f1-score": float("nan"),
        }

        if last_results is not None:
            last = {
                "precision": last_results["precision"] * 100,
                "recall": last_results["recall"] * 100,
                "f1-score": last_results["f1-score"] * 100,
            }

        LOGGER.info(
            "Precision: %02.03f%% (%02.03f%%); Recall: %02.03f%% (%02.03f%%); "
            "F-score: %02.03f%% (%02.03f%%)"
            % (
                current["precision"],
                last["precision"],
                current["recall"],
                last["recall"],
                current["f1-score"],
                last["f1-score"],
            )
        )

        if keep_best_model and not has_better_metrics(
            result_focus,
            self.processing_stats["results"]["weighted avg"],
            last_results,
        ):
            LOGGER.warning(
                "Performance decreased from original values. Replacing model with previous "
                "one..."
            )
            rmtree(model_dir)
            copytree(model_dir_bkp, model_dir)

        self.processing_stats["last_results"] = last_results

        if exists(model_dir_bkp):
            rmtree(model_dir_bkp)
