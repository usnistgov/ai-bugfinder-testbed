from os import remove
from os.path import join, basename, dirname
from unittest import TestCase
from unittest.mock import patch, Mock

from bugfinder import settings
from bugfinder.dataset import CWEClassificationDataset
from bugfinder.features import GraphFeatureExtractor, FlowGraphFeatureExtractor
from bugfinder.settings import ROOT_DIR
from tests import patch_paths

import re


class MockGraphFeatureExtractor(GraphFeatureExtractor):
    def map_features(self):
        pass

    def configure_container(self):
        pass

    def extract_features(self):
        pass


class MockFlowGraphFeatureExtractor(FlowGraphFeatureExtractor):
    def get_flowgraph_list_for_entrypoint(self, entrypoint):
        pass

    def get_label_from_flowgraph(self, flowgraph):
        pass

    def get_flowgraph_count(self, flowgraph):
        pass

    def configure_container(self):
        pass


class GraphFeatureExtractorGetEntrypointList(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = MockGraphFeatureExtractor(None)

    @patch("bugfinder.neo4j.Neo4J3Processing.neo4j_db")
    def test_entrypoint_list_contains_all_info(self, mock_neo4j_db):
        class MockNeo4JRunData(object):
            def __init__(self, *args, **kwargs):
                self.call_nb = 0
                super().__init__()

            def data(self):
                self.call_nb += 1

                if self.call_nb == 1:
                    return [
                        {
                            "id": 0,
                            "filepath": "mock_testcase_a",
                            "mock_key_0": "mock_value_0",
                        },
                        {
                            "id": 1,
                            "filepath": "mock_testcase_b",
                            "mock_key_0": "mock_value_1",
                        },
                    ]
                else:
                    return [{"call_nb": self.call_nb}]

        mock_neo4j_db_run_data = MockNeo4JRunData()
        mock_neo4j_db.run.side_effect = [
            mock_neo4j_db_run_data,
            mock_neo4j_db_run_data,
            mock_neo4j_db_run_data,
        ]

        expected_result = [
            {"filepath": "mock_testcase_a", "call_nb": 2},
            {"filepath": "mock_testcase_b", "call_nb": 3},
        ]

        self.assertListEqual(
            self.dataset_processing._get_entrypoint_list(), expected_result
        )

    @patch("bugfinder.neo4j.Neo4J3Processing.neo4j_db")
    def test_empty_entrypoint_list_returns_empty_list(self, mock_neo4j_db):
        class MockNeo4JRunData(object):
            def __init__(self, *args, **kwargs):
                self.call_nb = 0
                super().__init__()

            @staticmethod
            def data():
                return []

        mock_neo4j_db.run = MockNeo4JRunData

        self.assertListEqual(self.dataset_processing._get_entrypoint_list(), [])


class GraphFeatureExtractorCreateFeatureMapFile(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.dataset.LOGGER", "bugfinder.features.LOGGER"])

        self.dataset_path = "./tests/fixtures/dataset01"
        dataset = CWEClassificationDataset(self.dataset_path)
        self.dataset_processing = MockGraphFeatureExtractor(dataset)

    def tearDown(self) -> None:
        try:
            remove(join(self.dataset_path, settings.SUMMARY_FILE))
        except FileNotFoundError:
            pass  # Ignore FileNotFound errors

    @patch("bugfinder.features.mkdir")
    def test_feature_map_file_created_if_arg_none(self, mock_mkdir):
        mock_mkdir.return_value = None
        self.dataset_processing._create_feature_map_file(None)

        self.assertEqual(
            self.dataset_processing.feature_map_filepath,
            join(
                ROOT_DIR,
                "feature_maps",
                "%s.bin" % basename(dirname(self.dataset_processing.dataset.path)),
            ),
        )

    def test_feature_map_file_assigned_if_arg_not_none(self):
        expected_filepath = "mock_path"
        self.dataset_processing._create_feature_map_file(expected_filepath)

        self.assertEqual(
            self.dataset_processing.feature_map_filepath, expected_filepath
        )


class GraphFeatureExtractorExecute(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = MockGraphFeatureExtractor(None)

    @patch("bugfinder.neo4j.Neo4J3Processing.execute")
    @patch(
        "tests.features.test_unit.MockGraphFeatureExtractor._create_feature_map_file"
    )
    def test_create_feature_map_file_called(
        self, mock_create_feature_map_file, mock_execute
    ):
        mock_execute.return_value = None

        self.dataset_processing.execute()

        self.assertTrue(mock_create_feature_map_file.called)

    @patch("bugfinder.neo4j.Neo4J3Processing.execute")
    @patch(
        "tests.features.test_unit.MockGraphFeatureExtractor._create_feature_map_file"
    )
    def test_need_map_features_init(self, mock_create_feature_map_file, mock_execute):
        mock_create_feature_map_file.return_value = None
        mock_execute.return_value = None
        expected_result = not self.dataset_processing.need_map_features

        self.dataset_processing.execute(need_map_features=expected_result)

        self.assertEqual(self.dataset_processing.need_map_features, expected_result)

    @patch("bugfinder.neo4j.Neo4J3Processing.execute")
    @patch(
        "tests.features.test_unit.MockGraphFeatureExtractor._create_feature_map_file"
    )
    def test_parent_execute_called(self, mock_create_feature_map_file, mock_execute):
        mock_create_feature_map_file.return_value = None
        mock_execute.return_value = None

        self.dataset_processing.execute()

        self.assertTrue(mock_execute.called)


class GraphFeatureExtractorSendCommands(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.LOGGER"])

        self.dataset_processing = MockGraphFeatureExtractor(None)

    @patch("bugfinder.neo4j.Neo4J3Processing.send_commands")
    @patch("tests.features.test_unit.GraphFeatureExtractor.check_extraction_inputs")
    @patch("tests.features.test_unit.MockGraphFeatureExtractor.extract_features")
    @patch("tests.features.test_unit.GraphFeatureExtractor.write_extraction_outputs")
    def test_parent_send_command_called(
        self,
        mock_write_extraction_outputs,
        mock_extract_features,
        mock_check_extraction_inputs,
        mock_send_commands,
    ):
        mock_write_extraction_outputs.return_value = None
        mock_extract_features.return_value = None
        mock_check_extraction_inputs.return_value = None
        mock_send_commands.return_value = None
        self.dataset_processing.send_commands()

        self.assertTrue(mock_send_commands.called)

    @patch("bugfinder.neo4j.Neo4J3Processing.send_commands")
    @patch("tests.features.test_unit.MockGraphFeatureExtractor.map_features")
    @patch("tests.features.test_unit.GraphFeatureExtractor.save_labels_to_feature_map")
    def test_map_features_called_if_need_map_feature(
        self, mock_save_labels_to_feature_map, mock_map_features, mock_send_commands
    ):
        mock_save_labels_to_feature_map.return_value = None
        mock_map_features.return_value = None
        mock_send_commands.return_value = None

        self.dataset_processing.need_map_features = True
        self.dataset_processing.send_commands()

        self.assertTrue(mock_map_features.called)

    @patch("bugfinder.neo4j.Neo4J3Processing.send_commands")
    @patch("tests.features.test_unit.MockGraphFeatureExtractor.map_features")
    @patch("tests.features.test_unit.GraphFeatureExtractor.save_labels_to_feature_map")
    def test_save_labels_called_if_need_map_feature(
        self, mock_save_labels_to_feature_map, mock_map_features, mock_send_commands
    ):
        mock_save_labels_to_feature_map.return_value = None
        mock_map_features.return_value = None
        mock_send_commands.return_value = None

        self.dataset_processing.need_map_features = True
        self.dataset_processing.send_commands()

        self.assertTrue(mock_save_labels_to_feature_map.called)

    @patch("bugfinder.neo4j.Neo4J3Processing.send_commands")
    @patch("tests.features.test_unit.GraphFeatureExtractor.check_extraction_inputs")
    @patch("tests.features.test_unit.MockGraphFeatureExtractor.extract_features")
    @patch("tests.features.test_unit.GraphFeatureExtractor.write_extraction_outputs")
    def test_check_extraction_inputs_called_if_not_need_map_feature(
        self,
        mock_write_extraction_outputs,
        mock_extract_features,
        mock_check_extraction_inputs,
        mock_send_commands,
    ):
        mock_write_extraction_outputs.return_value = None
        mock_extract_features.return_value = None
        mock_check_extraction_inputs.return_value = None
        mock_send_commands.return_value = None
        self.dataset_processing.send_commands()

        self.assertTrue(mock_check_extraction_inputs.called)

    @patch("bugfinder.neo4j.Neo4J3Processing.send_commands")
    @patch("tests.features.test_unit.GraphFeatureExtractor.check_extraction_inputs")
    @patch("tests.features.test_unit.MockGraphFeatureExtractor.extract_features")
    @patch("tests.features.test_unit.GraphFeatureExtractor.write_extraction_outputs")
    def test_extract_features_called_if_not_need_map_feature(
        self,
        mock_write_extraction_outputs,
        mock_extract_features,
        mock_check_extraction_inputs,
        mock_send_commands,
    ):
        mock_write_extraction_outputs.return_value = None
        mock_extract_features.return_value = None
        mock_check_extraction_inputs.return_value = None
        mock_send_commands.return_value = None
        self.dataset_processing.send_commands()

        self.assertTrue(mock_extract_features.called)

    @patch("bugfinder.neo4j.Neo4J3Processing.send_commands")
    @patch("tests.features.test_unit.GraphFeatureExtractor.check_extraction_inputs")
    @patch("tests.features.test_unit.MockGraphFeatureExtractor.extract_features")
    @patch("tests.features.test_unit.GraphFeatureExtractor.write_extraction_outputs")
    def test_write_output_called_if_not_need_map_feature(
        self,
        mock_write_extraction_outputs,
        mock_extract_features,
        mock_check_extraction_inputs,
        mock_send_commands,
    ):
        mock_write_extraction_outputs.return_value = None
        mock_extract_features.return_value = None
        mock_check_extraction_inputs.return_value = None
        mock_send_commands.return_value = None
        self.dataset_processing.send_commands()

        self.assertTrue(mock_write_extraction_outputs.called)


class GraphFeatureExtractorCheckExtractionInputs(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.dataset.join",
                "bugfinder.dataset.listdir",
                "bugfinder.dataset.pd.read_csv",
                "bugfinder.dataset.CWEClassificationDataset._validate_features",
                "bugfinder.dataset.LOGGER",
            ],
        )

        self.dataset = Mock(spec=CWEClassificationDataset)
        self.dataset.feats_dir = "mock_feats_dir"
        self.dataset_processing = MockGraphFeatureExtractor(self.dataset)

    @patch("bugfinder.features.exists")
    @patch("bugfinder.features.mkdir")
    @patch("bugfinder.features.join")
    def test_feature_dir_is_created_if_needed(self, mock_join, mock_mkdir, mock_exists):
        mock_join.return_value = None
        mock_mkdir.return_value = None
        mock_exists.return_value = False

        self.dataset_processing.check_extraction_inputs()

        self.assertTrue(mock_mkdir.called)

    @patch("bugfinder.features.exists")
    @patch("bugfinder.features.join")
    def test_return_correct_file_path(self, mock_join, mock_exists):
        mock_join.return_value = None
        mock_exists.return_value = True

        self.dataset_processing.check_extraction_inputs()

        mock_join.assert_called_with(self.dataset.feats_dir, "features.csv")


class GraphFeatureExtractorWriteExtractionOutputs(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.dataset.join",
                "bugfinder.dataset.listdir",
                "bugfinder.dataset.pd.read_csv",
                "bugfinder.dataset.CWEClassificationDataset._validate_features",
                "bugfinder.features.join",
                "bugfinder.features.open",
                "bugfinder.dataset.LOGGER",
            ],
        )

        self.dataset = Mock(spec=CWEClassificationDataset)
        self.dataset.feats_dir = "mock_feats_dir"
        self.dataset_processing = MockGraphFeatureExtractor(self.dataset)

    @patch("tests.features.test_unit.GraphFeatureExtractor.get_labels_from_feature_map")
    def test_get_labels_from_feature_map_called(self, mock_get_labels_from_feature_map):
        mock_get_labels_from_feature_map.return_value = []
        mock_features = [[True, "mock_name"]]

        self.dataset_processing.write_extraction_outputs(mock_features)

        self.assertTrue(mock_get_labels_from_feature_map.called)

    @patch("tests.features.test_unit.GraphFeatureExtractor.get_labels_from_feature_map")
    def test_missing_label_raises_index_error(self, mock_get_labels_from_feature_map):
        mock_get_labels_from_feature_map.return_value = [0]
        mock_features = [[True, "mock_name"]]

        with self.assertRaises(IndexError):
            self.dataset_processing.write_extraction_outputs(mock_features)


class GraphFeatureExtractorSaveLabelsToFeatursMap(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.dataset.join",
                "bugfinder.dataset.listdir",
                "bugfinder.dataset.pd.read_csv",
                "bugfinder.dataset.CWEClassificationDataset._validate_features",
                "bugfinder.features.open",
                "bugfinder.features.join",
                "bugfinder.dataset.LOGGER",
                "bugfinder.features.LOGGER",
            ],
        )

        self.dataset = Mock(spec=CWEClassificationDataset)
        self.dataset_processing = MockGraphFeatureExtractor(self.dataset)

    @patch("tests.features.test_unit.GraphFeatureExtractor.get_labels_from_feature_map")
    def test_get_labels_called(self, mock_get_labels_from_feature_map):
        mock_get_labels_from_feature_map.return_value = []

        self.dataset_processing.save_labels_to_feature_map([])

        self.assertTrue(mock_get_labels_from_feature_map.called)

    @patch("tests.features.test_unit.GraphFeatureExtractor.get_labels_from_feature_map")
    @patch("bugfinder.features.pickle")
    def test_same_labels_are_not_overwritten(
        self, mock_pickle, mock_get_labels_from_feature_map
    ):
        mock_get_labels_from_feature_map.return_value = ["feature"]

        self.dataset_processing.save_labels_to_feature_map(["feature"])

        self.assertFalse(mock_pickle.dump.called)

    @patch("tests.features.test_unit.GraphFeatureExtractor.get_labels_from_feature_map")
    @patch("bugfinder.features.pickle")
    def test_extra_labels_are_overwritten(
        self, mock_pickle, mock_get_labels_from_feature_map
    ):
        mock_get_labels_from_feature_map.return_value = ["feature_1"]

        self.dataset_processing.save_labels_to_feature_map(["feature_1", "feature_2"])

        self.assertTrue(mock_pickle.dump.called)


class GraphFeatureExtractorGetLabelsFromFeatursMap(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.dataset.join",
                "bugfinder.dataset.listdir",
                "bugfinder.dataset.pd.read_csv",
                "bugfinder.dataset.CWEClassificationDataset._validate_features",
                "bugfinder.features.join",
                "bugfinder.features.open",
                "bugfinder.dataset.LOGGER",
            ],
        )

        self.dataset = Mock(spec=CWEClassificationDataset)
        self.dataset_processing = MockGraphFeatureExtractor(self.dataset)

    @patch("bugfinder.features.exists")
    def test_non_existent_file_returns_empty_list(self, mock_exists):
        mock_exists.return_value = False

        returned_labels = self.dataset_processing.get_labels_from_feature_map()

        self.assertEqual(returned_labels, [])

    @patch("bugfinder.features.exists")
    @patch("bugfinder.features.pickle")
    def test_return_labels_from_file(self, mock_pickle, mock_exists):
        expected_labels = ["label_1", "label_2"]
        mock_pickle.load.return_value = expected_labels
        mock_exists.return_value = True

        returned_labels = self.dataset_processing.get_labels_from_feature_map()

        self.assertEqual(returned_labels, expected_labels)


