import pickle
from os.path import join
from unittest import TestCase
from unittest.mock import patch, mock_open

from bugfinder.ast import AbstractASTMarkup, ASTSetExporter
from bugfinder.settings import ROOT_DIR
from tests import patch_paths


class TestAbstractASTMarkupSendCommands(TestCase):
    class MockASTMarkup(AbstractASTMarkup):
        def configure_container(self):
            return None

        def get_ast_information(self):
            return ["mock_item_1", "mock_item_2"]

        def build_ast_markup(self, ast_item):
            return None

    def setUp(self) -> None:
        patch_paths(self, [
            "bugfinder.ast.LOGGER"
        ])

        self.dataset_processing = self.MockASTMarkup(None)

    @patch("bugfinder.neo4j.Neo4J3Processing.send_commands")
    def test_send_commands_called(self, mock_send_commands):
        self.dataset_processing.send_commands()
        self.assertTrue(mock_send_commands.called)

    @patch.object(MockASTMarkup, "get_ast_information")
    @patch("bugfinder.neo4j.Neo4J3Processing.send_commands")
    def test_get_ast_information_calls(
        self, mock_send_commands, mock_get_ast_information
    ):
        mock_send_commands.return_value = None

        self.dataset_processing.send_commands()
        self.assertTrue(mock_get_ast_information.called)

    @patch.object(MockASTMarkup, "build_ast_markup")
    @patch("bugfinder.neo4j.Neo4J3Processing.send_commands")
    def test_build_ast_markup_calls(
        self, mock_send_commands, mock_build_ast_markup
    ):
        mock_send_commands.return_value = None

        self.dataset_processing.send_commands()
        self.assertTrue(mock_build_ast_markup.called)

    @patch("bugfinder.neo4j.Neo4J3Processing.neo4j_db")
    @patch("bugfinder.neo4j.Neo4J3Processing.send_commands")
    def test_neo4j_run_calls(
        self, mock_send_commands, mock_neo4j_db
    ):
        mock_send_commands.return_value = None

        self.dataset_processing.send_commands()
        self.assertTrue(mock_neo4j_db.run.called)


class TestASTSetExporterExecute(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = ASTSetExporter(None)

    @patch("bugfinder.neo4j.Neo4J3Processing.execute")
    def test_ast_file_is_setup(self, mock_execute):
        mock_execute.return_value = None
        expected_result = "mock_ast_file"
        self.dataset_processing.execute(ast_file=expected_result)
        self.assertEqual(self.dataset_processing.ast_file, expected_result)

    @patch("bugfinder.neo4j.Neo4J3Processing.execute")
    def test_execute_called(self, mock_execute):
        self.dataset_processing.execute()
        self.assertTrue(mock_execute.called)


class TestASTSetExporterConfigureContainer(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = ASTSetExporter(None)

    @patch("bugfinder.neo4j.Neo4J3Processing.configure_container")
    def test_configure_container_called(self, mock_configure_container):
        self.dataset_processing.configure_container()
        self.assertTrue(mock_configure_container.called)

    @patch("bugfinder.neo4j.Neo4J3Processing.configure_container")
    def test_container_name_is_setup(self, mock_configure_container):
        mock_configure_container.return_value = None
        self.dataset_processing.configure_container()
        self.assertEqual(self.dataset_processing.container_name, "ast-set-generator")


class TestASTSetExporterSendCommands(TestCase):
    def setUp(self) -> None:
        patch_paths(self, [
            "builtins.open"
        ])
        self.dataset_processing = ASTSetExporter(None)
        self.dataset_processing.ast_file = "mock_file"

    @patch("bugfinder.neo4j.Neo4J3Processing.neo4j_db")
    @patch("bugfinder.neo4j.Neo4J3Processing.send_commands")
    def test_send_commands_called(self, mock_send_commands, mock_neo4j_db):
        mock_neo4j_db.return_value = None
        self.dataset_processing.send_commands()
        self.assertTrue(mock_send_commands.called)

    @patch("bugfinder.neo4j.Neo4J3Processing.neo4j_db")
    @patch("bugfinder.ast.load")
    @patch("bugfinder.ast.exists")
    @patch("bugfinder.neo4j.Neo4J3Processing.send_commands")
    def test_ast_file_reloaded_if_exists(self, mock_send_commands, mock_exists,
                                         mock_load, mock_neo4j_db):
        mock_send_commands.return_value = None
        mock_exists.return_value = True
        mock_load.return_value = []
        mock_neo4j_db.return_value = None

        with patch("builtins.open", mock_open(read_data=b"data")) as mock_file:
            self.dataset_processing.send_commands()
            mock_file.assert_any_call(
                join(ROOT_DIR, self.dataset_processing.ast_file),
                "rb"
            )

            self.assertEqual(mock_file.call_count, 2)

    @patch("bugfinder.neo4j.Neo4J3Processing.neo4j_db")
    @patch("bugfinder.ast.exists")
    @patch("bugfinder.neo4j.Neo4J3Processing.send_commands")
    def test_ast_list_empty_if_file_does_not_exists(
            self, mock_send_commands, mock_exists, mock_neo4j_db
    ):
        mock_send_commands.return_value = None
        mock_exists.return_value = False
        mock_neo4j_db.return_value = None

        with patch("builtins.open", mock_open(read_data=b"data")) as mock_file:
            self.dataset_processing.send_commands()
            mock_file.assert_any_call(
                join(ROOT_DIR, self.dataset_processing.ast_file),
                "wb"
            )

            self.assertEqual(mock_file.call_count, 1)






