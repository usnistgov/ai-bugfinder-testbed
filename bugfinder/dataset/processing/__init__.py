from abc import ABC, abstractmethod
from os import listdir
from os.path import join

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
        return self.value


class DatasetProcessing(ABC):
    def __init__(self, dataset):
        self.metadata = {"category": str(DatasetProcessingCategory.PROCESSING)}
        self.processing_stats = dict()

        self.dataset = dataset

    @abstractmethod
    def execute(self, *args, **kwargs):
        raise NotImplementedError("method not implemented")


class DatasetFileProcessing(DatasetProcessing):
    def execute(self):
        for test_case in self.dataset.test_cases:
            for filepath in listdir(join(self.dataset.path, test_case)):
                self.process_file(join(self.dataset.path, test_case, filepath))

        self.dataset.rebuild_index()

    @abstractmethod
    def process_file(self, filepath):
        raise NotImplementedError("method not implemented")


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

    def execute(self, command_args=None):
        try:
            self.configure_container()
            started = False

            self.container_name = "%s-%s" % (
                self.container_name,
                get_rand_string(6, special=False, upper=False),
            )

            if command_args is not None:
                self.configure_command(command_args)

            while not started:
                try:
                    # Randomly assign ports on the machine
                    assigned_ports = None
                    if self.container_ports is not None:
                        self.machine_ports = [
                            "%d" % randint(49152, 65535) for _ in self.container_ports
                        ]
                        assigned_ports = dict(
                            zip(self.container_ports, self.machine_ports)
                        )

                    self.container = start_container(
                        self.image_name,
                        self.container_name,
                        assigned_ports,
                        self.volumes,
                        self.environment,
                        self.command,
                        self.detach,
                    )

                    started = True
                except Exception as e:  # Try to restart the container if an error occured
                    LOGGER.error(
                        "An exception has occured while starting the container: %s"
                        % str(e)
                    )
                    sleep(5)
                    self.start_retries -= 1

                    if self.start_retries == 0:
                        raise e

            self.send_commands()
        except Exception as e:
            LOGGER.error("Error while running commands: %s" % str(e))
            raise e
        finally:
            if self.container is not None and self.detach:
                stop_container_by_name(self.container_name)

    @abstractmethod
    def configure_container(self):
        raise NotImplementedError("method not implemented")

    def configure_command(self, command):
        raise Exception("Command %s not handled by container")

    @abstractmethod
    def send_commands(self):
        raise NotImplementedError("method not implemented")
