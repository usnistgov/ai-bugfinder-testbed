"""
"""
from abc import abstractmethod
from os import remove, listdir
from os.path import basename, dirname, splitext
from shutil import rmtree

from tools.dataset.processing import DatasetFileProcessing
from tools.settings import LOGGER
import re


class DatasetFileRemover(DatasetFileProcessing):
    @staticmethod
    def _remove_file(filepath):
        LOGGER.debug("Removing %s..." % basename(filepath))
        remove(filepath)

        # Inspect directory to check for emptyness
        dirpath = dirname(filepath)
        for filename in listdir(dirpath):
            if splitext(filename) != ".h":
                return

        # If directory is empty (or only contains .h files) it is deleted
        # and the test case is removes from the dataset.
        LOGGER.debug("Removing %s (directory is empty)..." % dirpath)
        rmtree(dirpath)

    @abstractmethod
    def process_file(self, filepath):
        raise NotImplementedError("method not implemented")


class RemoveCppFiles(DatasetFileRemover):
    def process_file(self, filepath):
        if basename(filepath).endswith(".cpp"):
            self._remove_file(filepath)


class RemoveInterproceduralTestCases(DatasetFileRemover):
    def process_file(self, filepath):
        if len(re.findall(r"[0-9]+[a-e]\.c$", basename(filepath))) > 0:
            self._remove_file(filepath)