class FlowGraphFeatureExtractorInitializeFeatures(TestCase):
    def setUp(self) -> None:
        dataset = Mock(spec=CWEClassificationDataset)
        dataset.classes = ["bad"]
        dataset_processing = MockFlowGraphFeatureExtractor(dataset)
        self.returned_features = dataset_processing.initialize_features(
            {"filepath": "/code/bad/entrypoint_name/entrypoint_file.c"},
            ["label1", "label2"],
        )

    def test_returns_list(self):
        self.assertEqual(type(self.returned_features), list)

    def test_returns_correct_data(self):
        self.assertEqual(self.returned_features, [0, 0, 0, "entrypoint_file.c"])


class FlowGraphFeatureExtractorFinalizeFeatures(TestCase):
    def setUp(self) -> None:
        dataset_processing = MockFlowGraphFeatureExtractor(None)
        self.features = [1, 2]
        self.returned_features = dataset_processing.finalize_features(
            self.features, ["label1", "label2"]
        )

    def test_returns_args(self):
        self.assertEqual(self.returned_features, self.features)


class FlowGraphFeatureExtractorExtractFeatures(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.LOGGER"])

        self.dataset_processing = MockFlowGraphFeatureExtractor(None)

    @patch("bugfinder.features.GraphFeatureExtractor.get_labels_from_feature_map")
    @patch("bugfinder.features.GraphFeatureExtractor._get_entrypoint_list")
    def test_get_label_from_feature_map_is_called(
        self, mock_get_entrypoint_list, mock_get_labels_from_feature_map
    ):
        mock_get_entrypoint_list.return_value = []
        self.dataset_processing.extract_features()

        self.assertTrue(mock_get_labels_from_feature_map.called)

    @patch("bugfinder.features.GraphFeatureExtractor.get_labels_from_feature_map")
    @patch("bugfinder.features.GraphFeatureExtractor._get_entrypoint_list")
    def test_get_entrypoint_list_is_called(
        self, mock_get_entrypoint_list, mock_get_labels_from_feature_map
    ):
        mock_get_entrypoint_list.return_value = []
        mock_get_labels_from_feature_map.return_value = []
        self.dataset_processing.extract_features()

        self.assertTrue(mock_get_entrypoint_list.called)

    @patch("bugfinder.features.GraphFeatureExtractor.get_labels_from_feature_map")
    @patch("bugfinder.features.GraphFeatureExtractor._get_entrypoint_list")
    @patch("bugfinder.features.FlowGraphFeatureExtractor.initialize_features")
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_flowgraph_list_for_entrypoint"
    )
    @patch("bugfinder.features.FlowGraphFeatureExtractor.finalize_features")
    def test_initialize_features_is_called(
        self,
        mock_finalize_features,
        mock_get_flowgraph_list_for_entrypoint,
        mock_initialize_features,
        mock_get_entrypoint_list,
        mock_get_labels_from_feature_map,
    ):
        mock_finalize_features.return_value = None
        mock_get_flowgraph_list_for_entrypoint.return_value = []
        mock_initialize_features.return_value = []
        mock_get_entrypoint_list.return_value = ["entrypoint"]
        mock_get_labels_from_feature_map.return_value = []
        self.dataset_processing.extract_features()

        self.assertTrue(mock_initialize_features.called)

    @patch("bugfinder.features.GraphFeatureExtractor.get_labels_from_feature_map")
    @patch("bugfinder.features.GraphFeatureExtractor._get_entrypoint_list")
    @patch("bugfinder.features.FlowGraphFeatureExtractor.initialize_features")
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_flowgraph_list_for_entrypoint"
    )
    @patch("bugfinder.features.FlowGraphFeatureExtractor.finalize_features")
    def test_get_flowgraph_list_for_entrypoint_is_called(
        self,
        mock_finalize_features,
        mock_get_flowgraph_list_for_entrypoint,
        mock_initialize_features,
        mock_get_entrypoint_list,
        mock_get_labels_from_feature_map,
    ):
        mock_finalize_features.return_value = None
        mock_get_flowgraph_list_for_entrypoint.return_value = []
        mock_initialize_features.return_value = []
        mock_get_entrypoint_list.return_value = ["entrypoint"]
        mock_get_labels_from_feature_map.return_value = []
        self.dataset_processing.extract_features()

        self.assertTrue(mock_get_flowgraph_list_for_entrypoint.called)

    @patch("bugfinder.features.GraphFeatureExtractor.get_labels_from_feature_map")
    @patch("bugfinder.features.GraphFeatureExtractor._get_entrypoint_list")
    @patch("bugfinder.features.FlowGraphFeatureExtractor.initialize_features")
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_flowgraph_list_for_entrypoint"
    )
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_label_from_flowgraph"
    )
    @patch("bugfinder.features.FlowGraphFeatureExtractor.finalize_features")
    def test_get_label_from_flowgraph_is_called(
        self,
        mock_finalize_features,
        mock_get_label_from_flowgraph,
        mock_get_flowgraph_list_for_entrypoint,
        mock_initialize_features,
        mock_get_entrypoint_list,
        mock_get_labels_from_feature_map,
    ):
        mock_finalize_features.return_value = None
        mock_get_label_from_flowgraph.return_value = None
        mock_get_flowgraph_list_for_entrypoint.return_value = ["mock_flowgraph"]
        mock_initialize_features.return_value = []
        mock_get_entrypoint_list.return_value = ["entrypoint"]
        mock_get_labels_from_feature_map.return_value = []
        self.dataset_processing.extract_features()

        self.assertTrue(mock_get_label_from_flowgraph.called)

    @patch("bugfinder.features.GraphFeatureExtractor.get_labels_from_feature_map")
    @patch("bugfinder.features.GraphFeatureExtractor._get_entrypoint_list")
    @patch("bugfinder.features.FlowGraphFeatureExtractor.initialize_features")
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_flowgraph_list_for_entrypoint"
    )
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_label_from_flowgraph"
    )
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor" ".get_flowgraph_count"
    )
    @patch("bugfinder.features.FlowGraphFeatureExtractor.finalize_features")
    def test_get_flowgraph_count_is_called(
        self,
        mock_finalize_features,
        mock_get_flowgraph_count,
        mock_get_label_from_flowgraph,
        mock_get_flowgraph_list_for_entrypoint,
        mock_initialize_features,
        mock_get_entrypoint_list,
        mock_get_labels_from_feature_map,
    ):
        mock_finalize_features.return_value = None
        mock_get_flowgraph_count.return_value = 0
        mock_get_label_from_flowgraph.return_value = "mock_label"
        mock_get_flowgraph_list_for_entrypoint.return_value = ["mock_flowgraph"]
        mock_initialize_features.return_value = [0]
        mock_get_entrypoint_list.return_value = ["entrypoint"]
        mock_get_labels_from_feature_map.return_value = ["mock_label"]
        self.dataset_processing.extract_features()

        self.assertTrue(mock_get_flowgraph_count.called)

    @patch("bugfinder.features.GraphFeatureExtractor.get_labels_from_feature_map")
    @patch("bugfinder.features.GraphFeatureExtractor._get_entrypoint_list")
    @patch("bugfinder.features.FlowGraphFeatureExtractor.initialize_features")
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_flowgraph_list_for_entrypoint"
    )
    @patch("bugfinder.features.FlowGraphFeatureExtractor.finalize_features")
    def test_finalize_features_is_called(
        self,
        mock_finalize_features,
        mock_get_flowgraph_list_for_entrypoint,
        mock_initialize_features,
        mock_get_entrypoint_list,
        mock_get_labels_from_feature_map,
    ):
        mock_finalize_features.return_value = None
        mock_get_flowgraph_list_for_entrypoint.return_value = []
        mock_initialize_features.return_value = []
        mock_get_entrypoint_list.return_value = ["entrypoint"]
        mock_get_labels_from_feature_map.return_value = []
        self.dataset_processing.extract_features()

        self.assertTrue(mock_finalize_features.called)

    @patch("bugfinder.features.GraphFeatureExtractor.get_labels_from_feature_map")
    @patch("bugfinder.features.GraphFeatureExtractor._get_entrypoint_list")
    @patch("bugfinder.features.FlowGraphFeatureExtractor.initialize_features")
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_flowgraph_list_for_entrypoint"
    )
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_label_from_flowgraph"
    )
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor" ".get_flowgraph_count"
    )
    def test_unknown_labels_are_ignored(
        self,
        mock_get_flowgraph_count,
        mock_get_label_from_flowgraph,
        mock_get_flowgraph_list_for_entrypoint,
        mock_initialize_features,
        mock_get_entrypoint_list,
        mock_get_labels_from_feature_map,
    ):
        mock_get_flowgraph_count.return_value = 2
        mock_get_label_from_flowgraph.side_effect = lambda name: re.sub(
            "flowgraph", "label", name
        )
        mock_get_flowgraph_list_for_entrypoint.return_value = [
            "mock_flowgraph_1",
            "mock_flowgraph_2",
        ]
        mock_initialize_features.return_value = [0]
        mock_get_entrypoint_list.return_value = ["entrypoint"]
        mock_get_labels_from_feature_map.return_value = ["mock_label_1"]

        returned_features = self.dataset_processing.extract_features()

        self.assertEqual(returned_features, [[2]])


