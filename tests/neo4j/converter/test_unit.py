from unittest import TestCase
from unittest.mock import Mock, patch

from bugfinder.dataset import CWEClassificationDataset
from bugfinder.neo4j.converter import Neo4J3Converter, Neo4J2Converter
from tests import patch_paths


class TestNeo4J2ConverterDefault(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = Neo4J2Converter(None)

    def test_start_string_correct(self):
        self.assertEqual(
            self.dataset_processing.START_STRING, "Remote interface ready"
        )


class TestNeo4J2ConverterConfigureContainer(TestCase):
    def setUp(self) -> None:
        self.dataset = Mock(spec=CWEClassificationDataset)
        self.dataset.joern_dir = "mock_joern_dir"
        self.dataset_processing = Neo4J2Converter(self.dataset)

    def test_image_name_correct(self):
        self.dataset_processing.configure_container()

        self.assertEqual(self.dataset_processing.image_name, "neo4j:2.3")

    def test_container_name_correct(self):
        self.dataset_processing.configure_container()

        self.assertEqual(self.dataset_processing.container_name, "neo2-converter")

    def test_environment_correct(self):
        self.dataset_processing.configure_container()

        self.assertDictEqual(self.dataset_processing.environment, {
            "NEO4J_CACHE_MEMORY": "2048M",
            "NEO4J_HEAP_MEMORY": "2048",
            "NEO4J_ALLOW_STORE_UPGRADE": "true",
            "NEO4J_AUTH": "none"
        })

    def test_ports_correct(self):
        self.dataset_processing.configure_container()

        self.assertDictEqual(self.dataset_processing.ports, {
            "7474": "7474"
        })

    def test_volumes_correct(self):
        self.dataset_processing.configure_container()

        self.assertDictEqual(self.dataset_processing.volumes, {
            self.dataset.joern_dir: "/data/graph.db"
        })


class TestNeo4J2ConverterSendCommands(TestCase):
    def setUp(self) -> None:
        self.dataset = Mock(spec=CWEClassificationDataset)
        self.dataset.joern_dir = "mock_joern_dir"
        self.dataset.neo4j_dir = "mock_neo4j_dir"
        self.dataset_processing = Neo4J2Converter(self.dataset)

    @patch("bugfinder.neo4j.converter.wait_log_display")
    @patch("bugfinder.neo4j.converter.makedirs")
    @patch("bugfinder.neo4j.converter.copy_dir")
    @patch("bugfinder.neo4j.converter.walk")
    def test_wait_for_display_called(self, mock_walk, mock_copy_dir, mock_makedirs,
                                     mock_wait_log_display):
        mock_walk.return_value = [(None, None, [])]
        mock_copy_dir.return_value = True
        mock_makedirs.return_value = None

        self.dataset_processing.send_commands()

        self.assertTrue(mock_wait_log_display.called)

    @patch("bugfinder.neo4j.converter.wait_log_display")
    @patch("bugfinder.neo4j.converter.makedirs")
    @patch("bugfinder.neo4j.converter.copy_dir")
    @patch("bugfinder.neo4j.converter.walk")
    def test_makedirs_called(self, mock_walk, mock_copy_dir, mock_makedirs,
                             mock_wait_log_display):
        mock_wait_log_display.return_value = None
        mock_walk.return_value = [(None, None, [])]
        mock_copy_dir.return_value = True
        mock_makedirs.return_value = None

        self.dataset_processing.send_commands()

        self.assertTrue(mock_makedirs.called)

    @patch("bugfinder.neo4j.converter.wait_log_display")
    @patch("bugfinder.neo4j.converter.makedirs")
    @patch("bugfinder.neo4j.converter.copy_dir")
    def test_failed_dir_copy_raises_exception(self, mock_copy_dir, mock_makedirs,
                                              mock_wait_log_display):
        mock_wait_log_display.return_value = None
        mock_copy_dir.return_value = False
        mock_makedirs.return_value = None

        with self.assertRaises(Exception):
            self.dataset_processing.send_commands()

    @patch("bugfinder.neo4j.converter.wait_log_display")
    @patch("bugfinder.neo4j.converter.makedirs")
    @patch("bugfinder.neo4j.converter.copy_dir")
    @patch("bugfinder.neo4j.converter.walk")
    @patch("bugfinder.neo4j.converter.remove")
    def test_id_files_removed_from_dir(self, mock_remove, mock_walk, mock_copy_dir,
                                       mock_makedirs, mock_wait_log_display):
        mock_wait_log_display.return_value = None
        mock_walk.return_value = [("mockdir", None, ["test.txt", "test.id"])]
        mock_copy_dir.return_value = True
        mock_makedirs.return_value = None

        self.dataset_processing.send_commands()

        mock_remove.assert_called_with("mockdir/test.id")


class TestNeo4J3ConverterConfigureContainer(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = Neo4J3Converter(None)

    @patch("bugfinder.neo4j.converter.super")
    def test_super_configure_container_called(self, mock_super):
        self.dataset_processing.configure_container()

        self.assertTrue(mock_super().configure_container.called)

    @patch("bugfinder.neo4j.converter.super")
    def test_container_name_correct(self, mock_super):
        mock_super().configure_container.return_value = None

        self.dataset_processing.configure_container()

        self.assertEqual(self.dataset_processing.container_name, "neo3-converter")


class TestNeo4J3ConverterSendCommands(TestCase):
    def setUp(self) -> None:
        patch_paths(self, [
            "bugfinder.neo4j.converter.LOGGER"
        ])

        self.dataset_processing = Neo4J3Converter(None)

    @patch("bugfinder.neo4j.converter.super")
    def test_super_send_commands_called(self, mock_super):
        self.dataset_processing.send_commands()

        self.assertTrue(mock_super().send_commands.called)
