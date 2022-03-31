""" Base classes for managing dataset
"""
from os import listdir, walk
from os.path import exists, isdir, join, dirname, realpath

import json
import pandas as pd
import re
from enum import IntEnum

from bugfinder import settings
from bugfinder.dataset.processing import DatasetProcessingCategory
from bugfinder.settings import LOGGER
from bugfinder.utils.processing import is_processing_stack_valid
from bugfinder.utils.statistics import get_time, display_time


class DatasetQueueRetCode(IntEnum):
    """Enumeration to determine the state of the processing queue."""

    OK = 0
    EMPTY_QUEUE = 1
    INVALID_QUEUE = 2
    OPERATION_FAIL = 3


class CodeWeaknessClassificationDataset:
    """Main dataset class."""

    ignored_dirs = list(settings.DATASET_DIRS.values())

    def _index_dataset(self):
        """Browse the dataset to build various indexes"""
        LOGGER.debug("Indexing test cases...")

        if not exists(self.path):
            msg = "%s does not exists", self.path
            LOGGER.error(msg)
            raise FileNotFoundError(msg)

        # If the path exists, browse directory
        for item in listdir(self.path):
            item_path = join(self.path, item)

            # If item is not a directory or should be ignored, get the next item
            if not isdir(item_path) or item in self.ignored_dirs:
                continue

            # Add item name as new class
            self.classes.append(item)

            # Retrieve the list of files in the directory
            for root, _, files in walk(item_path):
                # Specify full path for test cases and ignore UNIX hidden files
                files = [
                    dirname(join(root, f).replace(self.path, ""))
                    for f in files
                    if not f.startswith(".")
                ]

                self.test_cases.update(files)

            # Sort classes to avoid discrepancies between runs
            self.classes = sorted(self.classes)

            # Compute stats
            self.stats.append(len(self.test_cases) - sum(self.stats))

    def _index_features(self):
        """Browse the dataset to index features."""
        features_filename = join(self.feats_dir, settings.FEATURES_FILE)

        if not exists(features_filename):
            LOGGER.debug("Features file does not exist. Skipping dataframe loading...")
            return

        LOGGER.debug("Loading feature dataframe...")
        self.features = pd.read_csv(features_filename)
        self._validate_features()

        feature_history_version = [
            int(re.sub(r"[^\.]+\.([0-9]+)\.csv", r"\1", feature_file))
            for feature_file in listdir(self.feats_dir)
            if feature_file != settings.FEATURES_FILE
        ]

        self.feats_version = (
            max(feature_history_version) + 1 if len(feature_history_version) > 0 else 1
        )

    def __init__(self, dataset_path, silent=False):
        """Inititialization method"""
        start_time = get_time()
        logger_log_func = LOGGER.debug if silent else LOGGER.info

        self.path = join(dataset_path, "")
        self.joern_dir = join(self.path, settings.DATASET_DIRS["joern"])
        self.neo4j_dir = join(self.path, settings.DATASET_DIRS["neo4j"])
        self.feats_dir = join(self.path, settings.DATASET_DIRS["feats"])
        self.model_dir = join(self.path, settings.DATASET_DIRS["models"])
        self.embeddings_dir = join(self.path, settings.DATASET_DIRS["embeddings"])
        self.summary_filepath = join(self.path, settings.SUMMARY_FILE)

        self.classes = []
        self.test_cases = set()
        self.features = pd.DataFrame()
        self.feats_version = 1
        self.stats = []
        self.ops_queue = []
        self.summary = None

        self.rebuild_index()

        logger_log_func(
            "Dataset initialized in %s.", display_time(get_time() - start_time)
        )

    def rebuild_index(self):
        """Rebuild index"""
        LOGGER.debug("Rebuilding index...")
        _time = get_time()

        self.classes = []
        self.test_cases = set()
        self.stats = []

        self._index_dataset()
        self._index_features()

        if len(self.test_cases) > 0:
            self.stats = [st / len(self.test_cases) for st in self.stats]

        LOGGER.debug(
            "Dataset index build in %s. %d test_cases, %d classes, "
            "%d features (v%d).",
            display_time(get_time() - _time),
            len(self.test_cases),
            len(self.classes),
            self.features.shape[1] - 2,
            self.feats_version,
        )

        self.load_summary()
        self.summary["metadata"] = {
            "test_cases": len(self.test_cases),
            "classes": len(self.classes),
            "features": {
                "number": self.features.shape[1],
                "version": self.feats_version,
            },
        }

    def load_summary(self):
        """Load summary file"""
        if not exists(self.summary_filepath):
            self.reset_summary()
            return

        with open(self.summary_filepath, "r", encoding="utf-8") as summary_fp:
            self.summary = json.load(summary_fp)

    def save_summary(self):
        """Save summary file"""
        with open(self.summary_filepath, "w", encoding="utf-8") as summary_fp:
            json.dump(self.summary, summary_fp, indent=2)

    def reset_summary(self):
        """Reset summary file"""
        self.summary = {"metadata": {}, "processing": [], "training": {}}
        self.save_summary()

    def _validate_features(self):
        """Ensure feature are valid"""
        if self.features.shape[1] < 3:
            raise IndexError("Feature file must contain at least 3 columns")

    def get_features_info(self):
        """Retrieve feature information"""
        LOGGER.info(
            "Analyzing features (%dx%d matrix)...",
            self.features.shape[0],
            self.features.shape[1],
        )

        self._validate_features()

        features_info = {"non_empty_cols": 0, "empty_cols": 0}

        for col in self.features:
            for item in self.features[col]:
                if item != 0:
                    features_info["non_empty_cols"] += 1
                    break

        features_info["empty_cols"] = (
            self.features.shape[1] - features_info["non_empty_cols"]
        )
        features_info["non_empty_cols"] -= 2

        LOGGER.info(
            "Features contain %d empty columns, %d non-empty columns.",
            features_info["empty_cols"],
            features_info["non_empty_cols"],
        )

        return features_info

    def get_classes(self):
        """List classes identified in the dataset and their id"""
        class_dict = {}

        for cat_class in self.classes:
            class_dict[cat_class] = self.classes.index(cat_class)

        return class_dict

    def clear_queue(self):
        """Clear processing queue"""
        self.ops_queue = []

    def queue_operation(self, op_class, op_args=None):
        """Queue operation"""
        if op_args is None:
            op_args = {}

        self.ops_queue.append({"class": op_class, "args": op_args})

    def process(self, silent=False):
        """Run all processing in the processing queue"""
        logger_log_func = LOGGER.debug if silent else LOGGER.info

        _time = get_time()
        LOGGER.debug("Processing ops queue...")

        if not is_processing_stack_valid(self.ops_queue, silent=silent):
            LOGGER.error("Invalid ops queue")
            return DatasetQueueRetCode.INVALID_QUEUE

        total_op = len(self.ops_queue)
        current_op = 0

        # Exit if the queue is empty.
        if total_op == 0:
            logger_log_func("No operation in queue.")
            return DatasetQueueRetCode.EMPTY_QUEUE

        # Process operation while the queue is not empty.
        while len(self.ops_queue) != 0:
            operation = self.ops_queue.pop(0)  # Get the first op in the queue
            operation_class = operation["class"](self)

            operation_category = operation_class.metadata["category"]

            if (
                operation_category not in self.summary.keys()
                and operation_category != str(DatasetProcessingCategory.__NONE__)
            ):
                self.summary[operation_category] = []

            operation_call = {
                "class": "%s.%s"
                % (
                    operation_class.__class__.__module__,
                    operation_class.__class__.__name__,
                ),
                "args": operation["args"],
            }
            current_op += 1

            logger_log_func(
                "Running operation %d/%d (%s)...",
                current_op,
                total_op,
                operation_call["class"],
            )

            op_start_time = get_time()  # Time single operation

            try:
                operation_instance = operation["class"](self)
                # If args are defined, pass them to execute command
                if operation["args"] is not None:
                    operation_instance.execute(**operation["args"])
                else:
                    operation_instance.execute()

                self.append_summary(
                    operation_call,
                    operation_category,
                    get_time() - op_start_time,
                    operation_instance.processing_stats,
                    DatasetQueueRetCode.OK,
                )
            except Exception as exc:
                LOGGER.error(
                    "Operation %d/%d failed: %s.", current_op, total_op, str(exc)
                )

                # Clear the operation queue and exit
                self.ops_queue.clear()
                self.append_summary(
                    operation_call,
                    operation_category,
                    get_time() - op_start_time,
                    {},
                    DatasetQueueRetCode.OPERATION_FAIL,
                )
                return DatasetQueueRetCode.OPERATION_FAIL

        logger_log_func(
            "%d operations run in %s.", total_op, display_time(get_time() - _time)
        )

        return DatasetQueueRetCode.OK

    def append_summary(self, op_call, op_category, exec_time, op_stats, return_code=-1):
        """Append new processing to summary file"""
        processing_ops_summary = {
            "dataset_path": realpath(self.path),
            "operation": op_call,
            "time": exec_time,
            "return_code": return_code,
        }

        processing_ops_summary.update(op_stats)

        if op_category == str(DatasetProcessingCategory.TRAINING):
            if op_call["args"]["name"] not in self.summary[op_category].keys():
                self.summary[op_category][op_call["args"]["name"]] = {
                    "last_results": None,
                    "sessions": [],
                }

            self.summary[op_category][op_call["args"]["name"]][
                "last_results"
            ] = processing_ops_summary["last_results"]
            del processing_ops_summary["last_results"]

            self.summary[op_category][op_call["args"]["name"]]["sessions"].append(
                processing_ops_summary
            )

        elif op_category != str(DatasetProcessingCategory.__NONE__):
            self.summary[op_category].append(processing_ops_summary)

        self.save_summary()
