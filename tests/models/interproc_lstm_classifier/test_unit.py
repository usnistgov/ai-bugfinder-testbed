from unittest import TestCase
from unittest.mock import Mock

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from bugfinder.models.interproc_lstm import InterprocLSTMTraining
import tensorflow as tf


class TestInterprocLSTMTrainingInit(TestCase):
    def setUp(self) -> None:
        dataset = Mock(spec=CodeWeaknessClassificationDataset)
        self.dataset_processing = InterprocLSTMTraining(dataset)

    def test_model_cls_initialized(self):
        self.assertEqual(self.dataset_processing.model_cls, tf.keras.models.Sequential)
