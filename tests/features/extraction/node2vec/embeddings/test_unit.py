from os import walk
from os.path import exists, basename
from unittest import TestCase

from shutil import rmtree
from unittest.mock import patch, Mock

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.features.extraction.node2vec.embeddings import Node2VecEmbeddings
from tests import patch_paths


class MockEmbedding(Mock):
    __name__ = "MockNode2VecEmbedding"


class MockNode2VecEmbedding(Node2VecEmbeddings):
    def init_model(self, name, **kwargs):
        return MockEmbedding()


class TestNode2VecEmbeddingInit(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = MockNode2VecEmbedding(None)


class TestNode2VecEmbeddingExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.models.LOGGER"])

        self.dataset = Mock(spec=CodeWeaknessClassificationDataset)
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

    @patch(
        "bugfinder.features.extraction.node2vec.embeddings.Node2VecEmbeddings._save_dataframe"
    )
    def test_embedding_vector_valid_size(self, mock_save_df):
        mock_save_df.return_value = None

        embeddings = self.dataset_processing.execute(**self.dataset_processing_kwargs)

        self.assertIsNotNone(embeddings)

        self.assertEqual(
            len(embeddings[0]["embeddings"]), self.dataset_processing.embedding_length
        )
        self.assertEqual(
            len(embeddings[0]["embeddings"][0]), self.dataset_processing.vector_length
        )

    def test_embeddings_folder_exists(self):
        self.dataset_processing.execute(**self.dataset_processing_kwargs)

        self.assertTrue(exists(self.dataset.embeddings_dir))

    def test_embedding_is_saved_as_file(self):
        embeddings_files = 0
        self.dataset_processing.execute(**self.dataset_processing_kwargs)

        for dirs, subdirs, files in walk(self.dataset.embeddings_dir):
            for file in files:
                if basename(file).endswith(".csv"):
                    embeddings_files += 1

        self.assertEqual(embeddings_files, 1)
