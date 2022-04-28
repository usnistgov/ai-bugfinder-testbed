from os.path import splitext

from bugfinder.processing.cleaning import AbstractFileRemover
from bugfinder.settings import LOGGER


class RemoveCppFiles(AbstractFileRemover):
    """Processing class to remove any C++ files that are not correctly parsed by
    Joern.
    """

    def execute(self):
        """Runs the processing"""
        LOGGER.debug("Removing CPP files from dataset at '%s'...", self.dataset.path)
        super().execute()
        LOGGER.info("CPP files successfully removed.")

    def match_file(self, filepath) -> bool:
        """Avoid processing header files"""
        return splitext(filepath)[1] == ".cpp"
