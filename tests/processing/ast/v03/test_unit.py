from unittest import TestCase
from unittest.mock import patch

from bugfinder.processing.ast.v03 import Neo4JASTMarkup

# WARNING This test was copied from ast.v02 and the
# data structures have not been updated for ast.v03


class TestNeo4JASTMarkupConfigureContainer(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = Neo4JASTMarkup(None)

    @patch("bugfinder.processing.ast.AbstractASTMarkup.configure_container")
    def test_configure_container_called(self, mock_configure_container):
        self.dataset_processing.configure_container()
        self.assertTrue(mock_configure_container.called)

    @patch("bugfinder.processing.ast.AbstractASTMarkup.configure_container")
    def test_container_name_is_correct(self, mock_configure_container):
        expected_result = "ast-markup-v03"
        mock_configure_container.return_value = None
        self.dataset_processing.configure_container()

        self.assertEqual(self.dataset_processing.container_name, expected_result)


class TestNeo4JASTMarkupGetAstInformation(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = Neo4JASTMarkup(None)

    @patch("bugfinder.processing.neo4j.Neo4J3Processing.neo4j_db")
    def test_neo4j_db_run_called(self, mock_neo4j_db):
        self.dataset_processing.get_ast_information()
        self.assertTrue(mock_neo4j_db.run.called)

    @patch("bugfinder.processing.neo4j.Neo4J3Processing.neo4j_db")
    def test_returns_correct_datastructure(self, mock_neo4j_db):
        class MockNeo4JRunData(object):
            @staticmethod
            def data():
                return [
                    {
                        "id": "mock_id",
                        "ast": "mock_ast",
                    }
                ]

        mock_neo4j_db.run.side_effect = [
            MockNeo4JRunData(),
            [
                {
                    "id": "mock_id",
                    "ast": "mock_ast",
                }
            ],
        ]

        expected_result = [
            {
                "id": "mock_id",
                "ast": "mock_ast",
            }
        ]

        self.assertListEqual(
            self.dataset_processing.get_ast_information(), expected_result
        )


class TestNeo4JASTMarkupBuildAstMarkup(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = Neo4JASTMarkup(None)

    def test_returns_correct_datastructure(self):
        ast_item = {
            "id": "mock_id",
            "ast": "mock_ast",
        }
        expected_result = {"id": "mock_id", "ast": "mock_ast"}

        self.assertDictEqual(
            self.dataset_processing.build_ast_markup(ast_item), expected_result
        )
