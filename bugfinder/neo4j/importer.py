from os.path import join

from bugfinder.neo4j import Neo4J3Processing
from bugfinder.settings import LOGGER


class Neo4J3Importer(Neo4J3Processing):
    db_name = "import.db"
    import_dir = "/var/lib/neo4j/import"

    def configure_container(self):
        super().configure_container()

        self.container_name = "neo3-importer"
        self.volumes = {
            self.dataset.neo4j_dir: "/data/databases/%s" % self.db_name,
            "%s/import" % self.dataset.joern_dir: self.import_dir,
        }

    def send_commands(self):
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
