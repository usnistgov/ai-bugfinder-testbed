from unittest import TestCase

from unittest.mock import patch, Mock

from bugfinder.processing.ast import AbstractASTMarkup
from bugfinder.base.dataset import CodeWeaknessClassificationDataset
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
        patch_paths(
            self, ["bugfinder.processing.ast.LOGGER", "bugfinder.base.processing.LOGGER"]
        )

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        dataset.ops_queue = list()

        self.dataset_processing = self.MockASTMarkup(dataset)

    @patch("bugfinder.processing.neo4j.Neo4J3Processing.send_commands")
    def test_send_commands_called(self, mock_send_commands):
        self.dataset_processing.send_commands()
        self.assertTrue(mock_send_commands.called)

    @patch.object(MockASTMarkup, "get_ast_information")
    @patch("bugfinder.processing.neo4j.Neo4J3Processing.send_commands")
    def test_get_ast_information_calls(
        self, mock_send_commands, mock_get_ast_information
    ):
        mock_send_commands.return_value = None

        self.dataset_processing.send_commands()
        self.assertTrue(mock_get_ast_information.called)

    @patch.object(MockASTMarkup, "build_ast_markup")
    @patch("bugfinder.processing.neo4j.Neo4J3Processing.send_commands")
    def test_build_ast_markup_calls(self, mock_send_commands, mock_build_ast_markup):
        mock_send_commands.return_value = None

        self.dataset_processing.send_commands()
        self.assertTrue(mock_build_ast_markup.called)

    @patch("bugfinder.processing.neo4j.Neo4J3Processing.neo4j_db")
    @patch("bugfinder.processing.neo4j.Neo4J3Processing.send_commands")
    def test_neo4j_run_calls(self, mock_send_commands, mock_neo4j_db):
        mock_send_commands.return_value = None

        self.dataset_processing.send_commands()
        self.assertTrue(mock_neo4j_db.run.called)
