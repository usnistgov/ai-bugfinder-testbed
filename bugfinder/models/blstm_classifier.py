""" 
Bidirectional LSTM classifier.
"""

from bugfinder.models import BLSTMClassifierModel

from bugfinder.settings import LOGGER


class BLSTMClassifierTraining(BLSTMClassifierModel):
    def __init__(self, dataset):
        super().__init__(dataset)

    def init_model(self, **kwargs):
        LOGGER.debug("Bidirectional LSTM class")
