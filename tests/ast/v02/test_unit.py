from unittest import TestCase
from unittest.mock import patch

from bugfinder.ast.v02 import Neo4JASTMarkup
from tests import patch_paths


class TestNeo4JASTMarkupConfigureContainer(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, [
                "bugfinder.ast.LOGGER",
                "bugfinder.dataset.processing.LOGGER"
            ]
        )

        self.dataset_processing = Neo4JASTMarkup(None)

    @patch("bugfinder.ast.AbstractASTMarkup.configure_container")
    def test_configure_container_called(self, mock_configure_container):
        self.dataset_processing.configure_container()
        self.assertTrue(mock_configure_container.called)

    @patch("bugfinder.ast.AbstractASTMarkup.configure_container")
    def test_container_name_is_correct(self, mock_configure_container):
        expected_result = "ast-markup-v02"
        mock_configure_container.return_value = None
        self.dataset_processing.configure_container()

        self.assertEqual(self.dataset_processing.container_name, expected_result)


class TestNeo4JASTMarkupGetAstInformation(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, [
                "bugfinder.ast.LOGGER",
                "bugfinder.dataset.processing.LOGGER"
            ]
        )

        self.dataset_processing = Neo4JASTMarkup(None)

    @patch("bugfinder.neo4j.Neo4J3Processing.neo4j_db")
    def test_neo4j_db_run_called(self, mock_neo4j_db):
        self.dataset_processing.get_ast_information()
        self.assertTrue(mock_neo4j_db.run.called)

    @patch("bugfinder.neo4j.Neo4J3Processing.neo4j_db")
    def test_returns_correct_datastructure(self, mock_neo4j_db):
        class MockNeo4JRunData(object):
            @staticmethod
            def data():
                return [
                    {
                        "id": "mock_id",
                        "type": "mock_type",
                        "parent": "mock_parent",
                        "child_num": "mock_child_num",
                    }
                ]

        mock_neo4j_db.run.side_effect = [
            MockNeo4JRunData(),
            [
                {
                    "id": "mock_id",
                    "type": "mock_type",
                    "parent": "mock_parent",
                    "child_num": "mock_child_num",
                }
            ],
        ]

        expected_result = [
            {
                "id": "mock_id",
                "type": "mock_type",
                "ast": [
                    {
                        "id": "mock_id",
                        "parent": "mock_parent",
                        "type": "mock_type",
                        "child_num": "mock_child_num",
                    }
                ],
            }
        ]

        self.assertListEqual(
            self.dataset_processing.get_ast_information(), expected_result
        )


class TestNeo4JASTMarkupBuildAstMarkup(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self, [
                "bugfinder.ast.LOGGER",
                "bugfinder.dataset.processing.LOGGER"
            ]
        )

        self.dataset_processing = Neo4JASTMarkup(None)

    def test_returns_correct_datastructure(self):
        ast_item = {
            "id": "mock_id_0",
            "type": "A",
            "ast": [
                {"id": "mock_id_1", "type": "B", "parent": "mock_id_0", "child_num": 0},
                {"id": "mock_id_2", "type": "C", "parent": "mock_id_0", "child_num": 1},
                {"id": "mock_id_3", "type": "D", "parent": "mock_id_2", "child_num": 0},
                {"id": "mock_id_4", "type": "E", "parent": "mock_id_2", "child_num": 1},
            ],
        }
        expected_result = {"id": "mock_id_0", "ast": "A(B,C(D,E))"}

        self.assertDictEqual(
            self.dataset_processing.build_ast_markup(ast_item), expected_result
        )
