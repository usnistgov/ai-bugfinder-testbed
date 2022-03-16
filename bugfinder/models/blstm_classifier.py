""" 
Bidirectional LSTM classifier.
"""

from bugfinder.models import BLSTMClassifierModel

from bugfinder.settings import LOGGER


class BLSTMClassifierTraining(BLSTMClassifierModel):
    """Bidirectional Long Short-Term Memory classifier"""

    def __init__(self, dataset):
        """Class initialization method"""
        super().__init__(dataset)

    def init_model(self, **kwargs):
        """Setup the model"""
        LOGGER.debug("Bidirectional LSTM class")
