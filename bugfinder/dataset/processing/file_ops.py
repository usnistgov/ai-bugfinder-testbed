"""
"""
import re
from abc import abstractmethod
from os import remove, listdir
from os.path import basename, dirname, splitext, join
from shutil import rmtree

from bugfinder.dataset.processing import DatasetFileProcessing
from bugfinder.settings import LOGGER


class DatasetFileRemover(DatasetFileProcessing):
    def _remove_file(self, filepath):
        LOGGER.debug("Removing %s..." % basename(filepath))
        remove(filepath)

        # Inspect parent directory to check for emptyness
        dirpath = dirname(filepath)
        for filename in listdir(dirpath):
            dir_filepath = join(dirpath, filename)
            if self.is_needed_file(dir_filepath):
                return

        # If directory is empty (or only contains .h files) it is deleted
        # and the test case is removes from the dataset.
        LOGGER.debug("Removing %s (directory is empty)..." % dirpath)
        rmtree(dirpath)

    @abstractmethod
    def is_needed_file(self, filepath):
        raise NotImplementedError("method not implemented")

    @abstractmethod
    def process_file(self, filepath):
        raise NotImplementedError("method not implemented")


class RemoveCppFiles(DatasetFileRemover):
    def is_needed_file(self, filepath):
        return splitext(filepath)[1] != ".h"

    def process_file(self, filepath):
        if basename(filepath).endswith(".cpp"):
            self._remove_file(filepath)


class RemoveInterproceduralTestCases(DatasetFileRemover):
    def is_needed_file(self, filepath):
        return splitext(filepath)[1] != ".h"

    def process_file(self, filepath):
        if len(re.findall(r"[0-9]+[a-e]\.c$", basename(filepath))) > 0:
            self._remove_file(filepath)