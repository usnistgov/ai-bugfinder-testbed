from os import remove
from os.path import join, exists
from unittest import TestCase

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.processing.cleaning.remove_main_function import (
    RemoveMainFunction,
)
from unittest.mock import patch, Mock

from tests import patch_paths


class TestRemoveMainFunctionExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.processing.cleaning.remove_main_function.LOGGER",
                "bugfinder.base.dataset.LOGGER",
            ],
        )

    @patch("bugfinder.base.processing.files.AbstractFileProcessing.execute")
    def test_super_execute_called(self, mock_super_execute):
        dataset_path = "./tests/fixtures/dataset01"

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        dataset.path = dataset_path
        self.dataset_processing = RemoveMainFunction(dataset)

        self.dataset_processing.execute()
        self.assertTrue(mock_super_execute.called)


class TestRemoveMainFunctionProcessFile(TestCase):
    def _default_patch(self):
        patches_path = [
            "bugfinder.processing.cleaning.remove_main_function.move",
            "bugfinder.processing.cleaning.remove_main_function.LOGGER",
            "bugfinder.base.dataset.LOGGER",
        ]

        for patch_path in patches_path:
            patch_item = patch(patch_path)
            patch_item.start()
            self.addCleanup(patch_item.stop)

    def setUp(self) -> None:
        self._default_patch()
        dataset_path = "./tests/fixtures/dataset01"

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        dataset.path = dataset_path
        self.dataset_processing = RemoveMainFunction(dataset)

        self.file_with_main = join(dataset_path, "class02/tc01", "item.c")
        self.clean_file = join(dataset_path, "class02/tc03", "item.c")

    def tearDown(self) -> None:
        try:
            remove("%s.tmp" % self.file_with_main)
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

        try:
            remove("%s.tmp" % self.clean_file)
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_main_is_removed(self):
        self.dataset_processing.process_file(self.file_with_main)

        with open("%s.tmp" % self.file_with_main) as processed_file:
            self.assertEqual(len(processed_file.readlines()), 0)

    def test_main_create_temp_file(self):
        self.dataset_processing.process_file(self.file_with_main)

        self.assertTrue(exists("%s.tmp" % self.file_with_main))

    def test_no_main_creates_identical_file(self):
        self.dataset_processing.process_file(self.clean_file)

        with open(self.clean_file) as orig_file:
            orig_lines = orig_file.readlines()

        with open("%s.tmp" % self.clean_file) as mod_file:
            mod_lines = mod_file.readlines()

        self.assertEqual(orig_lines, mod_lines)
