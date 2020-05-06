from unittest import TestCase
from unittest.mock import patch, Mock

from bugfinder.dataset import CWEClassificationDataset
from bugfinder.features.any_hop.all_flows import (
    FeatureExtractor as AnyHopAllFlowsFeatureExtractor,
)
from tests import patch_paths


class FeatureExtractorConfigureContainer(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.LOGGER"])

        dataset = Mock(spec=CWEClassificationDataset)
        dataset.ops_queue = list()

        self.dataset_processing = AnyHopAllFlowsFeatureExtractor(dataset)

    @patch("bugfinder.neo4j.Neo4J3Processing.configure_container")
    def test_container_name_is_correct(self, mock_configure_container):
        mock_configure_container.return_value = None
        expected_container_name = "fext-any-hop-all-flows"

        self.dataset_processing.configure_container()

        self.assertEqual(
            self.dataset_processing.container_name, expected_container_name
        )


class FeatureExtractorGetFlowgraphListForEntrypoint(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.LOGGER"])

        self.dataset_processing = AnyHopAllFlowsFeatureExtractor(None)

    @patch("bugfinder.neo4j.Neo4J3Processing.neo4j_db")
    def test_neo4j_db_run_is_called(self, mock_neo4j_db):
        self.dataset_processing.get_flowgraph_list_for_entrypoint({"id": None})

        self.assertTrue(mock_neo4j_db.run.called)


class FeatureExtractorGetFlowgraphCount(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.LOGGER"])

        self.dataset_processing = AnyHopAllFlowsFeatureExtractor(None)

    def test_returns_1(self):
        expected_count = 1

        returned_count = self.dataset_processing.get_flowgraph_count(None)

        self.assertEqual(returned_count, expected_count)


class FeatureExtractorGetLabelFromFlowgraph(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.LOGGER"])

        self.dataset_processing = AnyHopAllFlowsFeatureExtractor(None)

    def test_format_is_correct(self):
        expected_label = "source-flow1:flow2-sink"
        returned_label = self.dataset_processing.get_label_from_flowgraph(
            {"source": "source", "sink": "sink", "flow": ["flow1", "flow2"],}
        )

        self.assertEqual(returned_label, expected_label)
