from unittest import TestCase
from unittest.mock import Mock, patch

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.processing.neo4j import Neo4J3Processing
from bugfinder import settings


class MockNeo4J3Processing(Neo4J3Processing):
    def configure_container(self):
        super().configure_container()


class TestNeo4J3ProcessingDefault(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = MockNeo4J3Processing(None)

    def test_start_string_correct(self):
        self.assertEqual(
            self.dataset_processing.start_string, "Remote interface available"
        )

    def test_neo4j_db_correct(self):
        self.assertEqual(self.dataset_processing.neo4j_db, None)


class TestNeo4J3ProcessingConfigureContainer(TestCase):
    def setUp(self) -> None:
        self.dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset.neo4j_dir = "mock_neo4j_dir"
        self.dataset_processing = MockNeo4J3Processing(self.dataset)

    def test_image_name_correct(self):
        self.dataset_processing.configure_container()

        self.assertEqual(self.dataset_processing.image_name, "neo4j-ai:latest")

    def test_environment_correct(self):
        self.dataset_processing.configure_container()

        self.assertDictEqual(
            self.dataset_processing.environment,
            {
                "NEO4J_dbms_memory_pagecache_size": settings.NEO4J_V3_MEMORY,
                "NEO4J_dbms_memory_heap_max__size": settings.NEO4J_V3_MEMORY,
                "NEO4J_dbms_allow__upgrade": "true",
                "NEO4J_dbms_shell_enabled": "true",
                "NEO4J_dbms_transaction_timeout": settings.NEO4J_DEFAULT_TIMEOUT,
                "NEO4J_AUTH": "none",
            },
        )

    def test_ports_correct(self):
        self.dataset_processing.configure_container()

        self.assertListEqual(
            self.dataset_processing.container_ports, ["7474", "7687", "7473"]
        )

    def test_volume_correct(self):
        self.dataset_processing.configure_container()

        self.assertDictEqual(
            self.dataset_processing.volumes,
            {
                self.dataset.neo4j_dir: "/data/databases/graph.db",
            },
        )


class TestNeo4J3ProcessingSendCommands(TestCase):
    def setUp(self) -> None:
        self.dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset.neo4j_dir = "mock_neo4j_dir"
        self.dataset_processing = MockNeo4J3Processing(self.dataset)
        self.dataset_processing.configure_container()
        self.dataset_processing.assign_ports()

    @patch("bugfinder.processing.neo4j.Graph")
    @patch("bugfinder.processing.neo4j.wait_log_display")
    def test_wait_for_log_display_called(self, mock_wait_log_display, mock_graph):
        mock_graph.return_value = None
        self.dataset_processing.send_commands()
        self.assertTrue(mock_wait_log_display.called)

    @patch("bugfinder.processing.neo4j.Graph")
    @patch("bugfinder.processing.neo4j.wait_log_display")
    def test_neo4j_db_initialized(self, mock_wait_log_display, mock_graph):
        mock_wait_log_display.return_value = None
        mock_graph.return_value = "mock_graph"
        self.dataset_processing.send_commands()

        self.assertEqual(self.dataset_processing.neo4j_db, "mock_graph")
