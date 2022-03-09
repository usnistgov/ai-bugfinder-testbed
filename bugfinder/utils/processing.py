""" Utilities for processing classes
"""
from inspect import isclass

from bugfinder.dataset.processing import DatasetProcessing
from bugfinder.settings import LOGGER
from bugfinder.utils.statistics import get_time, display_time


def is_operation_valid(processing_operation):
    """Ensure a processing operation is valid"""
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


def is_processing_stack_valid(operation_list, silent=False):
    """Check validity of a processing stack (list of processing operation)"""
    logger_log_func = LOGGER.debug if silent else LOGGER.info
    _time = get_time()

    processing_operation_index = 1
    for processing_operation in operation_list:
        try:
            LOGGER.debug(
                "Checking operation %d/%d (%s)...",
                processing_operation_index,
                len(operation_list),
                str(processing_operation),
            )
            is_operation_valid(processing_operation)
        except AssertionError:
            LOGGER.error("Processing operation is invalid.", exc_info=True)
            return False

        processing_operation_index += 1

    logger_log_func(
        "Operation queue validated in %s.", display_time(get_time() - _time)
    )
    return True