class FlowGraphFeatureExtractorMapFeatures(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.LOGGER"])

        self.dataset_processing = MockFlowGraphFeatureExtractor(None)

    @patch("bugfinder.features.GraphFeatureExtractor._get_entrypoint_list")
    def test_get_entrypoint_list_is_called(self, mock_get_entrypoint_list):
        mock_get_entrypoint_list.return_value = []

        self.dataset_processing.map_features()

        self.assertTrue(mock_get_entrypoint_list.called)

    @patch("bugfinder.features.GraphFeatureExtractor._get_entrypoint_list")
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_flowgraph_list_for_entrypoint"
    )
    def test_get_flowgraph_list_for_entrypoint_is_called(
        self, mock_get_flowgraph_list_for_entrypoint, mock_get_entrypoint_list
    ):
        mock_get_flowgraph_list_for_entrypoint.return_value = []
        mock_get_entrypoint_list.return_value = [None]

        self.dataset_processing.map_features()

        self.assertTrue(mock_get_flowgraph_list_for_entrypoint.called)

    @patch("bugfinder.features.GraphFeatureExtractor._get_entrypoint_list")
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_flowgraph_list_for_entrypoint"
    )
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_label_from_flowgraph"
    )
    def test_get_label_from_flowgraph_is_called(
        self,
        mock_get_label_from_flowgraph,
        mock_get_flowgraph_list_for_entrypoint,
        mock_get_entrypoint_list,
    ):
        mock_get_label_from_flowgraph.return_value = "label"
        mock_get_flowgraph_list_for_entrypoint.return_value = [None]
        mock_get_entrypoint_list.return_value = [None]

        self.dataset_processing.map_features()

        self.assertTrue(mock_get_label_from_flowgraph.called)

    @patch("bugfinder.features.GraphFeatureExtractor._get_entrypoint_list")
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_flowgraph_list_for_entrypoint"
    )
    @patch(
        "tests.features.test_unit.MockFlowGraphFeatureExtractor"
        ".get_label_from_flowgraph"
    )
    def test_duplicate_label_appear_only_once(
        self,
        mock_get_label_from_flowgraph,
        mock_get_flowgraph_list_for_entrypoint,
        mock_get_entrypoint_list,
    ):
        mock_get_label_from_flowgraph.return_value = "label"
        mock_get_flowgraph_list_for_entrypoint.return_value = [None, None, None]
        mock_get_entrypoint_list.return_value = [None, None]

        expected_list = ["label"]

        returned_list = self.dataset_processing.map_features()

        self.assertEqual(returned_list, expected_list)
