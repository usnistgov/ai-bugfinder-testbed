from os import remove
from os.path import join
from unittest import TestCase

import os

from bugfinder import settings
from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.processing.dataset.fix_rights import RightFixer
from tests import patch_paths


class TestRightFixer(TestCase):
    def tearDown(self) -> None:
        try:
            remove(join(self.input_dataset_path, settings.SUMMARY_FILE))
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    def test_right_are_fixed(self):
        patch_paths(
            self,
            [
                "bugfinder.processing.dataset.fix_rights.LOGGER",
                "bugfinder.base.processing.LOGGER",
                "bugfinder.base.dataset.LOGGER",
                "bugfinder.utils.containers.LOGGER",
            ],
        )

        self.input_dataset_path = "./tests/fixtures/dataset01"
        sample_uid = 20000
        sample_gid = 25000

        self.dataset = CodeWeaknessClassificationDataset(self.input_dataset_path)
        self.dataset_processing = RightFixer(self.dataset)

        self.dataset_processing.execute(
            command_args=". %s %s" % (sample_uid, sample_gid)
        )

        self.assertEqual(os.stat(self.input_dataset_path).st_uid, sample_uid)
        self.assertEqual(os.stat(self.input_dataset_path).st_gid, sample_gid)

        self.dataset_processing.execute(
            command_args=". %s %s" % (os.getuid(), os.getgid())
        )

        self.assertEqual(os.stat(self.input_dataset_path).st_uid, os.getuid())
        self.assertEqual(os.stat(self.input_dataset_path).st_gid, os.getgid())
