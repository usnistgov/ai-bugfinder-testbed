""" Utilities for processing classes
"""
from inspect import isclass

from bugfinder.dataset.processing import DatasetProcessing
from bugfinder.settings import LOGGER


def is_operation_valid(processing_operation):
    if isinstance(processing_operation, dict):
        assert (
            "class" in processing_operation.keys()
            and "args" in processing_operation.keys()
        )
        assert issubclass(processing_operation["class"], DatasetProcessing)
        assert isinstance(processing_operation["args"], dict)
    else:  # operation should be a sublass of dataset operation
        assert isclass(processing_operation)
        assert issubclass(processing_operation, DatasetProcessing)


def is_processing_stack_valid(operation_list):
    processing_operation_index = 1
    for processing_operation in operation_list:
        try:
            LOGGER.debug(
                "Checking operation %d/%d (%s)..."
                % (
                    processing_operation_index,
                    len(operation_list),
                    str(processing_operation),
                )
            )
            is_operation_valid(processing_operation)
        except AssertionError:
            LOGGER.error("Processing operation is invalid", exc_info=True)
            return False

        processing_operation_index += 1

    return True
