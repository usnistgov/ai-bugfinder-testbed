from abc import abstractmethod

from bugfinder.dataset.processing import DatasetProcessingWithContainer


class JoernDefaultDatasetProcessing(DatasetProcessingWithContainer):
    def configure_container(self):
        self.volumes = {
            self.dataset.path: "/code"
        }
        self.detach = False

    @abstractmethod
    def send_commands(self):
        raise NotImplementedError("method not implemented")
