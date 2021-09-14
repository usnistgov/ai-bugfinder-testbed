from logging import DEBUG

from bugfinder.models import Word2VecModel
from bugfinder.models import Word2VecEmbeddings

from bugfinder.settings import LOGGER

#########################################
class Word2VecTraining(Word2VecModel):
    def __init__(self, dataset):
        super().__init__(dataset)

    def init_model(self, **kwargs):
        LOGGER.debug("Word2vec model class")


#########################################
class Word2VecEmbeddings(Word2VecEmbeddings):
    def __init__(self, dataset):
        super().__init__(dataset)

    def init_model(self, **kwargs):
        LOGGER.debug("Word2vec embeddings class")
