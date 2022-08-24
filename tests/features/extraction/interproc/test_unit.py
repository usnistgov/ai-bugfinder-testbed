from unittest import TestCase
from unittest.mock import patch, Mock
from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.features.extraction.interproc import FeatureExtractor
from tests import patch_paths


class InterprocTestCase(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.extraction.interproc.LOGGER"])
        self.dataset_processing = FeatureExtractor(None)


class TestFeatureExtractorConfigureContainer(InterprocTestCase):
    @patch("bugfinder.processing.neo4j.Neo4J3Processing.configure_container")
    def test_container_name_is_correct(self, mock_configure_container):
        mock_configure_container.return_value = None
        expected_container_name = "fext-interprocedural-raw"

        self.dataset_processing.configure_container()

        self.assertEqual(
            self.dataset_processing.container_name, expected_container_name
        )


class FeatureExtractorGetFlowgraphListForEntrypoint(InterprocTestCase):
    @patch("bugfinder.processing.neo4j.Neo4J3Processing.neo4j_db")
    def test_neo4j_db_run_is_called(self, mock_neo4j_db):
        self.dataset_processing.get_flowgraph_list_for_entrypoint({"id": None})
        self.assertTrue(mock_neo4j_db.run.called)

    @patch("bugfinder.processing.neo4j.Neo4J3Processing.neo4j_db")
    def test_flowgraph_list_is_correctly_formatted(self, mock_neo4j_db):
        expected_flowgraphs = [
            {
                "path_id": "path_id",
                "sink": True,
                "id": 123,
                "ast": "ast",
                "iorder": [],
                "inflow": [],
                "outflow": [4],
            }
        ]

        class MockNeo4JRunData(object):
            @staticmethod
            def data():
                return expected_flowgraphs

        mock_neo4j_db.run.side_effect = lambda _: MockNeo4JRunData()
        returned_flowgraphs = self.dataset_processing.get_flowgraph_list_for_entrypoint(
            {"id": None}
        )
        self.assertListEqual(returned_flowgraphs, expected_flowgraphs)


class FeatureExtractorExtractFeaturesWorker(InterprocTestCase):
    @patch("bugfinder.processing.neo4j.Neo4J3Processing.neo4j_db")
    def test_neo4j_db_run_is_called(self, mock_neo4j_db):
        self.dataset_processing.get_flowgraph_list_for_entrypoint({"id": None})
        self.assertTrue(mock_neo4j_db.run.called)

    @patch("bugfinder.processing.neo4j.Neo4J3Processing.neo4j_db")
    def test_features_are_correctly_formatted(self, mock_neo4j_db):
        expected_flowgraphs = [
            {
                "path_id": "path_id_0",
                "sink": False,
                "id": 123,
                "ast": "ast_01",
                "iorder": [],
                "inflow": [],
                "outflow": [4],
            },
            {
                "path_id": "path_id_0",
                "sink": False,
                "id": 123,
                "ast": "ast_02",
                "iorder": ["var01"],
                "inflow": [["ast_01", "v01", 4]],
                "outflow": [8],
            },
            {
                "path_id": "path_id_0",
                "sink": True,
                "id": 123,
                "ast": "ast_03",
                "iorder": ["var02", "var01"],
                "inflow": [["ast_01", "v01", 0], ["ast_02", "v02", 8]],
                "outflow": [],
            },
            {
                "path_id": "path_id_1",
                "sink": False,
                "id": 123,
                "ast": "ast_04",
                "iorder": [],
                "inflow": [],
                "outflow": [8],
            },
            {
                "path_id": "path_id_1",
                "sink": True,
                "id": 123,
                "ast": "ast_05",
                "iorder": [],
                "inflow": [],
                "outflow": [4],
            },
            {
                "path_id": "path_id_2",
                "sink": True,
                "id": 123,
                "ast": "ast_06",
                "iorder": [],
                "inflow": [],
                "outflow": [4],
            },
        ]

        class MockNeo4JRunData(object):
            @staticmethod
            def data():
                return expected_flowgraphs

        mock_neo4j_db.run.side_effect = lambda _: MockNeo4JRunData()

        returned_seqs = self.dataset_processing.extract_features_worker({"id": None})

        expected_seqs = {
            "path_id_0": [
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_01",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                },
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_02",
                    "iorder": ["var01"],
                    "inflow": [],
                    "outflow": [8],
                },
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_03",
                    "iorder": ["var02", "var01"],
                    "inflow": [],
                    "outflow": [],
                },
            ],
            "path_id_1": [
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_04",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [8],
                },
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_05",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                },
            ],
            "path_id_2": [
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_06",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                }
            ],
        }

        self.assertDictEqual(expected_seqs, returned_seqs)


