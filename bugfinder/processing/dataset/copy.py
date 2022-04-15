from os.path import exists

import os
from shutil import rmtree, copytree

from bugfinder.base.dataset import (
    CodeWeaknessClassificationDataset as Dataset,
    ProcessingCategory,
)
from bugfinder.base.processing import (
    AbstractProcessing,
)
from bugfinder.processing.dataset.fix_rights import RightFixer
from bugfinder.settings import LOGGER


class CopyDataset(AbstractProcessing):
    """Processing class to copy entire datasets."""

    def __init__(self, dataset):
        super().__init__(dataset)

        self.metadata["category"] = str(ProcessingCategory.__NONE__)

    def execute(self, to_path, force=False):
        """Run the processing"""
        LOGGER.debug(
            "Copying dataset at %s to %s (force=%d)...",
            self.dataset.path,
            to_path,
            int(force),
        )

        # Fix rights of the original dataset
        orig_dataset = Dataset(self.dataset.path, silent=True)
        orig_dataset.queue_operation(
            RightFixer,
            {"command_args": ". %s %s" % (os.getuid(), os.getgid())},
        )
        orig_dataset.process(silent=True)

        # Cleanup directory if it exists or remove
        if exists(to_path):
            if force:
                try:
                    dest_dataset = Dataset(to_path, silent=True)
                    dest_dataset.queue_operation(
                        RightFixer,
                        {"command_args": ". %s %s" % (os.getuid(), os.getgid())},
                    )
                    dest_dataset.process(silent=True)
                finally:
                    rmtree(to_path)
            else:
                raise FileExistsError(
                    f"{to_path} already exists. Run with force=True to overwrite the "
                    f"existing directory."
                )

        copytree(self.dataset.path, to_path)
        LOGGER.info("Dataset copy succeeded.")
