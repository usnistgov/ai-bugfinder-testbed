from os import remove, listdir
from os.path import join, exists, splitext
from unittest import TestCase
from unittest.mock import patch, call, Mock

from bugfinder import settings
from bugfinder.dataset import CodeWeaknessClassificationDataset
from bugfinder.dataset.processing.content_ops import (
    ReplaceLitterals,
    RemoveMainFunction,
)
from bugfinder.settings import ROOT_DIR
from tests import patch_paths
from bugfinder.dataset.processing.word2vec_ops import (
    RemoveComments,
    ReplaceFunctions,
    ReplaceVariables,
)
from bugfinder.dataset.processing.token_ops import (
    TokenizeText,
)


class TestReplaceLitteralsExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.dataset.processing.content_ops.LOGGER",
                "bugfinder.dataset.LOGGER",
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

    @patch("bugfinder.dataset.processing.content_ops.ReplaceLitterals.process_file")
    def test_process_file_called_correctly(self, mock_process_file):
        mock_process_file.return_value = 0

        dataset_processing = ReplaceLitterals(self.dataset)
        dataset_processing.execute()

        mock_process_file_calls = [call(test_file) for test_file in self.test_files]
        mock_process_file.assert_has_calls(mock_process_file_calls, any_order=True)

    @patch("bugfinder.dataset.processing.content_ops.ReplaceLitterals.process_file")
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


class TestRemoveMainFunctionExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.dataset.processing.content_ops.LOGGER",
                "bugfinder.dataset.LOGGER",
            ],
        )

    @patch("bugfinder.dataset.processing.DatasetFileProcessing.execute")
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

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        dataset.path = dataset_path
        self.dataset_processing = RemoveMainFunction(dataset)

        self.file_with_main = join(dataset_path, "class02/tc01", "item.c")
        self.clean_file = join(dataset_path, "class02/tc03", "item.c")
        self.invalid_file = join(dataset_path, "features", "features.csv")

    def tearDown(self) -> None:
        try:
            remove("%s.tmp" % self.file_with_main)
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

        try:
            remove("%s.tmp" % self.clean_file)
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_invalid_file_not_processed(self):
        self.dataset_processing.process_file(self.invalid_file)
        self.assertFalse(exists(f"{self.invalid_file}.tmp"))

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


class TestRemoveCommentsProcessFile(TestCase):
    def _default_patch(self):
        patches_path = [
            "bugfinder.dataset.processing.word2vec_ops.move",
            "bugfinder.dataset.processing.word2vec_ops.LOGGER",
            "bugfinder.dataset.LOGGER",
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

        self.dataset_processing = RemoveComments(dataset)

        self.original_file = join(dataset_path, "class01/tc01", "item04.c")

    def tearDown(self) -> None:
        try:
            remove("%s.tmp" % self.original_file)
        except FileNotFoundError:
            pass

    def test_create_temp_file(self):
        self.dataset_processing.process_file(self.original_file)

        self.assertTrue(exists("%s.tmp" % self.original_file))

    def test_original_file_not_equal(self):
        self.dataset_processing.process_file(self.original_file)

        with open(self.original_file) as unprocessed_file:
            unprocessed_file.readlines()

        with open("%s.tmp" % self.original_file) as processed_file:
            processed_file.readlines()

        self.assertNotEqual(unprocessed_file, processed_file)


class TestReplaceFunctionsProcessFile(TestCase):
    def _default_patch(self):
        patches_path = [
            "bugfinder.dataset.processing.word2vec_ops.move",
            "bugfinder.dataset.processing.word2vec_ops.LOGGER",
            "bugfinder.dataset.LOGGER",
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

        self.dataset_processing = ReplaceFunctions(dataset)

        self.original_file = join(dataset_path, "class01/tc01", "item04.c")

    def tearDown(self) -> None:
        try:
            remove("%s.tmp" % self.original_file)
        except FileNotFoundError:
            pass

    def test_create_temp_file(self):
        self.dataset_processing.process_file(self.original_file)

        self.assertTrue(exists("%s.tmp" % self.original_file))

    def test_number_of_replaced_functions_not_zero(self):
        func_count = self.dataset_processing.process_file(self.original_file)

        self.assertNotEqual(func_count, 0)

    def test_number_of_functions_replaced_is_correct(self):
        func_count = self.dataset_processing.process_file(self.original_file)

        self.assertEqual(func_count, 5)

    def test_original_file_not_equal(self):
        self.dataset_processing.process_file(self.original_file)

        with open(self.original_file) as unprocessed_file:
            unprocessed_file.readlines()

        with open("%s.tmp" % self.original_file) as processed_file:
            processed_file.readlines()

        self.assertNotEqual(unprocessed_file, processed_file)


class TestReplaceVariablesProcessFile(TestCase):
    def _default_patch(self):
        patches_path = [
            "bugfinder.dataset.processing.word2vec_ops.move",
            "bugfinder.dataset.processing.word2vec_ops.LOGGER",
            "bugfinder.dataset.LOGGER",
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


class TestTokenizeProcessFile(TestCase):
    def _default_patch(self):
        patches_path = [
            "bugfinder.dataset.processing.token_ops.move",
            "bugfinder.dataset.processing.token_ops.LOGGER",
            "bugfinder.dataset.LOGGER",
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

        self.dataset_processing = TokenizeText(dataset)

        self.original_file = join(dataset_path, "class01/tc02", "item.c")

    def tearDown(self) -> None:
        try:
            remove("%s.tmp" % self.original_file)
        except FileNotFoundError:
            pass

    def test_create_temp_file(self):
        self.dataset_processing.process_file(self.original_file)

        self.assertTrue(exists("%s.tmp" % self.original_file))

    def test_regex_construction_single_char(self):
        ops = ["a", "b", "c", "!", "="]
        regs = "(a)|(b)|(c)|(!)|(=)"

        self.assertEqual(self.dataset_processing.to_regex(ops), regs)

    def test_regex_construction_double_char(self):
        ops = ["ab", "cd", "||", "!=", "|="]
        regs = "(ab)|(cd)|(\\|\\|)|(!=)|(\\|=)"

        self.assertEqual(self.dataset_processing.to_regex(ops), regs)

    def test_regex_construction_triple_char(self):
        ops = ["abc", "|=<", ">>="]
        regs = "(abc)|(\\|=<)|(>>=)"

        self.assertEqual(self.dataset_processing.to_regex(ops), regs)

    def test_tokenize_content(self):
        self.dataset_processing.process_file(self.original_file)

        with open("%s.tmp" % self.original_file) as processed_file:
            lines = processed_file.readlines()

            for line in lines:
                self.assertEqual(len(line.split()), 1)
