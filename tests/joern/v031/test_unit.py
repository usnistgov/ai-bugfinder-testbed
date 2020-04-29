from unittest import TestCase

from bugfinder.joern.v031 import JoernDatasetProcessing
from tests import patch_paths


class TestJoernDatasetProcessingConfigureContainer(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, ["bugfinder.joern.JoernDefaultDatasetProcessing.configure_container"]
        )

        self.dataset_processing = JoernDatasetProcessing(None)

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
