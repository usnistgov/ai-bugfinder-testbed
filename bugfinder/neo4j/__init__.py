from abc import abstractmethod

from py2neo import Graph

from bugfinder.dataset.processing import DatasetProcessingWithContainer
from bugfinder.dataset.processing.dataset_ops import RightFixer
from bugfinder.settings import NEO4J_V3_MEMORY
from bugfinder.utils.containers import wait_log_display


class Neo4J3Processing(DatasetProcessingWithContainer):
    start_string = "Remote interface available"
    neo4j_db = None

    @abstractmethod
    def configure_container(self):
        self.image_name = "neo4j-ai:latest"
        self.environment = {
            "NEO4J_dbms_memory_pagecache_size": NEO4J_V3_MEMORY,
            "NEO4J_dbms_memory_heap_max__size": NEO4J_V3_MEMORY,
            "NEO4J_dbms_allow__upgrade": "true",
            "NEO4J_dbms_shell_enabled": "true",
            "NEO4J_AUTH": "none",
        }
        self.container_ports = ["7474", "7687"]
        self.volumes = {
            self.dataset.neo4j_dir: "/data/databases/graph.db",
        }

    def fix_data_folder_rights(self):
        current_ops_queue = self.dataset.ops_queue

        # Reset queue to add the right fixer step
        self.dataset.clear_queue()
        self.dataset.queue_operation(
            RightFixer,
            {"command_args": "neo4j_v3.db 101 101"},
        )
        self.dataset.process()

        self.dataset.ops_queue = current_ops_queue

    def send_commands(self):
        wait_log_display(self.container, self.start_string)

        self.neo4j_db = Graph(
            scheme="http",
            host="0.0.0.0",
            port=self.machine_ports[self.container_ports.index("7474")],
        )
