from os.path import join
from unittest import TestCase
from unittest.mock import patch, Mock

import pandas as pd

from bugfinder.dataset import CWEClassificationDataset
from bugfinder.features.reduction.pca import FeatureSelector as PCA
from tests import patch_paths


class FeatureExtractorExecute(TestCase):
    def setUp(self) -> None:
        patch_paths(
            self,
            [
                "bugfinder.dataset.join",
                "bugfinder.dataset.listdir",
                "bugfinder.dataset.pd.read_csv",
                "bugfinder.dataset.CWEClassificationDataset._validate_features",
                "bugfinder.features.reduction.pca.PCA",
                "bugfinder.features.reduction.pca.pd.DataFrame",
                "bugfinder.features.reduction.pca.LOGGER",
                "bugfinder.features.reduction.LOGGER",
            ],
        )

        self.dataset = Mock(spec=CWEClassificationDataset)
        self.dataset.feats_dir = "mock_feats_dir"
        self.dataset.feats_version = 1
        self.dataset.features = pd.read_csv(
            "tests/fixtures/dataset01/features/features.csv"
        )
        self.data_processing = PCA(self.dataset)
        self.data_processing_kwargs = {"dry_run": False, "dimension": 2}

    @patch("bugfinder.features.reduction.copy")
    def test_feature_file_is_copied(self, mock_copy):
        self.data_processing.execute(**self.data_processing_kwargs)

        mock_copy.assert_called_with(
            join(self.dataset.feats_dir, "features.csv"),
            join(
                self.dataset.feats_dir,
                "features.%d.csv" % self.dataset.feats_version,
            ),
        )

    @patch("bugfinder.features.reduction.copy")
    def test_feature_version_is_updated(self, mock_copy):
        mock_copy.return_value = None
        self.data_processing.execute(**self.data_processing_kwargs)

        self.assertEqual(self.dataset.feats_version, 1)

    @patch("bugfinder.features.reduction.copy")
    @patch(
        "tests.features.reduction.pca.test_unit.CWEClassificationDataset.rebuild_index"
    )
    def test_index_is_rebuilt(self, mock_copy, mock_rebuild_index):
        mock_copy.return_value = None

        self.data_processing.execute(**self.data_processing_kwargs)

        mock_rebuild_index.assert_called()
