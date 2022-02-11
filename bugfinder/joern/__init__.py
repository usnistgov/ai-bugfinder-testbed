""" Module containing abstract classes for any Joern processing.
"""
from abc import abstractmethod

from bugfinder.dataset.processing import DatasetProcessingWithContainer


class JoernDefaultDatasetProcessing(DatasetProcessingWithContainer):
    """Abstract Joern processing class"""

    def configure_container(self):
        """Setup the properties of the container"""
        self.volumes = {self.dataset.path: "/code"}
        self.detach = False

    @abstractmethod
    def send_commands(self):
        """Send the commands. Must be implemented by subclasses."""
        raise NotImplementedError("Method 'send_commands' not implemented.")