class FeatureExtractorGetEntrypointList(InterprocTestCase):
    @patch("bugfinder.processing.neo4j.Neo4J3Processing.neo4j_db")
    def test_neo4j_db_run_is_called(self, mock_neo4j_db):
        self.dataset_processing._get_entrypoint_list()
        self.assertTrue(mock_neo4j_db.run.called)

    @patch("bugfinder.processing.neo4j.Neo4J3Processing.neo4j_db")
    def test_entrypoint_list_is_correctly_formatted(self, mock_neo4j_db):
        expected_entrypoints = [{"id": 0, "filepath": "/path", "name": "TestCase_01"}]

        class MockNeo4JRunData(object):
            @staticmethod
            def data():
                return expected_entrypoints

        mock_neo4j_db.run.side_effect = lambda _: MockNeo4JRunData()
        returned_entrypoints = self.dataset_processing._get_entrypoint_list()
        self.assertListEqual(returned_entrypoints, expected_entrypoints)


class FeatureExtractorExtractFeatures(InterprocTestCase):
    @patch("bugfinder.processing.neo4j.Neo4J3Processing.neo4j_db")
    def test_neo4j_db_run_is_called(self, mock_neo4j_db):
        self.dataset_processing.get_flowgraph_list_for_entrypoint({"id": None})
        self.assertTrue(mock_neo4j_db.run.called)

    @patch("bugfinder.processing.neo4j.Neo4J3Processing.neo4j_db")
    def test_features_are_correctly_formatted(self, mock_neo4j_db):
        class MockNeo4JRunDataEntrypoints(object):
            @staticmethod
            def data():
                expected_entrypoints = [
                    {"id": 1, "filepath": "/path1", "name": "TestCase_01"},
                    {"id": 2, "filepath": "/path2", "name": "TestCase_02"},
                ]
                return expected_entrypoints

        expected_flowgraphs1 = [
            {
                "path_id": "path_id_0",
                "sink": False,
                "id": 123,
                "ast": "ast_01",
                "iorder": [],
                "inflow": [],
                "outflow": [4],
            },
            {
                "path_id": "path_id_0",
                "sink": False,
                "id": 123,
                "ast": "ast_02",
                "iorder": ["var01"],
                "inflow": [["ast_01", "v01", 4]],
                "outflow": [8],
            },
            {
                "path_id": "path_id_0",
                "sink": True,
                "id": 123,
                "ast": "ast_03",
                "iorder": ["var02", "var01"],
                "inflow": [["ast_01", "v01", 0], ["ast_02", "v02", 8]],
                "outflow": [],
            },
            {
                "path_id": "path_id_1",
                "sink": False,
                "id": 123,
                "ast": "ast_04",
                "iorder": [],
                "inflow": [],
                "outflow": [8],
            },
            {
                "path_id": "path_id_1",
                "sink": True,
                "id": 123,
                "ast": "ast_05",
                "iorder": [],
                "inflow": [],
                "outflow": [4],
            },
            {
                "path_id": "path_id_2",
                "sink": True,
                "id": 123,
                "ast": "ast_06",
                "iorder": [],
                "inflow": [],
                "outflow": [4],
            },
        ]
        expected_flowgraphs2 = [
            {
                "path_id": "path_id_3",
                "sink": False,
                "id": 123,
                "ast": "ast_01",
                "iorder": [],
                "inflow": [],
                "outflow": [4],
            },
            {
                "path_id": "path_id_3",
                "sink": False,
                "id": 123,
                "ast": "ast_02",
                "iorder": ["var01"],
                "inflow": [["ast_01", "v01", 4]],
                "outflow": [8],
            },
            {
                "path_id": "path_id_3",
                "sink": True,
                "id": 123,
                "ast": "ast_03",
                "iorder": ["var02", "var01"],
                "inflow": [["ast_01", "v01", 0], ["ast_02", "v02", 8]],
                "outflow": [],
            },
            {
                "path_id": "path_id_4",
                "sink": False,
                "id": 123,
                "ast": "ast_04",
                "iorder": [],
                "inflow": [],
                "outflow": [8],
            },
            {
                "path_id": "path_id_4",
                "sink": True,
                "id": 123,
                "ast": "ast_05",
                "iorder": [],
                "inflow": [],
                "outflow": [4],
            },
            {
                "path_id": "path_id_5",
                "sink": True,
                "id": 123,
                "ast": "ast_06",
                "iorder": [],
                "inflow": [],
                "outflow": [4],
            },
        ]

        class MockNeo4JRunDataFlowGraphs1(object):
            @staticmethod
            def data():
                return expected_flowgraphs1

        class MockNeo4JRunDataFlowGraphs2(object):
            @staticmethod
            def data():
                return expected_flowgraphs2

        mock_neo4j_db.run.side_effect = [
            MockNeo4JRunDataEntrypoints(),
            MockNeo4JRunDataFlowGraphs1(),
            MockNeo4JRunDataFlowGraphs2(),
        ]

        expected_features = {
            "path_id_0": [
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_01",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                },
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_02",
                    "iorder": ["var01"],
                    "inflow": [],
                    "outflow": [8],
                },
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_03",
                    "iorder": ["var02", "var01"],
                    "inflow": [],
                    "outflow": [],
                },
            ],
            "path_id_1": [
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_04",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [8],
                },
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_05",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                },
            ],
            "path_id_2": [
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_06",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                }
            ],
            "path_id_3": [
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_01",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                },
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_02",
                    "iorder": ["var01"],
                    "inflow": [],
                    "outflow": [8],
                },
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_03",
                    "iorder": ["var02", "var01"],
                    "inflow": [],
                    "outflow": [],
                },
            ],
            "path_id_4": [
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_04",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [8],
                },
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_05",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                },
            ],
            "path_id_5": [
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_06",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                }
            ],
        }

        returned_features = self.dataset_processing.extract_features()
        self.assertDictEqual(returned_features, expected_features)


