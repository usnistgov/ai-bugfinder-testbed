from unittest import TestCase

from bugfinder.processing.joern.v031 import JoernProcessing
from tests import patch_paths


class TestJoernDatasetProcessingConfigureContainer(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.processing.joern.AbstractJoernProcessing.configure_container",
                "bugfinder.processing.joern.v031.LOGGER",
                "bugfinder.base.processing.LOGGER",
            ],
        )

        self.dataset_processing = JoernProcessing(None)

    def test_image_name_is_correct(self):
        expected_image_name = "joern-lite:0.3.1"

        self.dataset_processing.configure_container()

        self.assertEqual(self.dataset_processing.image_name, expected_image_name)

    def test_container_name_is_correct(self):
        expected_container_name = "joern031"

        self.dataset_processing.configure_container()

        self.assertEqual(
            self.dataset_processing.container_name, expected_container_name
        )
