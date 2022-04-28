""" Module containing abstract classes for any Joern processing.
"""
from abc import abstractmethod

from bugfinder.base.processing.containers import AbstractContainerProcessing


class JoernDefaultDatasetProcessing(AbstractContainerProcessing):
    """Abstract Joern processing class"""

    def configure_container(self):
        """Setup the properties of the container"""
        self.volumes = {self.dataset.path: "/code"}
        self.detach = False

    @abstractmethod
    def send_commands(self):
        """Send the commands. Must be implemented by subclasses."""
        raise NotImplementedError("Method 'send_commands' not implemented.")
