from unittest import TestCase
from unittest.mock import patch, Mock

from bugfinder.dataset import CWEClassificationDataset
from bugfinder.neo4j.importer import Neo4J3Importer
from tests import patch_paths


class TestNeo4J3ImporterDefault(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, [
                "bugfinder.neo4j.importer.LOGGER",
                "bugfinder.dataset.processing.LOGGER"
            ]
        )

        self.dataset_processing = Neo4J3Importer(None)

    def test_db_name_correct(self):
        self.assertEqual(self.dataset_processing.db_name, "import.db")

    def test_import_dir_correct(self):
        self.assertEqual(self.dataset_processing.import_dir, "/var/lib/neo4j/import")


class TestNeo4J3ImporterConfigureContainer(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, [
                "bugfinder.neo4j.importer.LOGGER",
                "bugfinder.dataset.processing.LOGGER"
            ]
        )

        self.dataset = Mock(spec=CWEClassificationDataset)
        self.dataset.neo4j_dir = "mock_neo4j_dir"
        self.dataset.joern_dir = "mock_joern_dir"
        self.dataset_processing = Neo4J3Importer(self.dataset)

    @patch("bugfinder.neo4j.importer.super")
    def test_super_configure_container_called(self, mock_super):
        self.dataset_processing.configure_container()

        self.assertTrue(mock_super().configure_container.called)

    @patch("bugfinder.neo4j.importer.super")
    def test_container_name_correct(self, mock_super):
        mock_super().configure_container.return_value = None

        self.dataset_processing.configure_container()

        self.assertEqual(self.dataset_processing.container_name, "neo3-importer")

    @patch("bugfinder.neo4j.importer.super")
    def test_volumes_correct(self, mock_super):
        mock_super().configure_container.return_value = None

        self.dataset_processing.configure_container()

        self.assertDictEqual(
            self.dataset_processing.volumes,
            {
                self.dataset.neo4j_dir: "/data/databases/%s"
                % self.dataset_processing.db_name,
                "%s/import"
                % self.dataset.joern_dir: self.dataset_processing.import_dir,
            },
        )


class TestNeo4J3ImporterSendCommands(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, [
                "bugfinder.neo4j.importer.LOGGER",
                "bugfinder.dataset.processing.LOGGER"
            ]
        )

        self.dataset_processing = Neo4J3Importer(None)

    @patch("bugfinder.neo4j.importer.super")
    @patch("bugfinder.neo4j.importer.Neo4J3Importer.container")
    def test_super_send_commands_called(self, mock_container, mock_super):
        mock_container.exec_run.return_value = None

        self.dataset_processing.send_commands()

        self.assertTrue(mock_super().send_commands.called)

    @patch("bugfinder.neo4j.importer.super")
    @patch("bugfinder.neo4j.importer.Neo4J3Importer.container")
    def test_container_exec_run_called(self, mock_container, mock_super):
        mock_super().send_commands.return_value = None
        mock_container.exec_run.return_value = None

        self.dataset_processing.send_commands()

        self.assertTrue(mock_container.exec_run.called)
