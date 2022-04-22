from os import remove
from os.path import join, exists
from unittest import TestCase

from gensim.models import Word2Vec
from shutil import rmtree
from unittest.mock import Mock

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.features.extraction.word2vec.model import Word2VecModel
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
