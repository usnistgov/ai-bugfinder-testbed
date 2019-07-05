"""
"""
from __future__ import division
from builtins import range
from builtins import object
from past.utils import old_div
import numpy as np
from scipy import sparse
from scipy.io import mmread
from random import shuffle

from scipy.sparse import csr_matrix


class Dataset(object):
    def __init__(self, feature_filename, feature_label_filename, label_filename,
                 train_ratio=0.8, batch_size=1):

        # Loading label and features
        self.labels = np.genfromtxt(label_filename, delimiter=',', dtype=None)
        self.feature_names = np.genfromtxt(feature_label_filename,
                                           delimiter='\n', dtype=None)

        self.features = mmread(feature_filename).tocsr()

        # Check if we have as many labels as features
        if len(self.labels) != self.features.shape[0]:
            raise ValueError(
                "Features and labels cardinalities do not match. Exiting..."
            )

        self.input = self.features.shape[1]
        self.output = 2
        self.batch_size = batch_size

        # Prepare indexes to get random sets for training and test
        shufidx = list(range(self.features.shape[0]))
        shuffle(shufidx)

        if 0 < train_ratio < 1:
            self.training_index = shufidx[:int(train_ratio * len(shufidx))]
            self.testing_index = shufidx[int(train_ratio * len(shufidx)):]
        elif train_ratio == 0:
            self.training_index = list()
            self.testing_index = shufidx
        elif train_ratio == 1:
            self.training_index = shufidx
            self.testing_index = list()

        self.last_index = 0

        # Assume training mode per default
        self.index = self.training_index

    def set_batch_size(self, batch_size):
        self.batch_size = batch_size

    def reset_index(self):
        self.last_index = 0
        shuffle(self.index)

    def set_mode(self, mode="training"):
        if mode == "training":
            self.index = self.training_index
        else:
            self.index = self.testing_index

        self.last_index = 0

    def get_batch_count(self):
        return int(old_div(len(self.index), self.batch_size))

    def get_next_batch(self):
        labels = np.zeros((self.batch_size, self.output))
        features = np.zeros((self.batch_size, self.input))
        testcases = [None] * self.batch_size

        for _offset in range(self.batch_size):
            if self.last_index >= len(self.index):
                raise IndexError("Dataset exhausted")

            label, testcase = self.labels[self.index[self.last_index]]
            features[_offset] = self.features[
                self.index[self.last_index]
            ].todense()

            # Need to use this trick to use softmax in the NN
            labels[_offset] = [label, 1 - label]
            testcases[_offset] = testcase

            self.last_index += 1

        return labels, features, testcases

    def get_whole_set(self):
        batch_size = self.batch_size
        last_index = self.last_index
        self.batch_size = len(self.index)
        self.last_index = 0
        labels, features, testcases = self.get_next_batch()
        self.batch_size = batch_size
        self.last_index = last_index

        return labels, features, testcases

    def enhance_dataset(self, extra_dataset):
        local_features = self.feature_names.tolist()
        extra_features = extra_dataset.feature_names.tolist()

        # if local_features == extra_features:
        #     return False

        # Missing features in the local set will be removed
        new_feature_names = sorted(list(
            set(local_features) & set(extra_features)
        ))
        new_features = csr_matrix(
            (self.features.shape[0], 0)
        )

        for feature_name in new_feature_names:
            feature_index = list(local_features).index(feature_name)

            new_features = sparse.hstack(
                (new_features, self.features.getcol(feature_index))
            )

        self.feature_names = np.array(new_feature_names)
        self.features = new_features.tocsr()
        self.input = self.features.shape[1]
        return True