class FeatureExtractorCheckExtractionInputs(InterprocTestCase):
    def test_extraction_inputs(self):
        import os

        self.dataset_processing.dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing.dataset.feats_dir = "/tmp/TEST"
        returned_path = self.dataset_processing.check_extraction_inputs()
        self.assertEqual(
            returned_path,
            os.path.join(
                self.dataset_processing.dataset.feats_dir, "interproc-features.json"
            ),
        )
        self.assertTrue(os.path.isdir(self.dataset_processing.dataset.feats_dir))
        os.rmdir(self.dataset_processing.dataset.feats_dir)


class FeatureExtractorWriteExtractionOutputs(InterprocTestCase):
    def test_extraction_inputs(self):
        import os, json

        expected_features = {
            "path_id_0": [
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_01",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                },
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_02",
                    "iorder": ["var01"],
                    "inflow": [],
                    "outflow": [8],
                },
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_03",
                    "iorder": ["var02", "var01"],
                    "inflow": [],
                    "outflow": [],
                },
            ],
            "path_id_1": [
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_04",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [8],
                },
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_05",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                },
            ],
            "path_id_2": [
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_06",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                }
            ],
            "path_id_3": [
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_01",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                },
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_02",
                    "iorder": ["var01"],
                    "inflow": [],
                    "outflow": [8],
                },
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_03",
                    "iorder": ["var02", "var01"],
                    "inflow": [],
                    "outflow": [],
                },
            ],
            "path_id_4": [
                {
                    "sink": False,
                    "id": 123,
                    "ast": "ast_04",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [8],
                },
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_05",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                },
            ],
            "path_id_5": [
                {
                    "sink": True,
                    "id": 123,
                    "ast": "ast_06",
                    "iorder": [],
                    "inflow": [],
                    "outflow": [4],
                }
            ],
        }
        expected_feature_map = {
            "ast_01": [0],
            "ast_02": [0],
            "ast_03": [0],
            "ast_04": [0],
            "ast_05": [0],
            "ast_06": [0],
        }

        self.dataset_processing.dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing.dataset.feats_dir = "/tmp/TEST"
        self.dataset_processing.check_extraction_inputs()
        self.dataset_processing.write_extraction_outputs(expected_features)
        feature_file = os.path.join(
            self.dataset_processing.dataset.feats_dir, "interproc-features.json"
        )
        featmap_file = os.path.join(
            self.dataset_processing.dataset.feats_dir, "interproc-feature-map.json"
        )
        with open(feature_file, "r") as f:
            self.assertDictEqual(json.load(f), expected_features)
        with open(featmap_file, "r") as f:
            self.assertDictEqual(json.load(f), expected_feature_map)
        os.remove(feature_file)
        os.remove(featmap_file)
        os.rmdir(self.dataset_processing.dataset.feats_dir)
