from os import remove
from os.path import join, exists
from unittest import TestCase

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.processing.tokenizers.replace_variables import (
    ReplaceVariables,
)
from unittest.mock import patch, Mock


class TestReplaceVariablesProcessFile(TestCase):
    def _default_patch(self):
        patches_path = [
            "bugfinder.processing.tokenizers.replace_variables.move",
            "bugfinder.processing.tokenizers.replace_variables.LOGGER",
            "bugfinder.base.dataset.LOGGER",
        ]

        for patch_path in patches_path:
            patch_item = patch(patch_path)
            patch_item.start()
            self.addCleanup(patch_item.stop)

    def setUp(self) -> None:
        self._default_patch()
        dataset_path = "./tests/fixtures/dataset05"

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        dataset.path = dataset_path

        self.dataset_processing = ReplaceVariables(dataset)

        self.original_file = join(dataset_path, "class01/tc01", "item04.c")

    def tearDown(self) -> None:
        try:
            remove("%s.tmp" % self.original_file)
        except FileNotFoundError:
            pass

    def test_create_temp_file(self):
        self.dataset_processing.process_file(self.original_file)

        self.assertTrue(exists("%s.tmp" % self.original_file))

    def test_number_of_replaced_variables_not_zero(self):
        var_count = self.dataset_processing.process_file(self.original_file)

        self.assertNotEqual(var_count, 0)

    def test_number_of_replaced_variables_is_correct(self):
        var_count = self.dataset_processing.process_file(self.original_file)

        self.assertEqual(var_count, 42)

    def test_original_file_not_equal(self):
        self.dataset_processing.process_file(self.original_file)

        with open(self.original_file) as unprocessed_file:
            unprocessed_file.readlines()

        with open("%s.tmp" % self.original_file) as processed_file:
            processed_file.readlines()

        self.assertNotEqual(unprocessed_file, processed_file)
