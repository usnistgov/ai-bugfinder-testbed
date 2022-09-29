from os import walk
from os.path import join, exists, basename
from unittest import TestCase

from gensim.models import Word2Vec
from shutil import rmtree
from unittest.mock import Mock

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.features.extraction.word2vec.embeddings import Word2VecEmbeddings
from tests import patch_paths


class MockEmbedding(Mock):
    __name__ = "MockW2VEmbedding"


class MockWord2VecEmbedding(Word2VecEmbeddings):
    def init_model(self, name, **kwargs):
        return MockEmbedding()


class TestWord2VecEmbeddingInit(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = MockWord2VecEmbedding(None)


class TestWord2VecEmbeddingExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.models.LOGGER"])

        self.dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing = MockWord2VecEmbedding(self.dataset)

        self.dataset.path = "./tests/fixtures/dataset05/"
        self.dataset.test_cases = ["./class01/tc05", "./class02/tc05"]

        self.tokenized_file = join(self.dataset.path, "./class01/tc05/item01.c")

        self.model_name = "word2vec_test.bin"

        self.dataset.model_dir = "./tests/fixtures/dataset05/models"
        self.dataset.embeddings_dir = "./tests/fixtures/dataset05/mock_emb_dir"

        self.model_kwargs = {"name": self.model_name}

    def tearDown(self) -> None:
        try:
            rmtree(self.dataset.embeddings_dir)
        except FileNotFoundError:
            pass

    def test_input_is_tokenized(self):
        pass

    def test_embedding_vector_length_is_valid(self):
        self.assertGreater(self.dataset_processing.embedding_length, 0)
        self.assertGreater(self.dataset_processing.vector_length, 0)

    def test_check_model_dir(self):
        self.assertTrue(exists(self.dataset.model_dir))

    def test_embedding_vector_valid_size(self):
        tokens = dict()

        model = Word2Vec.load(join(self.dataset.model_dir, self.model_name))

        with open(self.tokenized_file) as token_file:
            content = token_file.read().splitlines()

        tokens["tokens"] = content

        embeddings = self.dataset_processing.vectorize(model, tokens)

        self.assertEqual(embeddings.shape[0], self.dataset_processing.embedding_length)
        self.assertEqual(embeddings.shape[1], self.dataset_processing.vector_length)

    def test_embeddings_folder_exists(self):
        self.dataset_processing.execute(**self.model_kwargs)

        self.assertTrue(exists(self.dataset.embeddings_dir))

    def test_embedding_is_saved_as_file(self):
        embeddings_files = 0
        self.dataset_processing.execute(**self.model_kwargs)

        for dirs, subdirs, files in walk(self.dataset.embeddings_dir):
            for file in files:
                if basename(file).endswith(".csv"):
                    embeddings_files += 1

        self.assertEqual(embeddings_files, 4)
