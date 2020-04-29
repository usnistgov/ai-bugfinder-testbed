""" Tests for bugfinder package
"""
import json
import os
from hashlib import sha256
from os.path import join
from unittest.mock import patch

from bugfinder.dataset.processing import DatasetProcessing


class MockDatasetProcessing(DatasetProcessing):
    def execute(self, *args, **kwargs):
        return


def mock_return_fn_args_as_dict(*args, **kwargs):
    kwargs.update({
        "arg%d" % i: args[i] for i in range(len(args))
    })

    return kwargs


def directory_shasum(directory):
    directory_hashmap = dict()

    for root, dirs, files in os.walk(directory):
        for f in files:
            fpath = join(root, f)
            with open(fpath, "rb") as fp:
                directory_hashmap[
                    fpath.replace(directory, "")
                ] = sha256(fp.read()).hexdigest()

    return sha256(
        json.dumps(directory_hashmap, sort_keys=True).encode("utf-8")
    ).hexdigest()


def patch_paths(test_case, path_list):
    for patch_path in path_list:
        patch_logger = patch(patch_path)
        patch_logger.start()
        test_case.addCleanup(patch_logger.stop)
