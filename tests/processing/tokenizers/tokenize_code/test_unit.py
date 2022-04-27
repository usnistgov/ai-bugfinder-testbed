from os import remove
from os.path import join, exists
from unittest import TestCase
from unittest.mock import patch, Mock

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.processing.tokenizers.tokenize_code import (
    TokenizeCode,
)


class TestTokenizeProcessFile(TestCase):
    def _default_patch(self):
        patches_path = [
            "bugfinder.processing.tokenizers.tokenize_code.move",
            "bugfinder.processing.tokenizers.tokenize_code.LOGGER",
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

        self.dataset_processing = TokenizeCode(dataset)

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
