from unittest import TestCase
from unittest.mock import patch, Mock

from bugfinder.dataset import CWEClassificationDataset
from bugfinder.features.extraction.any_hop.single_flow import (
    FeatureExtractor as AnyHopSingleFlowsFeatureExtractor,
)
from tests import patch_paths


class FeatureExtractorConfigureContainer(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.extraction.LOGGER"])

        dataset = Mock(spec=CWEClassificationDataset)
        dataset.ops_queue = list()

        self.dataset_processing = AnyHopSingleFlowsFeatureExtractor(dataset)

    @patch("bugfinder.neo4j.Neo4J3Processing.configure_container")
    def test_container_name_is_correct(self, mock_configure_container):
        mock_configure_container.return_value = None
        expected_container_name = "fext-any-hop-single-flow"

        self.dataset_processing.configure_container()

        self.assertEqual(
            self.dataset_processing.container_name, expected_container_name
        )


class FeatureExtractorGetFlowgraphListForEntrypoint(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.extraction.LOGGER"])

        self.dataset_processing = AnyHopSingleFlowsFeatureExtractor(None)

    @patch("bugfinder.neo4j.Neo4J3Processing.neo4j_db")
    def test_neo4j_db_run_is_called(self, mock_neo4j_db):
        self.dataset_processing.get_flowgraph_list_for_entrypoint({"id": None})

        self.assertTrue(mock_neo4j_db.run.called)

    @patch("bugfinder.neo4j.Neo4J3Processing.neo4j_db")
    def test_flowgraph_list_is_correctly_formatted(self, mock_neo4j_db):
        class MockNeo4JRunData(object):
            @staticmethod
            def data():
                return [{"source": "source", "sink": "sink", "count": 1}]

        expected_flowgraphs = [
            {"source": "source", "sink": "sink", "count": 1, "flow": flow}
            for flow in self.dataset_processing.FLOWS
        ]

        mock_neo4j_db.run.side_effect = lambda _: MockNeo4JRunData()

        returned_flowgraphs = self.dataset_processing.get_flowgraph_list_for_entrypoint(
            {"id": None}
        )

        self.assertListEqual(returned_flowgraphs, expected_flowgraphs)


class FeatureExtractorGetFlowgraphCount(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.extraction.LOGGER"])

        self.dataset_processing = AnyHopSingleFlowsFeatureExtractor(None)

    def test_return_flowgraph_count(self):
        expected_count = 42
        returned_count = self.dataset_processing.get_flowgraph_count(
            {"count": expected_count}
        )

        self.assertEqual(returned_count, expected_count)


class FeatureExtractorGetLabelFromFlowgraph(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.extraction.LOGGER"])

        self.dataset_processing = AnyHopSingleFlowsFeatureExtractor(None)

    def test_format_is_correct(self):
        expected_label = "source-flow1-sink"
        returned_label = self.dataset_processing.get_label_from_flowgraph(
            {
                "source": "source",
                "sink": "sink",
                "flow": "flow1",
            }
        )

        self.assertEqual(returned_label, expected_label)


class FeatureExtractorFinalizeFeatures(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.extraction.LOGGER"])

        self.dataset_processing = AnyHopSingleFlowsFeatureExtractor(None)

    def test_normalized_features_are_properly_computed(self):
        input_features = [
            [4, 6, 3, 2, 6, 0, None, None],
            [4, 8, 5, 5, 5, 5, None, None],
            [3, 3, 11, 2, 4, 3, None, None],
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
        ]

        returned_features = self.dataset_processing.finalize_features(
            input_features, labels
        )

        self.assertListEqual(returned_features, expected_features)
