from abc import ABC, abstractmethod
from os import listdir
from os.path import join

from bugfinder.settings import LOGGER
from bugfinder.utils.containers import start_container, stop_container_by_name
from bugfinder.utils.rand import get_rand_string


class DatasetProcessing(ABC):
    def __init__(self, dataset):
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
    image_name = ""
    container_name = ""
    ports = None
    volumes = None
    environment = None
    command = None
    detach = True

    container = None

    def execute(self, command_args=None):
        try:
            self.configure_container()

            self.container_name = "%s-%s" % (
                self.container_name,
                get_rand_string(6, special=False, upper=False),
            )

            if command_args is not None:
                self.configure_command(command_args)

            self.container = start_container(
                self.image_name,
                self.container_name,
                self.ports,
                self.volumes,
                self.environment,
                self.command,
                self.detach,
            )

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
