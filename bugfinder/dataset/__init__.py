"""
"""
from enum import Enum
from os import listdir, walk
from os.path import exists, isdir, join, dirname

import pandas as pd

from bugfinder.settings import LOGGER, DATASET_DIRS
from bugfinder.utils.processing import is_processing_stack_valid
from bugfinder.utils.statistics import get_time


class DatasetQueueRetCode(Enum):
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

        self.classes = list()
        self.test_cases = set()
        self.features = pd.DataFrame()
        self.feats_ver = 0
        self.stats = list()
        self.ops_queue = list()

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

    def queue_operation(self, op_class, op_args=None):
        if op_args is None:
            op_args = dict()

        self.ops_queue.append({"class": op_class, "args": op_args})

    def process(self):
        _time = get_time()
        LOGGER.debug("Processing ops queue...")

        if not is_processing_stack_valid(self.ops_queue):
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
            current_op += 1

            LOGGER.info(
                "Running operation %d/%d (%s)..."
                % (current_op, total_op, operation_class.__class__.__name__)
            )

            try:
                # If args are defined, pass them to execute command
                if operation["args"] is not None:
                    operation["class"](self).execute(**operation["args"])
                else:
                    operation["class"](self).execute()
            except Exception as e:
                LOGGER.error(
                    "Operation %d/%d failed: %s." % (current_op, total_op, str(e))
                )

                # Clear the operation queue and exit
                self.ops_queue.clear()
                return DatasetQueueRetCode.OPERATION_FAIL

        LOGGER.info("%d operations run in %dms." % (total_op, get_time() - _time))

        return DatasetQueueRetCode.OK
