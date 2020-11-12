from bugfinder.joern import JoernDefaultDatasetProcessing
from bugfinder.settings import LOGGER


class JoernDatasetProcessing(JoernDefaultDatasetProcessing):
    def configure_container(self):
        super().configure_container()

        self.image_name = "joern-lite:0.3.1"
        self.container_name = "joern031"

    def send_commands(self):
        LOGGER.info("Joern V0.3.1 processing done.")
        LOGGER.debug("Stopping '%s'..." % self.container_name)
