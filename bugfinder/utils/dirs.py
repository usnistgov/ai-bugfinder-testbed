""" File management utilities.
"""
from os.path import exists, isdir

from shutil import rmtree, copytree

from bugfinder.settings import LOGGER


def copy_dir(src, dest):
    """Copy a directory from source to destination. Ensure source and destination
    exists and source is a directory.
    """
    LOGGER.debug("Copying %s into %s...", src, dest)
    if not exists(src) or not isdir(src):
        LOGGER.error("Directory '%s' is not a proper directory path. Copy failed.", src)
        return False

    if exists(dest):
        LOGGER.debug("Directory '%s' already exists. Removing...", dest)
        rmtree(dest)

    copytree(src, dest)

    LOGGER.debug("Succesfully copied '%s' into '%s'...", src, dest)
    return True
