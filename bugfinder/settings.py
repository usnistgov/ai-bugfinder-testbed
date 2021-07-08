""" Common settings shared by the scripts
"""
import os
import logging.config
import multiprocessing
from os.path import dirname, abspath

ROOT_DIR = "%s/.." % dirname(abspath(__file__))

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
            "filename": "%s/debug.log" % ROOT_DIR,
            "maxBytes": 25000,
            "backupCount": 3,
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

POOL_SIZE = int(os.getenv("POOL_SIZE", multiprocessing.cpu_count()))

NEO4J_V3_MEMORY = "4G"
NEO4J_V3_CORES = POOL_SIZE
NEO4J_DEFAULT_TIMEOUT = "2h"

DATASET_DIRS = {
    "joern": "joern.db",
    "neo4j": "neo4j_v3.db",
    "feats": "features",
    "models": "models",
}


logging.config.dictConfig(LOGGER_CONFIG)
LOGGER = logging.getLogger("app")
