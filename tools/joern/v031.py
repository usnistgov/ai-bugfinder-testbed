from os.path import realpath

from tools.joern import JoernDefaultDatasetProcessing
from tools.settings import LOGGER


class JoernDatasetProcessing(JoernDefaultDatasetProcessing):
    def configure_container(self):
        super().configure_container()

        self.image_name = "joern-lite:0.3.1"
        self.container_name = "joern031"

    def send_commands(self):
        LOGGER.debug("Joern processing done.")
