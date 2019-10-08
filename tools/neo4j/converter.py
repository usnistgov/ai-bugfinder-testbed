from os import makedirs, chown, walk, remove
from os.path import realpath, join, splitext

from tools.dataset.processing import DatasetProcessingWithContainer
from tools.settings import NEO4J_V3_MEMORY, LOGGER
from tools.utils.containers import wait_log_display
from tools.utils.dirs import copy_dir


class Neo4J2Converter(DatasetProcessingWithContainer):
    db_path = "neo4j_v3.db"
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
            realpath("%s/joern.db" % self.dataset.path):
                "/data/graph.db"
        }

    def send_commands(self):
        wait_log_display(self.container, self.START_STRING)

        destination_path = join(self.dataset.path, self.db_path)
        makedirs(destination_path)

        if not copy_dir(
            join(self.dataset.path, "joern.db"),
            destination_path
        ):
            raise Exception("Copy to neo4j-v3 failed.")

        for dirname, sudirs, filelist in walk(destination_path):
            for filename in filelist:
                (filetype, fileext) = splitext(filename)

                if fileext == ".id":
                    remove(join(dirname, filename))


class RightFixer(DatasetProcessingWithContainer):
    def configure_container(self):
        self.image_name = "right-fixer:latest"
        self.container_name = "right-fixer"
        self.volumes = {
            realpath(self.dataset.path): "/data"
        }

    def configure_command(self, command):
        self.command = join("/data", command)
        LOGGER.debug("Input command: %s" % self.command)

    def send_commands(self):
        LOGGER.debug("Right fixed for Neo4j DB.")


class Neo4J3Converter(DatasetProcessingWithContainer):
    db_path = "neo4j_v3.db"
    START_STRING = "Remote interface available"

    def configure_container(self):
        self.image_name = "neo4j-ai:latest"
        self.container_name = "neo3-converter"
        self.environment = {
            "NEO4J_dbms_memory_pagecache_size": NEO4J_V3_MEMORY,
            "NEO4J_dbms_memory_heap_max__size": NEO4J_V3_MEMORY,
            "NEO4J_dbms_allow__upgrade": "true",
            "NEO4J_dbms_shell_enabled": "true",
            "NEO4J_AUTH": "none"
        }
        self.ports = {
            "7474": "7474",
            "7687": "7687",
        }
        self.volumes = {
            realpath("%s/%s" % (self.dataset.path, self.db_path)):
                "/data/databases/graph.db"
        }

    def send_commands(self):
        wait_log_display(self.container, self.START_STRING)
        LOGGER.debug("Imported DB into Neo4J v3")
