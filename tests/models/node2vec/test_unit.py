from unittest import TestCase
from unittest.mock import patch, Mock

from os import remove, walk
from os.path import join, exists, basename

from shutil import rmtree

from bugfinder.dataset import CWEClassificationDataset
from bugfinder.models import Node2VecModel, Node2VecEmbeddingsBase

from tests import patch_paths


class MockModel(Mock):
    __name__ = "MockNode2VecModel"


class MockNode2VecModel(Node2VecModel):
    def init_model(self, name, **kwargs):
        return MockModel()


class TestNode2VecModelInit(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = MockNode2VecModel(None)


class Node2VecTrainingExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.models.LOGGER"])

        self.dataset = Mock(spec=CWEClassificationDataset)
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


##########################################################################################


class MockEmbedding(Mock):
    __name__ = "MockNode2VecEmbedding"


class MockNode2VecEmbedding(Node2VecEmbeddingsBase):
    def init_model(self, name, **kwargs):
        return MockEmbedding()


class TestNode2VecEmbeddingInit(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = MockNode2VecEmbedding(None)


class Node2VecEmbeddingExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.models.LOGGER"])

        self.dataset = Mock(spec=CWEClassificationDataset)
        self.dataset_processing = MockNode2VecEmbedding(self.dataset)

        self.dataset.path = "./tests/fixtures/dataset05/"
        self.dataset.test_cases = ["joern/item01"]

        self.dataset_processing_kwargs = {
            "model": "node2vec_test.bin",
            "emb_length": 20,
            "vec_length": 64,
        }

        self.model_name = "node2vec_mock"
        self.dataset.model_dir = "./tests/fixtures/dataset05/models"
        self.dataset.embeddings_dir = "./tests/fixtures/dataset05/mock_emb_dir"

    def tearDown(self) -> None:
        try:
            rmtree(self.dataset.embeddings_dir)
        except FileNotFoundError:
            pass

    def test_edge_list_valid_type(self):
        edges = self.dataset_processing._get_nodes_list()

        self.assertIsNotNone(edges)

        self.assertIsInstance(edges[0]["path"], str)
        self.assertIsInstance(edges[0]["nodes"], list)

    def test_embedding_vector_length_is_valid(self):
        self.assertGreater(self.dataset_processing.embedding_length, 0)
        self.assertGreater(self.dataset_processing.vector_length, 0)

    def test_check_model_dir(self):
        self.assertTrue(exists(self.dataset.model_dir))

    @patch("bugfinder.models.Node2VecEmbeddingsBase._save_dataframe")
    def test_embedding_vector_valid_size(self, mock_save_df):
        mock_save_df.return_value = None

        embeddings = self.dataset_processing.execute(
            self.model_name, **self.dataset_processing_kwargs
        )

        self.assertIsNotNone(embeddings)

        self.assertEqual(
            len(embeddings[0]["embeddings"]), self.dataset_processing.embedding_length
        )
        self.assertEqual(
            len(embeddings[0]["embeddings"][0]), self.dataset_processing.vector_length
        )

    def test_embeddings_folder_exists(self):
        self.dataset_processing.execute(
            self.model_name, **self.dataset_processing_kwargs
        )

        self.assertTrue(exists(self.dataset.embeddings_dir))

    def test_embedding_is_saved_as_file(self):
        embeddings_files = 0
        self.dataset_processing.execute(
            self.model_name, **self.dataset_processing_kwargs
        )

        for dirs, subdirs, files in walk(self.dataset.embeddings_dir):
            for file in files:
                if basename(file).endswith(".csv"):
                    embeddings_files += 1

        self.assertEqual(embeddings_files, 1)
