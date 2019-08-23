from abc import ABC, abstractmethod
from os import listdir
from os.path import join


class DatasetProcessing(ABC):
    def __init__(self, dataset):
        self.dataset = dataset

    @abstractmethod
    def execute(self, *args, **kwargs):
        raise NotImplementedError("method not implemented")


class DatasetFileProcessing(DatasetProcessing):
    def __init__(self, dataset):
        super().__init__(dataset)

    def execute(self):
        for test_case in self.dataset.test_cases:
            for filepath in listdir(join(self.dataset.path, test_case)):
                self.process_file(join(self.dataset.path, test_case, filepath))

        self.dataset.rebuild_index()

    @abstractmethod
    def process_file(self, filepath):
        raise NotImplementedError("method not implemented")
