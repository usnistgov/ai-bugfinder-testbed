""" Common settings shared by the scripts
"""
from os.path import dirname, abspath

import logging.config
import multiprocessing
import os

ROOT_DIR = f"{dirname(abspath(__file__))}/.."

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
            #            "maxBytes": 25000,
            #            "backupCount": 0,
        },
    },
    "loggers": {
        "app": {"level": "DEBUG", "handlers": ["console", "file"], "propagate": "no",}
    },
}

POOL_SIZE = int(os.getenv("POOL_SIZE", multiprocessing.cpu_count()))

NEO4J_V3_MEMORY = "4G"
NEO4J_V3_CORES = POOL_SIZE
NEO4J_DEFAULT_TIMEOUT = "2h"

DATASET_DIRS = {
    "joern": "joern.db",
    "neo4j": "neo4j_v3.db",
    "feats": "features",
    "models": "models",
    "embeddings": "embeddings",
}

SUMMARY_FILE = "summary.json"
FEATURES_FILE = "features.csv"

logging.config.dictConfig(LOGGER_CONFIG)
LOGGER = logging.getLogger("app")
