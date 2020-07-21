"""
"""
import json
from enum import IntEnum
from os import listdir, walk
from os.path import exists, isdir, join, dirname, realpath

import pandas as pd

from bugfinder.dataset.processing import DatasetProcessingCategory
from bugfinder.settings import LOGGER, DATASET_DIRS
from bugfinder.utils.processing import is_processing_stack_valid
from bugfinder.utils.statistics import get_time


class DatasetQueueRetCode(IntEnum):
    OK = 0
    EMPTY_QUEUE = 1
    INVALID_QUEUE = 2
    OPERATION_FAIL = 3


class CWEClassificationDataset(object):
    ignored_dirs = list(DATASET_DIRS.values())

    def _index_dataset(self):
        LOGGER.debug("Start indexing dataset...")

        if not exists(self.path):
            msg = "%s does not exists" % self.path
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
            for root, dirs, files in walk(item_path):
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
        LOGGER.debug("Start loading feature dataframe...")
        features_filename = join(self.feats_dir, "features.csv")

        if not exists(features_filename):
            LOGGER.debug("Features file does not exist yet.")
            return

        self.features = pd.read_csv(features_filename)
        self._validate_features()
        self.feats_ver = 0

    def __init__(self, dataset_path):
        self.path = join(dataset_path, "")
        self.joern_dir = join(self.path, DATASET_DIRS["joern"])
        self.neo4j_dir = join(self.path, DATASET_DIRS["neo4j"])
        self.feats_dir = join(self.path, DATASET_DIRS["feats"])
        self.model_dir = join(self.path, DATASET_DIRS["models"])
        self.summary_filepath = join(self.path, "summary.json")

        self.classes = list()
        self.test_cases = set()
        self.features = pd.DataFrame()
        self.feats_ver = 0
        self.stats = list()
        self.ops_queue = list()
        self.summary = None

        self.rebuild_index()

    def rebuild_index(self):
        LOGGER.debug("Rebuilding index...")
        _time = get_time()

        self.classes = list()
        self.test_cases = set()
        self.stats = list()

        self._index_dataset()
        self._index_features()

        if len(self.test_cases) > 0:
            self.stats = [st / len(self.test_cases) for st in self.stats]

        _time = get_time() - _time
        LOGGER.info(
            "Dataset index build in %dms. %d test_cases, %d classes, "
            "%d features (v%d)."
            % (
                _time,
                len(self.test_cases),
                len(self.classes),
                self.features.shape[1],
                self.feats_ver,
            )
        )

        self.load_summary()
        self.summary["metadata"] = {
            "test_cases": len(self.test_cases),
            "classes": len(self.classes),
            "features": {"number": self.features.shape[1], "version": self.feats_ver},
        }

    def load_summary(self):
        if not exists(self.summary_filepath):
            self.reset_summary()
            return

        with open(self.summary_filepath, "r") as summary_fp:
            self.summary = json.load(summary_fp)

    def save_summary(self):
        with open(self.summary_filepath, "w") as summary_fp:
            json.dump(self.summary, summary_fp, indent=2)

    def reset_summary(self):
        self.summary = {"metadata": dict(), "processing": list(), "training": dict()}
        self.save_summary()

    def _validate_features(self):
        if self.features.shape[1] < 3:
            raise IndexError("Feature file must contain at least 3 columns")

    def get_features_info(self):
        LOGGER.info(
            "Analyzing features (%dx%d matrix)..."
            % (self.features.shape[0], self.features.shape[1])
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
            "Features contain %d empty columns, %d non-empty columns."
            % (features_info["empty_cols"], features_info["non_empty_cols"])
        )

        return features_info

    def get_classes(self):
        """ List classes identified in the dataset and their id
        """
        class_dict = dict()

        for cat_class in self.classes:
            class_dict[cat_class] = self.classes.index(cat_class)

        return class_dict

    def clear_queue(self):
        self.ops_queue = list()

    def queue_operation(self, op_class, op_args=None):
        if op_args is None:
            op_args = dict()

        self.ops_queue.append({"class": op_class, "args": op_args})

    def process(self):
        _time = get_time()
        LOGGER.debug("Processing ops queue...")

        if not is_processing_stack_valid(self.ops_queue):
            LOGGER.error("Invalid ops queue")
            return DatasetQueueRetCode.INVALID_QUEUE

        total_op = len(self.ops_queue)
        current_op = 0

        # Exit if the queue is empty.
        if total_op == 0:
            LOGGER.info("No operation in queue.")
            return DatasetQueueRetCode.EMPTY_QUEUE

        # Process operation while the queue is not empty.
        while len(self.ops_queue) != 0:
            operation = self.ops_queue.pop(0)  # Get the first op in the queue
            operation_class = operation["class"](self)

            operation_category = operation_class.metadata["category"]

            if operation_category not in self.summary.keys() and operation_category != str(
                DatasetProcessingCategory.__NONE__
            ):
                self.summary[operation_category] = list()

            operation_call = {
                "class": "%s.%s"
                % (
                    operation_class.__class__.__module__,
                    operation_class.__class__.__name__,
                ),
                "args": operation["args"],
            }
            current_op += 1

            LOGGER.info(
                "Running operation %d/%d (%s)..."
                % (current_op, total_op, operation_call["class"])
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
            except Exception as e:
                LOGGER.error(
                    "Operation %d/%d failed: %s." % (current_op, total_op, str(e))
                )

                # Clear the operation queue and exit
                self.ops_queue.clear()
                self.append_summary(
                    operation_call,
                    operation_category,
                    get_time() - op_start_time,
                    dict(),
                    DatasetQueueRetCode.OPERATION_FAIL,
                )
                return DatasetQueueRetCode.OPERATION_FAIL

        LOGGER.info("%d operations run in %dms." % (total_op, get_time() - _time))

        return DatasetQueueRetCode.OK

    def append_summary(self, op_call, op_category, exec_time, op_stats, return_code=-1):
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
                    "sessions": list(),
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
