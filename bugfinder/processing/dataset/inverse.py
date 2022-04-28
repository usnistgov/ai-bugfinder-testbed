from os.path import exists, join, isdir, basename

from shutil import rmtree, copytree, copyfile

from bugfinder.base.dataset import CodeWeaknessClassificationDataset as Dataset
from bugfinder.base.processing import (
    AbstractProcessing,
)
from bugfinder.settings import LOGGER
from bugfinder.utils.statistics import get_time


class InverseDataset(AbstractProcessing):
    """Processing class to create a subset of a dataset by including test cases that
    are not present in a given subset.
    """

    def execute(self, to_path, from_path, force=False):
        """Run the processing"""
        LOGGER.debug(
            "Extracting inverse dataset of %s from %s to %s (force=%d)",
            self.dataset.path,
            from_path,
            to_path,
            int(force),
        )
        _time = get_time()

        if exists(to_path):
            if force:
                rmtree(to_path)
            else:
                raise FileExistsError(
                    f"{to_path} already exists. Run with force=True to overwrite the "
                    f"existing directory."
                )

        if not exists(from_path):
            raise FileNotFoundError(f"{from_path} does not exists.")

        if not isdir(from_path):
            raise NotADirectoryError(f"{from_path} is not a directory.")

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

        copyfile(
            self.dataset.summary_filepath,
            join(to_path, basename(self.dataset.summary_filepath)),
        )

        LOGGER.info("Inverse dataset creation succeeded.")
