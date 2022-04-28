""" Conversion module between Neo4J versions.
"""
from os import makedirs, walk, remove
from os.path import join, splitext

from bugfinder.base.processing.containers import AbstractContainerProcessing
from bugfinder.processing.neo4j import Neo4J3Processing
from bugfinder.settings import LOGGER
from bugfinder.utils.containers import wait_log_display
from bugfinder.utils.dirs import copy_dir


class Neo4J2Converter(AbstractContainerProcessing):
    """Converter to Neo4J version 2.x"""

    START_STRING = "Remote interface ready"

    def configure_container(self):
        """Setup container variables"""
        self.image_name = "neo4j:2.3"
        self.container_name = "neo2-converter"
        self.environment = {
            "NEO4J_CACHE_MEMORY": "2048M",
            "NEO4J_HEAP_MEMORY": "2048",
            "NEO4J_ALLOW_STORE_UPGRADE": "true",
            "NEO4J_AUTH": "none",
        }
        self.container_ports = ["7474"]
        self.volumes = {self.dataset.joern_dir: "/data/graph.db"}

    def send_commands(self):
        """Send commands to the container."""
        wait_log_display(self.container, self.START_STRING)

        LOGGER.debug("Importing DB into Neo4J v2.3...")

        # Copy Joern directory content to Neo4J directory content
        makedirs(self.dataset.neo4j_dir)
        if not copy_dir(self.dataset.joern_dir, self.dataset.neo4j_dir):
            raise Exception("Copy to neo4j-v3 failed.")

        for dirname, _, filelist in walk(self.dataset.neo4j_dir):
            for filename in filelist:
                (_, fileext) = splitext(filename)

                if fileext == ".id":
                    remove(join(dirname, filename))

        LOGGER.info("Imported DB into Neo4J v2.3.")


class Neo4J3Converter(Neo4J3Processing):
    """Converter for Neo4J v3.x"""

    def configure_container(self):
        """Setup container variables."""
        self.fix_data_folder_rights()

        super().configure_container()
        self.container_name = "neo3-converter"

    def send_commands(self):
        """Send commands to the container."""
        super().send_commands()
        LOGGER.info("Imported DB into Neo4J v3.")
