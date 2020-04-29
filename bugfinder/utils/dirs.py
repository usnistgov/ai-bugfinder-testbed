from os.path import exists, isdir
from shutil import rmtree, copytree

from bugfinder.settings import LOGGER


def copy_dir(src, dest):
    LOGGER.debug("Copying %s into %s..." % (src, dest))
    if not exists(src) or not isdir(src):
        LOGGER.error("%s is not a proper directory path. Copy failed." % src)
        return False

    if exists(dest):
        LOGGER.debug("%s directory already exists. Removing..." % dest)
        rmtree(dest)

    copytree(src, dest)

    LOGGER.debug("Succesfully copied %s into %s..." % (src, dest))
    return True
