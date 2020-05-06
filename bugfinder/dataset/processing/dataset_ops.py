import os
import random
from os.path import exists, join, isdir
from shutil import rmtree, copytree

from bugfinder.dataset import CWEClassificationDataset as Dataset
from bugfinder.dataset.processing import (
    DatasetProcessing,
    DatasetProcessingWithContainer,
)
from bugfinder.settings import LOGGER
from bugfinder.utils.statistics import get_time


class CopyDataset(DatasetProcessing):
    def execute(self, to_path, force=False):
        LOGGER.debug(
            "Copying dataset at %s to %s (force=%d)..."
            % (self.dataset.path, to_path, int(force))
        )
        _time = get_time()

        # Cleanup directory if it exists or remove
        if exists(to_path):
            if force:
                try:
                    dest_dataset = Dataset(to_path)
                    dest_dataset.queue_operation(
                        RightFixer,
                        {"command_args": ". %s %s" % (os.getuid(), os.getgid())},
                    )
                    dest_dataset.process()
                finally:
                    rmtree(to_path)
            else:
                raise FileExistsError(
                    "%s already exists. Run with force=True to overwrite the "
                    "directory" % to_path
                )

        copytree(self.dataset.path, to_path)
        LOGGER.debug("Dataset copied in %dms" % (get_time() - _time))


class ExtractSampleDataset(DatasetProcessing):
    def execute(self, to_path, sample_nb, shuffle=True, force=False):
        LOGGER.debug(
            "Extracting %d samples from dataset %s to %s (shuffle=%d, "
            "force=%d)..."
            % (sample_nb, self.dataset.path, to_path, int(shuffle), int(force))
        )
        _time = get_time()

        if exists(to_path):
            if force:
                rmtree(to_path)
            else:
                raise FileExistsError(
                    "%s already exists. Run with force=True to overwrite the "
                    "directory" % to_path
                )

        # Retrieve number of test cases per class. Approximated to simplify
        # computing.
        sample_nb = int(sample_nb)
        sample_nb_per_class = [
            int(class_stat * sample_nb) for class_stat in self.dataset.stats
        ]

        # Iterate over the number of classes
        for index in range(len(self.dataset.classes)):
            # Retrieve class name and create destination directory
            class_name = self.dataset.classes[index]

            # Retrieve all test cases belonging to the class
            class_test_cases = [
                tc_path
                for tc_path in self.dataset.test_cases
                if tc_path.startswith(class_name)
            ]

            if shuffle:  # Shuffle dataset if required.
                random.shuffle(class_test_cases)

            # Truncate test cases list
            class_test_cases = class_test_cases[: sample_nb_per_class[index]]

            # Copy test cases to their destination
            for class_file in class_test_cases:
                orig_filepath = join(self.dataset.path, class_file)
                dest_filepath = join(to_path, class_file)

                copytree(orig_filepath, dest_filepath)

        LOGGER.debug("Dataset extracted in %dms" % (get_time() - _time))


class InverseDataset(DatasetProcessing):
    def execute(self, to_path, from_path, force=False):
        LOGGER.debug(
            "Extracting inverse dataset of %s from %s to %s (force=%d)"
            % (self.dataset.path, from_path, to_path, int(force))
        )
        _time = get_time()

        if exists(to_path):
            if force:
                rmtree(to_path)
            else:
                raise FileExistsError(
                    "%s already exists. Run with force=True to overwrite the "
                    "directory" % to_path
                )

        if not exists(from_path):
            raise FileNotFoundError("%s does not exists" % from_path)

        if not isdir(from_path):
            raise NotADirectoryError("%s is not a directory" % from_path)

        from_dataset = Dataset(from_path)
        inverse_test_cases = [
            test_case
            for test_case in self.dataset.test_cases
            if test_case not in from_dataset.test_cases
        ]

        for test_case in inverse_test_cases:
            orig_test_case = join(self.dataset.path, test_case)
            dest_test_case = join(to_path, test_case)

            copytree(orig_test_case, dest_test_case)

        LOGGER.debug("Dataset created in %dms" % (get_time() - _time))


class RightFixer(DatasetProcessingWithContainer):
    def configure_container(self):
        self.image_name = "right-fixer:latest"
        self.container_name = "right-fixer"
        self.volumes = {self.dataset.path: "/data"}

    def configure_command(self, command):
        self.command = join("/data", command)
        LOGGER.debug("Input command: %s." % self.command)

    def send_commands(self):
        LOGGER.debug("Right fixed for Neo4j DB.")
