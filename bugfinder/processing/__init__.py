from abc import abstractmethod
from os.path import splitext

from bugfinder.base.processing.files import AbstractFileProcessing


class AbstractCppFileProcessing(AbstractFileProcessing):
    """Abstract file processing matching C and C++ files only"""

    def match_file(self, filepath) -> bool:
        return splitext(filepath)[1] in [".c", ".cpp", ".h", ".hpp"]

    @abstractmethod
    def process_file(self, filepath):  # pragma: no cover
        """Process a file with the given `filepath`. Needs to be implemented by the
        subclass.

        Args:
            filepath:
        """
        raise NotImplementedError("Method 'process_file' not implemented.")
