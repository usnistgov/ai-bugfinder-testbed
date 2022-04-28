""" Module containing importing utilities for Neo4J
"""
from os.path import join

from bugfinder.processing.neo4j import Neo4J3Processing
from bugfinder.settings import LOGGER


class Neo4J3Importer(Neo4J3Processing):
    """Importer class to Neo4J v3.x"""

    db_name = "import.db"
    import_dir = "/var/lib/neo4j/import"

    def configure_container(self):
        """Setup container variables."""
        super().configure_container()

        self.container_name = "neo3-importer"
        self.volumes = {
            self.dataset.neo4j_dir: "/data/databases/%s" % self.db_name,
            "%s/import" % self.dataset.joern_dir: self.import_dir,
        }

    def send_commands(self):
        """Send commands to the container."""
        super().send_commands()
        LOGGER.debug("Importing CSV files...")

        self.container.exec_run(
            """
            ./bin/neo4j-admin import --database=%s --delimiter='TAB'
                --nodes=%s --relationships=%s
            """
            % (
                self.db_name,
                join(self.import_dir, "nodes.csv"),
                join(self.import_dir, "edges.csv"),
            )
        )

        LOGGER.info("CSV files successfully imported.")
