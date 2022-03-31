from unittest import TestCase
from unittest.mock import patch, Mock

from bugfinder.dataset import CodeWeaknessClassificationDataset
from bugfinder.features.extraction.single_hop.raw import (
    FeatureExtractor as SingleHopRawFeatureExtractor,
)
from tests import patch_paths


class FeatureExtractorConfigureContainer(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.extraction.LOGGER"])

        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        dataset.ops_queue = list()

        self.dataset_processing = SingleHopRawFeatureExtractor(dataset)

    @patch("bugfinder.neo4j.Neo4J3Processing.configure_container")
    def test_container_name_is_correct(self, mock_configure_container):
        mock_configure_container.return_value = None
        expected_container_name = "fext-single-hop-raw"

        self.dataset_processing.configure_container()

        self.assertEqual(
            self.dataset_processing.container_name, expected_container_name
        )


class FeatureExtractorGetFlowgraphListForEntrypoint(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.extraction.LOGGER"])

        self.dataset_processing = SingleHopRawFeatureExtractor(None)

    @patch("bugfinder.neo4j.Neo4J3Processing.neo4j_db")
    def test_neo4j_db_run_is_called(self, mock_neo4j_db):
        self.dataset_processing.get_flowgraph_list_for_entrypoint({"function_id": None})

        self.assertTrue(mock_neo4j_db.run.called)


class FeatureExtractorGetFlowgraphCount(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.extraction.LOGGER"])

        self.dataset_processing = SingleHopRawFeatureExtractor(None)

    def test_returns_expected_count(self):
        expected_count = 42

        returned_count = self.dataset_processing.get_flowgraph_count(
            {"count": expected_count}
        )

        self.assertEqual(returned_count, expected_count)


class FeatureExtractorGetLabelFromFlowgraph(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.features.extraction.LOGGER"])

        self.dataset_processing = SingleHopRawFeatureExtractor(None)

    def test_format_is_correct(self):
        expected_label = "source-flow-sink"
        returned_label = self.dataset_processing.get_label_from_flowgraph(
            {"source": "source", "sink": "sink", "flow": "flow"}
        )

        self.assertEqual(returned_label, expected_label)
