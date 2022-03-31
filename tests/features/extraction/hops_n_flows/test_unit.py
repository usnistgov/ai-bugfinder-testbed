from unittest import TestCase
from unittest.mock import Mock, patch

from bugfinder.dataset import CodeWeaknessClassificationDataset
from bugfinder.features.extraction.hops_n_flows import (
    FeatureExtractor as HopsNFlowsExtractor,
)
from tests import patch_paths


class TestFeatureExtractorConfigureContainer(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.features.extraction.hops_n_flows.LOGGER",
                "bugfinder.features.extraction.LOGGER",
                "bugfinder.dataset.processing.LOGGER",
            ],
        )

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        dataset.ops_queue = list()

        self.dataset_processing = HopsNFlowsExtractor(dataset)

    @patch(
        "bugfinder.features.extraction.hops_n_flows.FlowGraphFeatureExtractor"
        ".configure_container"
    )
    def test_super_configure_container_called(self, mock_super_configure_container):
        self.dataset_processing.configure_container()
        self.assertTrue(mock_super_configure_container.called)


class TestFeatureExtractorExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.features.extraction.hops_n_flows.FlowGraphFeatureExtractor"
                ".execute",
                "bugfinder.features.extraction.hops_n_flows.LOGGER",
                "bugfinder.features.extraction.LOGGER",
                "bugfinder.dataset.processing.LOGGER",
            ],
        )

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        dataset.ops_queue = list()

        self.dataset_processing = HopsNFlowsExtractor(dataset)

    def test_no_flows_mean_all_flows(self):
        original_flows = self.dataset_processing.flows
        self.dataset_processing.execute()

        self.assertEqual(self.dataset_processing.flows, original_flows)

    def test_specific_flows_overwrite_all_flows(self):
        original_flows = self.dataset_processing.flows
        self.dataset_processing.execute(flows=["FLOWS_TO"])

        self.assertNotEqual(self.dataset_processing.flows, original_flows)

    def test_specific_flows_works(self):
        input_flows = ["FLOWS_TO"]
        self.dataset_processing.execute(flows=input_flows)

        self.assertEqual(self.dataset_processing.flows, input_flows)

    @patch("bugfinder.features.extraction.hops_n_flows.exit")
    def test_negative_min_hop_fails(self, mock_exit):
        self.dataset_processing.execute(min_hops=-1)
        self.assertTrue(mock_exit.called)

    @patch("bugfinder.features.extraction.hops_n_flows.exit")
    def test_max_hops_gt_min_hops_fails(self, mock_exit):
        self.dataset_processing.execute(min_hops=5, max_hops=2)
        self.assertTrue(mock_exit.called)

    @patch(
        "bugfinder.features.extraction.hops_n_flows.FlowGraphFeatureExtractor"
        ".execute"
    )
    def test_super_execute_called(self, mock_super_execute):
        self.dataset_processing.execute()
        self.assertTrue(mock_super_execute.called)


