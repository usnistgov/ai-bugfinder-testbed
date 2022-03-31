from unittest import TestCase
from unittest.mock import Mock

from os import walk, remove
from os.path import join, exists, basename

from shutil import rmtree

from gensim.models import Word2Vec

from bugfinder.dataset import CodeWeaknessClassificationDataset
from bugfinder.models.word2vec import Word2VecModel, Word2VecEmbeddingsBase

from tests import patch_paths


class MockModel(Mock):
    __name__ = "MockW2VModel"


class MockWord2VecModel(Word2VecModel):
    def init_model(self, name, **kwargs):
        return MockModel()


class TestWord2VecModelInit(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = MockWord2VecModel(None)


class Word2VecTrainingExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(self, ["bugfinder.models.LOGGER"])

        self.dataset = Mock(spec=CodeWeaknessClassificationDataset)

        self.dataset.path = "./tests/fixtures/dataset05/"
        self.dataset.test_cases = ["./class01/tc05", "./class02/tc05"]

        self.tokenized_file = join(self.dataset.path, "./class01/tc05/item01.c")

        self.model_name = "w2v_mock"
        self.dataset.model_dir = "./tests/fixtures/dataset05/mock_model_dir"

        self.dataset_processing = MockWord2VecModel(self.dataset)

    def tearDown(self) -> None:
        try:
            remove(join(self.dataset.model_dir, self.model_name))
            rmtree(self.dataset.model_dir)
        except FileNotFoundError:
            pass

    def test_input_is_tokenized(self):
        pass

    def test_skipgram_algorithm_is_valid(self):
        self.assertEqual(self.dataset_processing.algorithm, 1)

    def test_word_dimension_default_value_is_valid(self):
        self.assertGreater(self.dataset_processing.word_dim, 0)

    def test_check_model_dir(self):
        self.dataset_processing.execute(self.model_name)

        self.assertTrue(exists(self.dataset.model_dir))

    def test_model_valid_output_size(self):
        self.dataset_processing.execute(self.model_name)

        vectors = []
        model = Word2Vec.load(join(self.dataset.model_dir, self.model_name))

        with open(self.tokenized_file) as token_file:
            tokens = token_file.read().splitlines()

        for token in tokens:
            vector = model.wv[token]
            self.assertEqual(len(vector), self.dataset_processing.word_dim)

            vectors.append(model.wv[token])

        self.assertEqual(len(vectors), len(tokens))


##########################################################################################


class MockEmbedding(Mock):
    __name__ = "MockW2VEmbedding"


class MockWord2VecEmbedding(Word2VecEmbeddingsBase):
    def init_model(self, name, **kwargs):
        return MockEmbedding()


class TestWord2VecEmbeddingInit(TestCase):
    def setUp(self) -> None:
        self.dataset_processing = MockWord2VecEmbedding(None)


class Word2VecEmbeddingExecute(TestCase):
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

        self.model_kwargs = {"model": "word2vec_test.bin"}

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
        embeddings = dict()

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
