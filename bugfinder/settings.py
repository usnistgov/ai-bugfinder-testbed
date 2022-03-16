""" Common configuration keys for the bugfinder package.
"""
from os.path import dirname, abspath

import logging.config
import multiprocessing
import os

ROOT_DIR = f"{dirname(abspath(__file__))}/.."
""" str: Project root directory.
"""

POOL_SIZE = int(os.getenv("POOL_SIZE", multiprocessing.cpu_count()))
""" int: Number of CPU cores that can be used for multiprocessing tasks.
"""

# Neo4J configuration
NEO4J_V3_MEMORY = "4G"
""" str: Memory allocated to Neo4J databases.
"""

NEO4J_V3_CORES = POOL_SIZE
""" int: Number of CPU cores allowed to be used by Neo4J. Defaults to `POOL_SIZE`.
"""

NEO4J_DEFAULT_TIMEOUT = "2h"
""" str: Default timeout for Neo4J queries.
"""

# Dataset configuration
DATASET_DIRS = {
    "joern": "joern.db",
    "neo4j": "neo4j_v3.db",
    "feats": "features",
    "models": "models",
    "embeddings": "embeddings",
}
""" dict: Dataset directory names used by the various scripts.
"""

SUMMARY_FILE = "summary.json"
""" str: Name of the file storing dataset processing history and statistics.
"""

FEATURES_FILE = "features.csv"
""" str: Name of the CSV file containing the features that can be used for training 
purposes.
"""

# Logging configuration
LOGGER_CONFIG = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "[%(asctime)s][%(levelname)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": f"{ROOT_DIR}/debug.log",
            # "maxBytes": 25000,
            # "backupCount": 0,
        },
    },
    "loggers": {
        "app": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": "no",
        }
    },
}
""" dict: Logging configuration for the project.
"""

logging.config.dictConfig(LOGGER_CONFIG)
LOGGER = logging.getLogger("app")
""" logging.Logger: Main `Logger` instance used throughout the application.
"""