class TestFeatureExtractorGetFlowgraphListForEntrypoint(TestCase):
    class MockNeo4JRunData:
        class MockNode:
            def __init__(self, identity, labels):
                self.identity = identity
                self.labels = labels

            def has_label(self, label):
                return label in self.labels

            def __getitem__(self, item):
                return self.identity

        class MockRel:
            def __init__(self, start_node, end_node, identity):
                self.start_node = start_node
                self.end_node = end_node
                self.identity = identity

        nodes = {
            "a": MockNode("a", ["UpstreamNode"]),
            "b": MockNode("b", ["UpstreamNode", "DownstreamNode"]),
            "c": MockNode("c", ["DownstreamNode"]),
            "d": MockNode("d", ["DownstreamNode"]),
        }
        rels = [
            MockRel(nodes["a"], nodes["b"], "r1"),
            MockRel(nodes["b"], nodes["c"], "r2"),
            MockRel(nodes["a"], nodes["d"], "r3"),
        ]

        def __init__(self, data_return_value=None):
            self.data_return_value = data_return_value

        def data(self):
            return (
                [{"nodes": self.nodes.values(), "relationships": self.rels}]
                if self.data_return_value is None
                else self.data_return_value
            )

    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.features.extraction.hops_n_flows.LOGGER",
                "bugfinder.features.extraction.LOGGER",
                "bugfinder.dataset.processing.LOGGER",
            ],
        )

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        dataset.ops_queue = list()

        self.dataset_processing = HopsNFlowsExtractor(dataset)
        self.dataset_processing.flows = ["MockRel"]

    @patch("bugfinder.features.extraction.hops_n_flows.FeatureExtractor.neo4j_db")
    def test_neo4j_db_run_called(self, mock_neo4j_db):
        mock_neo4j_db.run.side_effect = [self.MockNeo4JRunData()]
        mock_entrypoint = {"entry_id": "mock_entry_id"}
        self.dataset_processing.get_flowgraph_list_for_entrypoint(mock_entrypoint)
        self.assertTrue(mock_neo4j_db.run.called)

    @patch("bugfinder.features.extraction.hops_n_flows.FeatureExtractor.neo4j_db")
    def test_zero_subgraph_returned_fails(self, mock_neo4j_db):
        mock_neo4j_db.run.side_effect = [self.MockNeo4JRunData(data_return_value=[])]
        mock_entrypoint = {"entry_id": "mock_entry_id"}
        with self.assertRaises(AssertionError):
            self.dataset_processing.get_flowgraph_list_for_entrypoint(mock_entrypoint)

    @patch("bugfinder.features.extraction.hops_n_flows.FeatureExtractor.neo4j_db")
    def test_several_subgraph_returned_fails(self, mock_neo4j_db):
        mock_neo4j_db.run.side_effect = [
            self.MockNeo4JRunData(data_return_value=["mock_graph_a", "mock_graph_b"])
        ]
        mock_entrypoint = {"entry_id": "mock_entry_id"}
        with self.assertRaises(AssertionError):
            self.dataset_processing.get_flowgraph_list_for_entrypoint(mock_entrypoint)

    @patch("bugfinder.features.extraction.hops_n_flows.FeatureExtractor.neo4j_db")
    def test_default_hops_returns_flowgraph_list(self, mock_neo4j_db):
        mock_neo4j_db.run.side_effect = [self.MockNeo4JRunData()]
        mock_entrypoint = {"entry_id": "mock_entry_id"}

        expected_result = [
            {"source": "a", "sink": "b", "flow": "MockRel", "count": 1},
            {"source": "b", "sink": "c", "flow": "MockRel", "count": 1},
            {"source": "a", "sink": "d", "flow": "MockRel", "count": 1},
            {"source": "a", "sink": "c", "flow": "MockRel", "count": 2},
        ]

        result = self.dataset_processing.get_flowgraph_list_for_entrypoint(
            mock_entrypoint
        )

        self.assertListEqual(result, expected_result)

    @patch("bugfinder.features.extraction.hops_n_flows.FeatureExtractor.neo4j_db")
    def test_max_hops_set_returns_flowgraph_list(self, mock_neo4j_db):
        mock_neo4j_db.run.side_effect = [self.MockNeo4JRunData()]
        mock_entrypoint = {"entry_id": "mock_entry_id"}
        self.dataset_processing.max_hops = 1

        expected_result = [
            {"source": "a", "sink": "b", "flow": "MockRel", "count": 1},
            {"source": "b", "sink": "c", "flow": "MockRel", "count": 1},
            {"source": "a", "sink": "d", "flow": "MockRel", "count": 1},
        ]

        result = self.dataset_processing.get_flowgraph_list_for_entrypoint(
            mock_entrypoint
        )

        self.assertListEqual(result, expected_result)

    @patch("bugfinder.features.extraction.hops_n_flows.FeatureExtractor.neo4j_db")
    def test_min_hops_set_returns_flowgraph_list(self, mock_neo4j_db):
        mock_neo4j_db.run.side_effect = [self.MockNeo4JRunData()]
        mock_entrypoint = {"entry_id": "mock_entry_id"}
        self.dataset_processing.min_hops = 2

        expected_result = [{"source": "a", "sink": "c", "flow": "MockRel", "count": 2}]

        result = self.dataset_processing.get_flowgraph_list_for_entrypoint(
            mock_entrypoint
        )

        self.assertListEqual(result, expected_result)


class TestFeatureExtractorGetFlowgraphCount(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.features.extraction.LOGGER",
                "bugfinder.dataset.processing.LOGGER",
            ],
        )

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        dataset.ops_queue = list()

        self.dataset_processing = HopsNFlowsExtractor(dataset)

    def test_returns_flowgraph_count(self):
        mock_flowgraph = {"source": "src", "flow": "FLOWS_TO", "sink": "snk"}
        expected_result = "src-FLOWS_TO-snk"

        result = self.dataset_processing.get_label_from_flowgraph(mock_flowgraph)

        self.assertEqual(result, expected_result)


class TestFeatureExtractorGetLabelFromFlowgraph(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.features.extraction.LOGGER",
                "bugfinder.dataset.processing.LOGGER",
            ],
        )

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        dataset.ops_queue = list()

        self.dataset_processing = HopsNFlowsExtractor(dataset)

    def test_retieve_correct_label(self):
        pass


class TestFeatureExtractorFinalizeFeatures(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.features.extraction.LOGGER",
                "bugfinder.dataset.processing.LOGGER",
            ],
        )

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        dataset.ops_queue = list()

        self.dataset_processing = HopsNFlowsExtractor(dataset)

    def test_normalized_features_are_properly_computed(self):
        input_features = [
            [4, 6, 3, 2, 6, 0, None, None],
            [4, 8, 5, 5, 5, 5, None, None],
            [3, 3, 11, 2, 4, 3, None, None],
            [3, 0, 0, 0, 0, 0, None, None],
        ]
        labels = [
            "a-CONTROLS-b",
            "a-CONTROLS-c",
            "a-FLOWS_TO-b",
            "a-REACHES-b",
            "a-REACHES-c",
            "a-REACHES-d",
        ]

        expected_features = [
            [0.4, 0.6, 1, 0.25, 0.75, 0, None, None],
            [1 / 3, 2 / 3, 1, 1 / 3, 1 / 3, 1 / 3, None, None],
            [0.5, 0.5, 1, 2 / 9, 4 / 9, 1 / 3, None, None],
            [1, 0, 0, 0, 0, 0, None, None],
        ]

        returned_features = self.dataset_processing.finalize_features(
            input_features, labels
        )

        self.assertListEqual(returned_features, expected_features)
