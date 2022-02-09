"""
"""
from os import remove, listdir
from os.path import basename, dirname, splitext, join

import re
from abc import abstractmethod
from shutil import rmtree

from bugfinder.dataset.processing import DatasetFileProcessing
from bugfinder.settings import LOGGER


class DatasetFileRemover(DatasetFileProcessing):
    def _remove_file(self, filepath):
        LOGGER.debug("Removing file '%s'...", basename(filepath))
        remove(filepath)

        # Inspect parent directory to check for emptyness
        dirpath = dirname(filepath)
        for filename in listdir(dirpath):
            dir_filepath = join(dirpath, filename)
            if self.is_needed_file(dir_filepath):
                return

        # If directory is empty (or only contains .h files) it is deleted
        # and the test case is removes from the dataset.
        LOGGER.debug("Removing empty directory at '%s'...", dirpath)
        rmtree(dirpath)

    @abstractmethod
    def is_needed_file(self, filepath):
        raise NotImplementedError("Method 'is_needed_file' not implemented.")

    @abstractmethod
    def process_file(self, filepath):
        raise NotImplementedError("Method 'process_file' not implemented")


class RemoveCppFiles(DatasetFileRemover):
    def execute(self):
        LOGGER.debug("Removing CPP files from dataset at '%s'...", self.dataset.path)
        super().execute()
        LOGGER.info("CPP files successfully removed.")

    def is_needed_file(self, filepath):
        return splitext(filepath)[1] != ".h"

    def process_file(self, filepath):
        if basename(filepath).endswith(".cpp"):
            self._remove_file(filepath)


class RemoveInterproceduralTestCases(DatasetFileRemover):
    def execute(self):
        LOGGER.debug(
            "Removing interprocedural test cases from dataset at '%s'...",
            self.dataset.path,
        )
        super().execute()
        LOGGER.info("Interprocedural test cases successfully removed.")

    def is_needed_file(self, filepath):
        return splitext(filepath)[1] != ".h"

    def process_file(self, filepath):
        if len(re.findall(r"[0-9]+[a-e]\.c$", basename(filepath))) > 0:
            self._remove_file(filepath)
