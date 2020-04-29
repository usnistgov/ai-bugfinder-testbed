from unittest import TestCase
from unittest.mock import patch

from docker.errors import APIError

from bugfinder.neo4j.annot import Neo4JAnnotations
from tests import patch_paths


class TestNeo4JAnnotationsConfigureContainer(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = Neo4JAnnotations(None)

    @patch("bugfinder.neo4j.annot.super")
    def test_super_configure_container_called(self, mock_super):
        self.dataset_processing.configure_container()

        self.assertTrue(mock_super().configure_container.called)

    @patch("bugfinder.neo4j.annot.super")
    def test_container_name_correct(self, mock_super):
        mock_super().configure_container.return_value = None
        self.dataset_processing.configure_container()

        self.assertEqual(self.dataset_processing.container_name, "neo3-annot")


class TestNeo4JAnnotationsSendCommand(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.neo4j.annot.LOGGER"])

        self.dataset_processing = Neo4JAnnotations(None)

    @patch("bugfinder.neo4j.annot.super")
    @patch("bugfinder.neo4j.annot.Neo4JAnnotations.neo4j_db")
    def test_super_send_commands_called(self, mock_neo4j_db, mock_super):
        mock_neo4j_db.run.return_value = None

        self.dataset_processing.send_commands()
        self.assertTrue(mock_super().send_commands.called)

    @patch("bugfinder.neo4j.annot.super")
    @patch("bugfinder.neo4j.annot.Neo4JAnnotations.neo4j_db")
    def test_neo4j_db_run_called(self, mock_neo4j_db, mock_super):
        mock_neo4j_db.run.return_value = None
        mock_super().send_commands.return_value = None

        self.dataset_processing.send_commands()
        self.assertTrue(mock_neo4j_db.run.called)

    @patch("bugfinder.neo4j.annot.super")
    @patch("bugfinder.neo4j.annot.Neo4JAnnotations.neo4j_db")
    def test_api_error_is_caught(self, mock_neo4j_db, mock_super):
        mock_neo4j_db.run.side_effect = APIError("mock_error")
        mock_super().send_commands.return_value = None

        self.dataset_processing.send_commands()
