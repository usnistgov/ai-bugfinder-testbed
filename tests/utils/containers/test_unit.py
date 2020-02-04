""" Utility for Docker containers
"""
import unittest
from multiprocessing import Process
from os.path import realpath
from unittest.mock import patch, Mock

from bugfinder.utils.containers import start_container, wait_log_display, \
    stop_container_by_name
from tests import mock_return_fn_args_as_dict


class TestStartContainer(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.image_name = "mock_image_name"
        cls.container_name = "mock_container_name"

    @patch("docker.models.containers.ContainerCollection.run")
    def test_default_parameters(self, mock_docker_run):
        mock_docker_run.side_effect = mock_return_fn_args_as_dict
        expected_value = {
            "arg0": self.image_name,
            "name": self.container_name,
            "environment": {},
            "ports": {},
            "volumes": {},
            "detach": True,
            "remove": False
        }

        value = start_container(self.image_name, self.container_name)
        self.assertDictEqual(value, expected_value)

    @patch("docker.models.containers.ContainerCollection.run")
    def test_unaltered_ports_arg(self, mock_docker_run):
        mock_docker_run.side_effect = mock_return_fn_args_as_dict
        ports = {"8080": "8080"}
        expected_value = {
            "arg0": self.image_name,
            "name": self.container_name,
            "environment": {},
            "ports": ports,
            "volumes": {},
            "detach": True,
            "remove": False
        }

        value = start_container(self.image_name, self.container_name, ports=ports)
        self.assertDictEqual(value, expected_value)

    @patch("docker.models.containers.ContainerCollection.run")
    def test_unaltered_volume_arg(self, mock_docker_run):
        mock_docker_run.side_effect = mock_return_fn_args_as_dict
        volumes = {"./data": "/tmp/data"}

        expected_value = {
            "arg0": self.image_name,
            "name": self.container_name,
            "environment": {},
            "ports": {},
            "volumes": {
                realpath(vol_key): {
                    "bind": vol_value,
                    "mode": "rw"
                } for vol_key, vol_value in volumes.items()
            },
            "detach": True,
            "remove": False
        }

        value = start_container(self.image_name, self.container_name, volumes=volumes)
        self.assertDictEqual(value, expected_value)

    @patch("docker.models.containers.ContainerCollection.run")
    def test_unaltered_env_arg(self, mock_docker_run):
        mock_docker_run.side_effect = mock_return_fn_args_as_dict
        env = {"key": "value"}
        expected_value = {
            "arg0": self.image_name,
            "name": self.container_name,
            "environment": env,
            "ports": {},
            "volumes": {},
            "detach": True,
            "remove": False
        }

        value = start_container(self.image_name, self.container_name, environment=env)
        self.assertDictEqual(value, expected_value)

    @patch("docker.models.containers.ContainerCollection.run")
    def test_unaltered_command_arg(self, mock_docker_run):
        mock_docker_run.side_effect = mock_return_fn_args_as_dict
        command = "bin arg0 ... argN"
        expected_value = {
            "arg0": self.image_name,
            "name": self.container_name,
            "environment": {},
            "ports": {},
            "volumes": {},
            "detach": True,
            "remove": False,
            "command": command
        }

        value = start_container(self.image_name, self.container_name, command=command)
        self.assertDictEqual(value, expected_value)

    @patch("docker.models.containers.ContainerCollection.run")
    def test_unaltered_detach_arg(self, mock_docker_run):
        mock_docker_run.side_effect = mock_return_fn_args_as_dict
        detach = False
        expected_value = {
            "arg0": self.image_name,
            "name": self.container_name,
            "environment": {},
            "ports": {},
            "volumes": {},
            "detach": detach,
            "remove": not detach
        }

        value = start_container(self.image_name, self.container_name, detach=detach)
        self.assertDictEqual(value, expected_value)


class TestWaitLogDisplay(unittest.TestCase):
    def test_string_returns_exits_before_timeout(self):
        container_mock = Mock()
        container_mock.logs.return_value = "logs content".encode("utf-8")

        p = Process(target=wait_log_display, args=(container_mock, "logs", 3))
        p.start()

        # Test if the function is still alive after 2 seconds
        p.join(2)
        self.assertFalse(p.is_alive())  # Expect function is terminated

    def test_string_not_in_log_exits_after_timeout(self):
        container_mock = Mock()
        container_mock.logs.return_value = "logs content".encode("utf-8")

        p = Process(target=wait_log_display, args=(container_mock, "not present", 2))
        p.start()

        # Test if the function is still alive after 2 seconds
        p.join(1)
        self.assertTrue(p.is_alive())  # Expect function is still running

        # Test if the function is still alive after 2 seconds
        p.join(2)
        self.assertFalse(p.is_alive())  # Expect function has stopped


class TestStopContainerByName(unittest.TestCase):

    @patch("docker.models.containers.ContainerCollection.get")
    def test_valid_name_exits_correctly(self, mock_container):
        mock_container_object = Mock()
        mock_container_object.stop.return_value = None
        mock_container.return_value = mock_container_object

        stop_container_by_name("container_name")

    @patch("docker.models.containers.ContainerCollection.get")
    def test_invalid_name_raises_exception(self, mock_container):
        mock_container.side_effect = Exception()

        self.assertRaises(Exception, stop_container_by_name, "container_name")
