""" Processing module for Joern v0.4.0
"""
from os import makedirs, walk
from os.path import join, exists, splitext

from bugfinder.processing.joern import AbstractJoernProcessing
from bugfinder.settings import LOGGER


class JoernProcessing(AbstractJoernProcessing):
    """Processing class for Joern v0.4.0"""

    def configure_container(self):
        """Set up the container properties"""
        super().configure_container()

        self.image_name = "joern-lite:0.4.0"
        self.container_name = "joern040"

    def send_commands(self):
        """Send commands"""
        LOGGER.debug("Extracting Joern V0.4.0 DB...")

        content = {"edges": [], "nodes": []}

        warn_count = 0

        in_path = join(self.dataset.joern_dir, "code")
        out_path = join(self.dataset.joern_dir, "import")

        # Create output path if it doesn't exist
        if not exists(out_path):
            makedirs(out_path)

        for dirname, _, filelist in walk(in_path):
            for filename in filelist:
                (filetype, fileext) = splitext(filename)

                if fileext != ".csv":  # Only parse CSV files
                    continue

                filepath = join(dirname, filename)

                with open(filepath, "r", encoding="utf-8") as csv_file:
                    if len(content[filetype]) == 0:
                        headers = csv_file.readline()

                        if filetype == "nodes":
                            headers = headers.replace("key", ":ID")
                        elif filetype == "edges":
                            headers = headers.replace("start", ":START_ID")
                            headers = headers.replace("end", ":END_ID")
                            headers = headers.replace("type", ":TYPE")

                        content[filetype].append(headers)

                    for line in csv_file.readlines()[1:]:
                        if "\tDirectory\t" in line:
                            LOGGER.debug(
                                "Ignoring '%s'", line[:-1].replace("\t", " ").strip()
                            )
                            continue

                        if "\tStatement\t" in line:
                            warn_count += 1
                            LOGGER.warning(
                                "Parsing error in '%s'",
                                line[:-1].replace("\t", " ").strip(),
                            )

                        content[filetype].append(line)

        with open(join(out_path, "nodes.csv"), "w", encoding="utf-8") as nodes_file:
            nodes_file.writelines(content["nodes"])

        with open(join(out_path, "edges.csv"), "w", encoding="utf-8") as nodes_file:
            nodes_file.writelines(content["edges"])

        LOGGER.info("Joern V0.4.0 processing done.")
        LOGGER.debug("Stopping '%s'...", self.container_name)
