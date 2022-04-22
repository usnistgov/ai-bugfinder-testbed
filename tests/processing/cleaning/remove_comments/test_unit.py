from os import remove
from os.path import join, exists
from unittest import TestCase

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.processing.cleaning.remove_comments import (
    RemoveComments,
)
from unittest.mock import patch, Mock


class TestRemoveCommentsProcessFile(TestCase):
    def _default_patch(self):
        patches_path = [
            "bugfinder.processing.cleaning.remove_comments.move",
            "bugfinder.processing.cleaning.LOGGER",
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
