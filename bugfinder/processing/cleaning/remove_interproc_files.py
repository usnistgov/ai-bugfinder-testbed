from os.path import basename, splitext

import re

from bugfinder.processing.cleaning import AbstractFileRemover
from bugfinder.settings import LOGGER


class RemoveInterprocFiles(AbstractFileRemover):
    """Processing to remove any interprocedural test case."""

    def execute(self):
        """Runs the processing"""
        LOGGER.debug(
            "Removing interprocedural test cases from dataset at '%s'...",
            self.dataset.path,
        )
        super().execute()
        LOGGER.info("Interprocedural test cases successfully removed.")

    def match_file(self, filepath) -> bool:
        """Avoid processing header files"""
        return (
            splitext(filepath)[1] != ".h"
            and len(re.findall(r"[0-9]+[a-e]\.c$", basename(filepath))) > 0
        )
