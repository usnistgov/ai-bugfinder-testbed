""" Script building all docker images for the project
"""
from os import listdir

import docker

from settings import ROOT_DIR, DIRS, LOGGER
from utils.statistics import get_time

if __name__ == "__main__":
    LOGGER.info("Building docker images...")

    docker_cli = docker.from_env()
    img_root_dir = "%s/%s" % (ROOT_DIR, DIRS["docker-images"])
    img_dirlist = listdir(img_root_dir)

    stats = {
        "total_files": len(img_dirlist),
        "current_file": 1,
        "total_time": 0
    }

    for img_dir in img_dirlist:
        LOGGER.info(
            "Building image %d/%d: %s..." %
            (stats["current_file"], stats["total_files"], img_dir)
        )

        # Gathering path and tag info for the build
        img_path = "%s/%s" % (img_root_dir, img_dir)
        img_tag_parts = img_dir.split("-v")

        img_tag = img_tag_parts[0]
        img_tag += ":%s" % img_tag_parts[1] if len(img_tag_parts) > 1 \
            else ":latest"

        # Using docker for building
        beg_time = get_time()
        docker_cli.images.build(
            path=img_path,
            tag=img_tag
        )
        end_time = get_time()

        total_time = end_time - beg_time
        LOGGER.info(
            "Image built in %dms." % total_time
        )

        stats["current_file"] += 1
        stats["total_time"] += total_time

    LOGGER.info("Images succesfully built (took %dms)." % stats["total_time"])
