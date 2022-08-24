from unittest import TestCase

from bugfinder.processing.joern import AbstractJoernProcessing
from tests import patch_paths


class MockDataset(object):
    def __init__(self):
        self.path = "mock_path"


class MockJoernDatasetProcessing(AbstractJoernProcessing):
    def send_commands(self):
        pass


class TestJoernDefaultDatasetProcessingConfigureContainer(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            ["bugfinder.base.processing.LOGGER"],
        )
        mock_dataset = MockDataset()
        self.dataset_processing = MockJoernDatasetProcessing(mock_dataset)

    def test_container_volume_is_correct(self):
        expected_container_volume = {"mock_path": "/code"}

        self.dataset_processing.configure_container()

        self.assertDictEqual(self.dataset_processing.volumes, expected_container_volume)

    def test_detach_is_false(self):
        self.dataset_processing.configure_container()

        self.assertFalse(self.dataset_processing.detach)
