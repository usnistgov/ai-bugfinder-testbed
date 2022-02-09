from os import listdir
from os.path import join

from abc import ABC, abstractmethod
from enum import Enum
from random import randint
from time import sleep

from bugfinder.settings import LOGGER
from bugfinder.utils.containers import start_container, stop_container_by_name
from bugfinder.utils.rand import get_rand_string


class DatasetProcessingCategory(Enum):
    __NONE__ = "__null__"
    PROCESSING = "processing"
    TRAINING = "training"

    def __str__(self):
        return str(self.value)


class DatasetProcessingDeprecation:
    def __init__(self, notice, deprecated_in=None, removed_in=None):
        self.notice = notice
        self.deprecated_in = deprecated_in
        self.removed_in = removed_in


class DatasetProcessing(ABC):
    def __init__(self, dataset, deprecation_warning=None):
        self.metadata = {"category": str(DatasetProcessingCategory.PROCESSING)}
        self.processing_stats = {}
        self.dataset = dataset

        if deprecation_warning:
            deprecation_notice = "%s processing class deprecated" % str(
                self.__class__.__name__
            )

            if deprecation_warning.deprecated_in:
                deprecation_notice += " since %s" % deprecation_warning.deprecated_in

            if deprecation_warning.removed_in:
                if deprecation_warning.deprecated_in:
                    deprecation_notice += ","

                deprecation_notice += (
                    " will be removed in %s" % deprecation_warning.removed_in
                )

            deprecation_notice += ". Notice: %s" % deprecation_warning.notice
            LOGGER.warning(deprecation_notice)

    @abstractmethod
    def execute(self, *args, **kwargs):
        raise NotImplementedError("Method 'execute' not implemented.")


class DatasetFileProcessing(DatasetProcessing):
    def execute(self):
        for test_case in self.dataset.test_cases:
            for filepath in listdir(join(self.dataset.path, test_case)):
                self.process_file(join(self.dataset.path, test_case, filepath))

        self.dataset.rebuild_index()

    @abstractmethod
    def process_file(self, filepath):
        raise NotImplementedError("Method 'process_file' not implemented.")


class DatasetProcessingWithContainer(DatasetProcessing):
    start_retries = 3
    image_name = ""
    container_name = ""
    container_ports = None
    machine_ports = None
    volumes = None
    environment = None
    command = None
    detach = True

    container = None

    def execute(self, command_args=None, container_config=None):
        try:
            # Handle container configuration depending on wether a manual configuration
            # has been provided or not
            if container_config is None:
                self.configure_container()
            else:
                self.configure_container_with_dict(container_config)
            started = False

            self.container_name = "%s-%s" % (
                self.container_name,
                get_rand_string(6, special=False, upper=False),
            )

            if command_args is not None:
                self.configure_command(command_args)

            while not started:
                try:
                    self.container = start_container(
                        self.image_name,
                        self.container_name,
                        self.assign_ports(),
                        self.volumes,
                        self.environment,
                        self.command,
                        self.detach,
                    )

                    started = True
                except Exception as exc:  # Restart the container if an error occured
                    LOGGER.error(
                        "An exception has occured while starting the container: %s.",
                        str(exc),
                    )
                    sleep(5)
                    self.start_retries -= 1

                    if self.start_retries == 0:
                        raise exc

            self.send_commands()
        except Exception as exc:
            LOGGER.error("Error while running commands: %s.", str(exc))
            raise exc
        finally:
            if self.container is not None and self.detach:
                stop_container_by_name(self.container_name)

    def assign_ports(self):
        """Randomly assign ports on the machine."""
        assigned_ports = None
        if self.container_ports is not None:
            self.machine_ports = [
                "%d" % randint(49152, 65535) for _ in self.container_ports
            ]
            assigned_ports = dict(zip(self.container_ports, self.machine_ports))

        return assigned_ports

    @abstractmethod
    def configure_container(self):
        raise NotImplementedError("Method 'configure_container' not implemented.")

    def configure_container_with_dict(self, container_config):
        LOGGER.warning(
            "Manual configuration is not handled by the container. The class should "
            "implement 'configure_container_with_dict(self, container_config)' to handle"
            "manual configuration"
        )
        return self.configure_container()

    def configure_command(self, command):
        raise Exception("Command %s not handled by container")

    @abstractmethod
    def send_commands(self):
        raise NotImplementedError("Method 'send_commands' not implemented.")
