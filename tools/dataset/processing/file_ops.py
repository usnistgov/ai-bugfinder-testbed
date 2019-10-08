"""
"""
from os import remove, listdir
from os.path import basename, dirname, splitext
from shutil import rmtree

from tools.dataset.processing import DatasetFileProcessing
from tools.settings import LOGGER


class RemoveCppFiles(DatasetFileProcessing):
    def process_file(self, filepath):
        if basename(filepath).endswith(".cpp"):
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
