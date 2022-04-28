from os import remove
from os.path import join, exists
from unittest import TestCase

from shutil import rmtree
from unittest.mock import Mock

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.features.extraction.node2vec.model import Node2VecModel
from tests import patch_paths


class MockModel(Mock):
    __name__ = "MockNode2VecModel"


class MockNode2VecModel(Node2VecModel):
    def init_model(self, name, **kwargs):
        return MockModel()


class TestNode2VecModelInit(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = MockNode2VecModel(None)


class TestNode2VecTrainingExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.models.LOGGER"])

        self.dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing = MockNode2VecModel(self.dataset)

        self.model_name = "node2vec_mock"
        self.dataset.model_dir = "./tests/fixtures/dataset05/mock_model_dir"

        self.dataset.path = "./tests/fixtures/dataset05/"
        self.dataset.test_cases = ["joern/item01"]

        self.dataset_processing_kwargs = {"vec_length": 64}

    def tearDown(self) -> None:
        try:
            remove(join(self.dataset.model_dir, self.model_name))
            rmtree(self.dataset.model_dir)
        except FileNotFoundError:
            pass

    def test_skipgram_algorithm_is_valid(self):
        self.assertEqual(self.dataset_processing.algorithm, 1)

    def test_vector_length_is_valid(self):
        self.assertGreater(self.dataset_processing.vector_length, 0)

    def test_edge_list_valid_shape(self):
        edges = self.dataset_processing._get_all_edges()

        self.assertGreaterEqual(edges.shape[0], 1)
        self.assertEqual(edges.shape[1], 3)

    def test_graph_object_is_created(self):
        edges = self.dataset_processing._get_all_edges()

        graph = self.dataset_processing._create_graph_object(edges)

        self.assertIsNotNone(graph)
        self.assertIsNotNone(graph.edges())

    def test_check_model_dir(self):
        self.dataset_processing.execute(
            self.model_name, **self.dataset_processing_kwargs
        )

        self.assertTrue(exists(self.dataset.model_dir))

    def test_saved_model(self):
        self.dataset_processing.execute(
            self.model_name, **self.dataset_processing_kwargs
        )

        self.assertTrue(exists(join(self.dataset.model_dir, self.model_name)))
