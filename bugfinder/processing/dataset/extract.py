from os.path import exists, join, basename

import random
from shutil import rmtree, copytree, copyfile

from bugfinder.base.processing import (
    AbstractProcessing,
)
from bugfinder.settings import LOGGER


class ExtractSampleDataset(AbstractProcessing):
    """Processing to create a subset of a given dataset."""

    def execute(self, to_path, sample_nb, shuffle=True, force=False):
        """Run the processing."""
        LOGGER.debug(
            "Extracting %d samples from dataset %s to %s (shuffle=%d, " "force=%d)...",
            sample_nb,
            self.dataset.path,
            to_path,
            int(shuffle),
            int(force),
        )

        if exists(to_path):
            if force:
                rmtree(to_path)
            else:
                raise FileExistsError(
                    f"{to_path} already exists. Run with force=True to overwrite the "
                    f"directory."
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

        copyfile(
            self.dataset.summary_filepath,
            join(to_path, basename(self.dataset.summary_filepath)),
        )

        LOGGER.info("Dataset extraction succeeded.")
