""" Utilities for processing classes
"""
import unittest

from bugfinder.utils.processing import is_operation_valid, is_processing_stack_valid
from tests import MockDatasetProcessing, patch_paths


class TestIsOperationValid(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.operation_class = MockDatasetProcessing

    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.utils.processing.LOGGER"])

    def test_valid_dict_operation(self):
        operation = {"class": self.operation_class, "args": {}}

        is_operation_valid(operation)

    def test_invalid_subclass_in_dict_operation(self):
        operation = {"class": object, "args": {}}

        with self.assertRaises(AssertionError):
            is_operation_valid(operation)

    def test_invalid_args_type_in_dict_operation(self):
        operation = {"class": self.operation_class, "args": []}

        with self.assertRaises(AssertionError):
            is_operation_valid(operation)

    def test_missing_class_key_in_dict_operation(self):
        operation = {"args": {}}

        with self.assertRaises(AssertionError):
            is_operation_valid(operation)

    def test_missing_args_key_in_dict_operation(self):
        operation = {"class": self.operation_class}

        with self.assertRaises(AssertionError):
            is_operation_valid(operation)

    def test_valid_class_operation(self):
        is_operation_valid(self.operation_class)

    def test_invalid_class_operation(self):
        with self.assertRaises(AssertionError):
            is_operation_valid(object)


class TestIsProcessingStackValid(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.operation_class = MockDatasetProcessing

    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.utils.processing.LOGGER"])

    def test_valid_stack(self):
        operation_list = [
            {"class": self.operation_class, "args": {}},
            self.operation_class,
        ]

        self.assertTrue(is_processing_stack_valid(operation_list))

    def test_invalid_dict_operation_stack(self):
        operation_list = [{}, self.operation_class]

        self.assertFalse(is_processing_stack_valid(operation_list))

    def test_invalid_class_operation_stack(self):
        operation_list = [{"class": self.operation_class, "args": {}}, object]

        self.assertFalse(is_processing_stack_valid(operation_list))
