from os import remove, listdir
from os.path import join, exists, splitext
from unittest import TestCase

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.processing.cleaning.replace_litterals import (
    ReplaceLitterals,
)
from unittest.mock import patch, call

from bugfinder import settings
from bugfinder.settings import ROOT_DIR
from tests import patch_paths


class TestReplaceLitteralsExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.processing.cleaning.replace_litterals.LOGGER",
                "bugfinder.base.dataset.LOGGER",
            ],
        )

        self.dataset_path = join(ROOT_DIR, "./tests/fixtures/dataset01")
        self.dataset = CodeWeaknessClassificationDataset(self.dataset_path)

        self.test_files = []
        for test_case in self.dataset.test_cases:
            test_case_path = join(self.dataset_path, test_case)
            for filename in listdir(test_case_path):
                if splitext(filename)[1] not in [".c", ".cpp", ".h", ".hpp"]:
                    continue

                self.test_files.append(join(test_case_path, filename))

    def tearDown(self) -> None:
        try:
            remove(join(self.dataset_path, settings.SUMMARY_FILE))
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    @patch(
        "bugfinder.processing.cleaning.replace_litterals.ReplaceLitterals.process_file"
    )
    def test_process_file_called_correctly(self, mock_process_file):
        mock_process_file.return_value = 0

        dataset_processing = ReplaceLitterals(self.dataset)
        dataset_processing.execute()

        mock_process_file_calls = [call(test_file) for test_file in self.test_files]
        mock_process_file.assert_has_calls(mock_process_file_calls, any_order=True)

    @patch(
        "bugfinder.processing.cleaning.replace_litterals.ReplaceLitterals.process_file"
    )
    def test_file_reprocessed_after_replacement(self, mock_process_file):
        processed_args = []

        def mock_process_file_fn(filepath):
            if filepath in processed_args:
                return 0
            else:
                processed_args.append(filepath)
                return 1

        mock_process_file.side_effect = mock_process_file_fn

        dataset_processing = ReplaceLitterals(self.dataset)
        dataset_processing.execute()

        self.assertEqual(mock_process_file.call_count, len(self.test_files) * 2)


class TestReplaceLitteralsProcessFile(TestCase):
    def _default_patch(self):
        patches_path = [
            "bugfinder.processing.cleaning.replace_litterals.move",
            "bugfinder.processing.cleaning.replace_litterals.LOGGER",
            "bugfinder.base.dataset.LOGGER",
        ]

        for patch_path in patches_path:
            patch_item = patch(patch_path)
            patch_item.start()
            self.addCleanup(patch_item.stop)

    def setUp(self) -> None:
        self._default_patch()
        self.dataset_path = "./tests/fixtures/dataset01"

        dataset = CodeWeaknessClassificationDataset(self.dataset_path)
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
