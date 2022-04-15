from os.path import join

from bugfinder.base.processing.containers import (
    AbstractContainerProcessing,
)
from bugfinder.settings import LOGGER


class RightFixer(AbstractContainerProcessing):
    """Processing to change the ownership of every file."""

    def configure_container(self):
        """Set the variables for the container"""
        self.image_name = "right-fixer:latest"
        self.container_name = "right-fixer"
        self.volumes = {self.dataset.path: "/data"}

    def configure_command(self, command):
        """Create the command to be run"""
        self.command = join("/data", command)
        LOGGER.debug("Input command: %s.", self.command)

    def send_commands(self):
        """Process the command"""
        LOGGER.debug("Right fixed for Neo4j DB.")
