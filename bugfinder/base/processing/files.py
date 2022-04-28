""" Abstract classes for creating processing steps.
"""
from os import listdir
from os.path import join

from abc import abstractmethod

from bugfinder.base.processing import AbstractProcessing


class AbstractFileProcessing(AbstractProcessing):
    """Abstract processing class for handling file changes."""

    def execute(self):
        """Execute the 'process_file' method on files where 'match_file' returns
        True.
        """
        exec_retcode_list = []

        for test_case in self.dataset.test_cases:
            exec_retcode_list += [
                self.process_file(join(self.dataset.path, test_case, filepath))
                for filepath in listdir(join(self.dataset.path, test_case))
                if self.match_file(filepath)
            ]

        self.dataset.rebuild_index()
        return exec_retcode_list

    @abstractmethod
    def match_file(self, filepath) -> bool:  # pragma: no cover
        """ """
        raise NotImplementedError("Method 'match_file' not implemented.")

    @abstractmethod
    def process_file(self, filepath):  # pragma: no cover
        """Process a file with the given `filepath`. Needs to be implemented by the
        subclass.

        Args:
            filepath:
        """
        raise NotImplementedError("Method 'process_file' not implemented.")
