import unittest

from bugfinder import settings


class TestSettings(unittest.TestCase):
    def test_root_dir(self):
        self.assertIsNotNone(settings.ROOT_DIR)

    def test_logger_config(self):
        self.assertIsInstance(settings.LOGGER_CONFIG, dict)
        self.assertIsInstance(settings.LOGGER_CONFIG["formatters"], dict)
        self.assertIsInstance(settings.LOGGER_CONFIG["handlers"], dict)
        self.assertIsInstance(settings.LOGGER_CONFIG["loggers"], dict)

    def test_neo4j_memory(self):
        self.assertIsNotNone(settings.NEO4J_V3_MEMORY)

    def test_dataset_dirs(self):
        self.assertIsInstance(settings.DATASET_DIRS, dict)

    def test_logger(self):
        self.assertIsNotNone(settings.LOGGER)
