"""
"""
import logging


def add_logfile(logger, logfile):
    logfile_handler = logging.FileHandler(logfile)
    logfile_handler.setFormatter(logger.handlers[0].formatter)
    logfile_handler.setLevel(logging.DEBUG)

    logger.addHandler(logfile_handler)

    return logger
