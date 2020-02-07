""" Tests for bugfinder package
"""
from bugfinder.dataset.processing import DatasetProcessing


class MockDatasetProcessing(DatasetProcessing):
    def execute(self, *args, **kwargs):
        return


def mock_return_fn_args_as_dict(*args, **kwargs):
    kwargs.update({
        "arg%d" % i: args[i] for i in range(len(args))
    })

    return kwargs
