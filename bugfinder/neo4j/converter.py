from os import makedirs, walk, remove
from os.path import join, splitext

from bugfinder.dataset.processing import DatasetProcessingWithContainer
from bugfinder.neo4j import Neo4J3Processing
from bugfinder.settings import LOGGER
from bugfinder.utils.containers import wait_log_display
from bugfinder.utils.dirs import copy_dir


class Neo4J2Converter(DatasetProcessingWithContainer):
    START_STRING = "Remote interface ready"

    def configure_container(self):
        self.image_name = "neo4j:2.3"
        self.container_name = "neo2-converter"
        self.environment = {
            "NEO4J_CACHE_MEMORY": "2048M",
            "NEO4J_HEAP_MEMORY": "2048",
            "NEO4J_ALLOW_STORE_UPGRADE": "true",
            "NEO4J_AUTH": "none"
        }
        self.ports = {
            "7474": "7474"
        }
        self.volumes = {
            self.dataset.joern_dir: "/data/graph.db"
        }

    def send_commands(self):
        wait_log_display(self.container, self.START_STRING)

        # Copy Joern directory content to Neo4J directory content
        makedirs(self.dataset.neo4j_dir)
        if not copy_dir(
            self.dataset.joern_dir,
            self.dataset.neo4j_dir
        ):
            raise Exception("Copy to neo4j-v3 failed")

        for dirname, sudirs, filelist in walk(self.dataset.neo4j_dir):
            for filename in filelist:
                (filetype, fileext) = splitext(filename)

                if fileext == ".id":
                    remove(join(dirname, filename))


class Neo4J3Converter(Neo4J3Processing):
    def configure_container(self):
        super().configure_container()
        self.container_name = "neo3-converter"

    def send_commands(self):
        super().send_commands()
        LOGGER.debug("Imported DB into Neo4J v3")
