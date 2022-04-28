from unittest import TestCase

import re
from unittest.mock import Mock, patch

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.base.processing.containers import AbstractContainerProcessing


class MockAbstractContainerProcessing(AbstractContainerProcessing):
    def configure_container(self):
        self.image_name = "mock:latest"
        self.container_name = "mock-container"
        self.container_ports = ["1111"]
        self.machine_ports = ["1111"]
        self.volumes = {"host_vol": "guest_vol"}
        self.environment = {"key0": "value0"}
        self.command = "mock_command"
        self.detach = self.configure_detach()

    @staticmethod
    def configure_detach():
        return False

    def configure_command(self, command):
        self.command = "%s_%s" % (self.command, command)

    def send_commands(self):
        return "%s_sent" % self.command


class TestDatasetProcessingWithContainerInit(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        mock_dataset = Mock(spec=CodeWeaknessClassificationDataset)
        cls.mock_dataset_processing = MockAbstractContainerProcessing(mock_dataset)

    def test_default_image_name(self):
        self.assertEqual(self.mock_dataset_processing.image_name, "")

    def test_default_container_name(self):
        self.assertEqual(self.mock_dataset_processing.container_name, "")

    def test_container_ports(self):
        self.assertEqual(self.mock_dataset_processing.container_ports, None)

    def test_machine_ports(self):
        self.assertEqual(self.mock_dataset_processing.machine_ports, None)

    def test_default_volumes(self):
        self.assertEqual(self.mock_dataset_processing.volumes, None)

    def test_default_environment(self):
        self.assertEqual(self.mock_dataset_processing.environment, None)

    def test_default_command(self):
        self.assertEqual(self.mock_dataset_processing.command, None)

    def test_default_detach(self):
        self.assertEqual(self.mock_dataset_processing.detach, True)

    def test_default_container(self):
        self.assertEqual(self.mock_dataset_processing.container, None)


class TestDatasetProcessingWithContainerExecute(TestCase):
    def setUp(self) -> None:
        mock_dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.mock_dataset_processing = MockAbstractContainerProcessing(mock_dataset)
        self.mock_dataset_processing.configure_container()

        patch_logger = patch("bugfinder.base.processing.containers.LOGGER")
        patch_start_container = patch(
            "bugfinder.base.processing.containers.start_container"
        )
        patch_stop_container = patch(
            "bugfinder.base.processing.containers.stop_container_by_name"
        )

        patch_logger.start()
        patch_start_container.start()
        self.mock_stop_container = patch_stop_container.start()

        self.addCleanup(patch_logger.stop)
        self.addCleanup(patch_start_container.stop)
        self.addCleanup(patch_stop_container.stop)

    def test_container_name_is_randomized(self):
        container_name_regexp = (
            r"^%s-[a-z0-9]{6}$" % self.mock_dataset_processing.container_name
        )

        self.mock_dataset_processing.execute()

        self.assertIsNotNone(
            re.match(container_name_regexp, self.mock_dataset_processing.container_name)
        )

    def test_empty_command_args(self):
        expected_command = self.mock_dataset_processing.command
        self.mock_dataset_processing.execute()

        self.assertEqual(self.mock_dataset_processing.command, expected_command)

    def test_command_args(self):
        mock_command = "exec_command"
        expected_command = "%s_%s" % (
            self.mock_dataset_processing.command,
            mock_command,
        )
        self.mock_dataset_processing.execute(mock_command)

        self.assertEqual(self.mock_dataset_processing.command, expected_command)

    @patch(
        "tests.base.processing.containers.test_unit"
        ".MockAbstractContainerProcessing.configure_container"
    )
    def test_configure_container_exception_is_caught(self, mock_configure_container):
        mock_configure_container.side_effect = Exception()
        self.mock_dataset_processing.configure_container = mock_configure_container

        with self.assertRaises(Exception):
            self.mock_dataset_processing.execute()

    @patch(
        "tests.base.processing.containers.test_unit"
        ".MockAbstractContainerProcessing.configure_command"
    )
    def test_configure_command_exception_is_caught(self, mock_configure_command):
        mock_command = "exec_command"
        mock_configure_command.side_effect = Exception()
        self.mock_dataset_processing.configure_command = mock_configure_command

        with self.assertRaises(Exception):
            self.mock_dataset_processing.execute(mock_command)

    @patch("bugfinder.base.processing.containers.start_container")
    def test_start_container_exception_is_caught(self, mock_start_container):
        mock_start_container.side_effect = Exception()

        with self.assertRaises(Exception):
            self.mock_dataset_processing.execute()

    @patch(
        "tests.base.processing.containers.test_unit"
        ".MockAbstractContainerProcessing.send_commands"
    )
    def test_send_commands_exception_is_caught(self, mock_send_commands):
        mock_send_commands.side_effect = Exception()
        self.mock_dataset_processing.send_commands = mock_send_commands

        with self.assertRaises(Exception):
            self.mock_dataset_processing.execute()

    @patch(
        "tests.base.processing.containers.test_unit"
        ".MockAbstractContainerProcessing.configure_detach"
    )
    def test_stop_container_called_if_container_exists(self, mock_configure_detach):
        mock_configure_detach.return_value = True
        self.mock_dataset_processing.configure_detach = mock_configure_detach

        self.mock_dataset_processing.execute()
        self.mock_stop_container.assert_called()

    @patch(
        "tests.base.processing.containers.test_unit"
        ".MockAbstractContainerProcessing.configure_detach"
    )
    @patch("bugfinder.base.processing.containers.start_container")
    def test_stop_container_not_called_if_container_is_none(
        self, mock_start_container, mock_configure_detach
    ):
        mock_start_container.return_value = None
        mock_configure_detach.return_value = True
        self.mock_dataset_processing.configure_detach = mock_configure_detach

        self.mock_dataset_processing.execute()
        self.mock_stop_container.assert_not_called()

    def test_stop_container_not_called_if_container_is_detached(self):
        self.mock_dataset_processing.execute()
        self.mock_stop_container.assert_not_called()
