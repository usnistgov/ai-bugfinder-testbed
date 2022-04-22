from unittest import TestCase
from unittest.mock import patch

from bugfinder.processing.ast.v01 import Neo4JASTMarkup
from tests import patch_paths


class TestNeo4JASTMarkupConfigureContainer(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, ["bugfinder.processing.ast.LOGGER", "bugfinder.base.processing.LOGGER"]
        )

        self.dataset_processing = Neo4JASTMarkup(None)

    @patch("bugfinder.processing.ast.AbstractASTMarkup.configure_container")
    def test_configure_container_called(self, mock_configure_container):
        self.dataset_processing.configure_container()
        self.assertTrue(mock_configure_container.called)

    @patch("bugfinder.processing.ast.AbstractASTMarkup.configure_container")
    def test_container_name_is_correct(self, mock_configure_container):
        mock_configure_container.return_value = None
        self.dataset_processing.configure_container()
        self.assertEqual(self.dataset_processing.container_name, "ast-markup-v01")


class TestNeo4JASTMarkupGetAstInformation(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, ["bugfinder.processing.ast.LOGGER", "bugfinder.base.processing.LOGGER"]
        )

        self.dataset_processing = Neo4JASTMarkup(None)

    @patch("bugfinder.processing.neo4j.Neo4J3Processing.neo4j_db")
    def test_neo4j_db_run_is_called(self, mock_neo4j_db):
        self.dataset_processing.get_ast_information()
        self.assertTrue(mock_neo4j_db.run.called)


class TestNeo4JASTMarkupBuildAstMarkup(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, ["bugfinder.processing.ast.LOGGER", "bugfinder.base.processing.LOGGER"]
        )

        self.dataset_processing = Neo4JASTMarkup(None)

    def test_returns_correct_datastructure(self):
        ast_item = {"id": "mock_id", "ast": ["a", "b", "c"]}
        expected_result = {"id": "mock_id", "ast": "a:b:c"}

        self.assertDictEqual(
            self.dataset_processing.build_ast_markup(ast_item), expected_result
        )
