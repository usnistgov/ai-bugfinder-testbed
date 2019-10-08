from abc import abstractmethod

from tools.dataset.processing import DatasetProcessingWithContainer


class JoernDefaultDatasetProcessing(DatasetProcessingWithContainer):
    def configure_container(self):
        pass

    @abstractmethod
    def send_commands(self):
        raise NotImplementedError("method not implemented")
