from bugfinder.models import Node2VecModel
from bugfinder.models import Node2VecEmbeddingsBase
from bugfinder.settings import LOGGER


#########################################
class Node2VecTraining(Node2VecModel):
    def init_model(self, name, **kwargs):
        LOGGER.debug("Class for the Node2Vec training model")


#########################################
class Node2VecEmbeddings(Node2VecEmbeddingsBase):
    def init_model(self, name, **kwargs):
        LOGGER.debug("Class for the Node2Vec embeddings generator")
