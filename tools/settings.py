""" Common settings shared by the scripts
"""
import logging.config
from os.path import dirname, abspath

ROOT_DIR = "%s/.." % dirname(abspath(__file__))

DIRS = {
    "docker-images": "./images"
}

LOGGER_CONFIG = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "[%(asctime)s][%(levelname)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
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
        }
    },
    "loggers": {
        "app": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": "no",
        }
    },
}

NEO4J_V3_MEMORY = "4G"

DATASET_DIRS = {
    "joern": "joern.db",
    "neo4j": "neo4j_v3.db",
    "feats": "features"
}

logging.config.dictConfig(LOGGER_CONFIG)
LOGGER = logging.getLogger("app")
