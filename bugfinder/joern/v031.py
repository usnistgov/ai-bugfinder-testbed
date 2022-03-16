""" Processing class for Joern version 0.3.1.
"""
from bugfinder.joern import JoernDefaultDatasetProcessing
from bugfinder.settings import LOGGER


class JoernDatasetProcessing(JoernDefaultDatasetProcessing):
    """Processing class for Joern version 0.3.1."""

    def configure_container(self):
        """Setup the container"""
        super().configure_container()

        self.image_name = "joern-lite:0.3.1"
        self.container_name = "joern031"

    def send_commands(self):
        """Send commands to the container"""
        LOGGER.info("Joern V0.3.1 processing done.")
        LOGGER.debug("Stopping '%s'...", self.container_name)
