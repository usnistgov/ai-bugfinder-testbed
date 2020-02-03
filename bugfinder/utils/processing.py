""" Utilities for processing classes
"""
from inspect import isclass

from tools.dataset.processing import DatasetProcessing


def is_operation_valid(processing_operation):
    if isinstance(processing_operation, dict):
        assert "class" in processing_operation.keys() and \
               "args" in processing_operation.keys()
        assert issubclass(processing_operation["class"], DatasetProcessing)
        assert isinstance(processing_operation["args"], dict)
    else:  # operation should be a sublass of dataset operation
        assert isclass(processing_operation)
        assert issubclass(processing_operation, DatasetProcessing)


def is_processsing_stack_valid(operation_list):
    for processing_operation in operation_list:
        try:
            is_operation_valid(processing_operation)
        except AssertionError:
            return False

    return True