from os import remove, listdir
from os.path import join, exists, splitext
from unittest import TestCase
from unittest.mock import patch, call, Mock

from bugfinder import settings
from bugfinder.dataset import CWEClassificationDataset
from bugfinder.dataset.processing.content_ops import (
    ReplaceLitterals,
    RemoveMainFunction,
)


class TestReplaceLitteralsExecute(TestCase):
    def tearDown(self) -> None:
        try:
            remove(join(self.dataset_path, settings.SUMMARY_FILE))
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    @patch("bugfinder.dataset.processing.content_ops.LOGGER")
    @patch("bugfinder.dataset.LOGGER")
    @patch("bugfinder.dataset.processing.content_ops.ReplaceLitterals.process_file")
    def test_process_file_called_correctly(
        self, mock_process_file, mock_processing_logger, mock_dataset_logger
    ):
        mock_process_file.return_value = 0
        mock_processing_logger.return_value = None
        mock_dataset_logger.return_value = None
        self.dataset_path = "./tests/fixtures/dataset01"

        dataset = CWEClassificationDataset(self.dataset_path)
        dataset_processing = ReplaceLitterals(dataset)

        dataset_processing.execute()

        test_files = []
        for test_case in dataset.test_cases:
            test_case_path = join(self.dataset_path, test_case)
            for filename in listdir(test_case_path):
                if splitext(filename)[1] in [".c", ".cpp", ".h", ".hpp"]:
                    test_files.append(join(test_case_path, filename))

        mock_process_file_calls = [call(test_file) for test_file in test_files]
        mock_process_file.assert_has_calls(mock_process_file_calls, any_order=True)


class TestReplaceLitteralsProcessFile(TestCase):
    def _default_patch(self):
        patches_path = [
            "bugfinder.dataset.processing.content_ops.move",
            "bugfinder.dataset.processing.content_ops.LOGGER",
            "bugfinder.dataset.LOGGER",
        ]

        for patch_path in patches_path:
            patch_item = patch(patch_path)
            patch_item.start()
            self.addCleanup(patch_item.stop)

    def setUp(self) -> None:
        self._default_patch()
        self.dataset_path = "./tests/fixtures/dataset01"

        dataset = CWEClassificationDataset(self.dataset_path)
        self.dataset_processing = ReplaceLitterals(dataset)

        self.file_with_litterals = join(self.dataset_path, "class01/tc02", "item.c")
        self.clean_file = join(self.dataset_path, "class01/tc03", "item.c")

    def tearDown(self) -> None:
        try:
            remove(join(self.dataset_path, settings.SUMMARY_FILE))
            remove("%s.tmp" % self.file_with_litterals)
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_matching_regexp_increase_repl_count(self):
        repl_count = self.dataset_processing.process_file(self.file_with_litterals)

        self.assertNotEqual(repl_count, 0)

    def test_repl_count_not_zero_creates_new_file(self):
        self.dataset_processing.process_file(self.file_with_litterals)

        self.assertTrue(exists("%s.tmp" % self.file_with_litterals))

    def test_default_repl_count_is_zero(self):
        repl_count = self.dataset_processing.process_file(self.clean_file)

        self.assertEqual(repl_count, 0)

    def test_repl_count_is_correct(self):
        repl_count = self.dataset_processing.process_file(self.file_with_litterals)

        self.assertEqual(repl_count, 2)


class TestRemoveMainFunctionProcessFile(TestCase):
    def _default_patch(self):
        patches_path = [
            "bugfinder.dataset.processing.content_ops.move",
            "bugfinder.dataset.processing.content_ops.LOGGER",
            "bugfinder.dataset.LOGGER",
        ]

        for patch_path in patches_path:
            patch_item = patch(patch_path)
            patch_item.start()
            self.addCleanup(patch_item.stop)

    def setUp(self) -> None:
        self._default_patch()
        dataset_path = "./tests/fixtures/dataset01"

        dataset = Mock(spec=CWEClassificationDataset)
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
