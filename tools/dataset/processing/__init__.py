from abc import ABC, abstractmethod
from os import listdir
from os.path import join

from tools.settings import LOGGER
from tools.utils.containers import start_container, stop_container_by_name


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
    detach = True

    container = None

    def execute(self):
        try:
            self.configure_container()

            self.container = start_container(
                self.image_name, self.container_name, self.ports, self.volumes,
                self.environment, self.detach
            )

            self.send_commands()
        except Exception as e:
            LOGGER.error("Error while running commands: %s" % str(e))

        if self.container is not None and self.detach:
            stop_container_by_name(self.container_name)

    @abstractmethod
    def configure_container(self):
        raise NotImplementedError("method not implemented")

    @abstractmethod
    def send_commands(self):
        raise NotImplementedError("method not implemented")
