""" Abstract classes for creating processing steps.
"""

from abc import ABC, abstractmethod
from enum import Enum

from bugfinder.settings import LOGGER


class ProcessingCategory(Enum):
    """Possible types of processing classes"""

    __NONE__ = "__null__"
    PROCESSING = "processing"
    EXTRACTION = "feature_extraction"
    REDUCTION = "feature_reduction"
    TRAINING = "training"

    def __str__(self):
        return str(self.value)


class ProcessingDeprecation:
    """Add a deprecation notice to a given class"""

    def __init__(self, notice, deprecated_in=None, removed_in=None):
        self.notice = notice
        self.deprecated_in = deprecated_in
        self.removed_in = removed_in


class AbstractProcessing(ABC):
    """Abstract class for all dataset processing."""

    def __init__(self, dataset, deprecation_warning=None):
        """Class constructor

        Args:
            dataset:
            deprecation_warning:
        """

        self.metadata = {"category": str(ProcessingCategory.PROCESSING)}
        self.processing_stats = {}
        self.dataset = dataset

        if deprecation_warning:
            deprecation_notice = "%s processing class deprecated" % str(
                self.__class__.__name__
            )

            if deprecation_warning.deprecated_in:
                deprecation_notice += " since %s" % deprecation_warning.deprecated_in

            if deprecation_warning.removed_in:
                if deprecation_warning.deprecated_in:
                    deprecation_notice += ","

                deprecation_notice += (
                    " will be removed in %s" % deprecation_warning.removed_in
                )

            deprecation_notice += ". Notice: %s" % deprecation_warning.notice
            LOGGER.warning(deprecation_notice)

    @abstractmethod
    def execute(self, *args, **kwargs):  # pragma: no cover
        """Execute the processing. Needs to be implemented by the subclass.

        Args:
            args:
            kwargs:
        """
        raise NotImplementedError("Method 'execute' not implemented.")
