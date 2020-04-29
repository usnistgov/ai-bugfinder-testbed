from os import makedirs, walk
from os.path import join, exists, splitext

from bugfinder.joern import JoernDefaultDatasetProcessing
from bugfinder.settings import LOGGER


class JoernDatasetProcessing(JoernDefaultDatasetProcessing):
    def configure_container(self):
        super().configure_container()

        self.image_name = "joern-lite:0.4.0"
        self.container_name = "joern040"

    def send_commands(self):
        content = {"edges": [], "nodes": []}

        warn_count = 0

        in_path = join(self.dataset.joern_dir, "code")
        out_path = join(self.dataset.joern_dir, "import")

        # Create output path if it doesn't exist
        if not exists(out_path):
            makedirs(out_path)

        for dirname, sudirs, filelist in walk(in_path):
            for filename in filelist:
                (filetype, fileext) = splitext(filename)

                if fileext != ".csv":  # Only parse CSV files
                    continue

                filepath = join(dirname, filename)

                with open(filepath, "r") as csv_file:
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
                                "Ignoring '%s'" % line[:-1].replace("\t", " ").strip()
                            )
                            continue

                        if "\tStatement\t" in line:
                            warn_count += 1
                            LOGGER.warn(
                                "Parsing error in '%s'"
                                % line[:-1].replace("\t", " ").strip()
                            )

                        content[filetype].append(line)

        with open(join(out_path, "nodes.csv"), "w") as nodes_file:
            nodes_file.writelines(content["nodes"])

        with open(join(out_path, "edges.csv"), "w") as nodes_file:
            nodes_file.writelines(content["edges"])
