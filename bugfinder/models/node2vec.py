from bugfinder.models import Node2VecModel
from bugfinder.models import Node2VecEmbeddingsBase
from bugfinder.settings import LOGGER


#########################################
class Node2VecTraining(Node2VecModel):
    """Class responsible for the training of the Word2Vec model using the node2vec algorithm output as input for the model."""

    def init_model(self, name, **kwargs):
        """Class initialization method"""
        LOGGER.debug("Class for the Node2Vec training model")


#########################################
class Node2VecEmbeddings(Node2VecEmbeddingsBase):
    """Class responsible for generating the embeddings, using the Word2Vec model trained with the output of the node2vec algorithm."""

    def init_model(self, name, **kwargs):
        """Class initialization method"""
        LOGGER.debug("Class for the Node2Vec embeddings generator")
