from unittest import TestCase

from unittest.mock import Mock

from bugfinder.base.dataset import CodeWeaknessClassificationDataset
from tests import MockAbstractProcessing


class TestAbstractProcessingInit(TestCase):
    def test_dataset_path_is_correct(self):
        dataset_obj = Mock(spec=CodeWeaknessClassificationDataset)
        data_processing = MockAbstractProcessing(dataset_obj)

        self.assertEqual(data_processing.dataset, dataset_obj)
