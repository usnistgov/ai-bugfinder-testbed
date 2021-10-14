from bugfinder.models import Word2VecEmbeddingsBase
from bugfinder.models import Word2VecModel
from bugfinder.settings import LOGGER


#########################################
class Word2VecTraining(Word2VecModel):
    def init_model(self, name, **kwargs):
        LOGGER.debug("Word2vec model class")


#########################################
class Word2VecEmbeddings(Word2VecEmbeddingsBase):
    def init_model(self, name, **kwargs):
        LOGGER.debug("Word2vec embeddings class")
