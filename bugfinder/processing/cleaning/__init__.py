from os import remove, listdir
from os.path import basename, dirname

from abc import abstractmethod
from shutil import rmtree

from bugfinder.base.processing.files import AbstractFileProcessing
from bugfinder.settings import LOGGER


class AbstractFileRemover(AbstractFileProcessing):
    """Processing class to remove files based on specific conditions."""

    @abstractmethod
    def match_file(self, filepath) -> bool:
        """Abstract method to determine wether a file should be ignored by the
        processing.
        """
        raise NotImplementedError("Method 'match_file' not implemented.")

    def process_file(self, filepath):
        """Remove file."""
        LOGGER.debug("Removing file '%s'...", basename(filepath))
        remove(filepath)

        # Inspect parent directory to check for emptyness
        dirpath = dirname(filepath)
        if len(listdir(dirpath)) > 0:
            return

        # If directory is empty (or only contains .h files) it is deleted
        # and the test case is removes from the dataset.
        LOGGER.debug("Removing empty directory at '%s'...", dirpath)
        rmtree(dirpath)
