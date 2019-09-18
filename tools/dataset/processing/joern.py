from os import walk, makedirs
from os.path import realpath, join, splitext, exists

from tools.dataset.processing import DatasetProcessingWithContainer
from tools.settings import LOGGER
from tools.utils.rand import get_rand_string


class JoernDatasetProcessing(DatasetProcessingWithContainer):
    def configure_container(self):
        self.image_name = "joern-lite:0.4.0"
        self.container_name = "joern-%s" % get_rand_string(
            6, special=False, upper=False
        )
        self.volumes = {realpath(self.dataset.path): "/code"}
        self.detach = False

    def send_commands(self):
        db_path = "%s/joern.db" % self.dataset.path

        content = {
            "edges": [],
            "nodes": []
        }

        warn_count = 0

        in_path = join(db_path, "code")
        out_path = join(db_path, "import")

        if not exists(out_path):
            makedirs(out_path)

        for dirname, sudirs, filelist in walk(in_path):
            for filename in filelist:
                (filetype, fileext) = splitext(filename)

                if fileext == ".csv":
                    filepath = join(dirname, filename)

                    with open(filepath) as csv_file:
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
                                    "Ignoring '%s'" %
                                    line[:-1].replace("\t", " ").strip()
                                )
                                continue

                            if "\tStatement\t" in line:
                                warn_count += 1
                                LOGGER.warn(
                                    "Parsing error in '%s'" %
                                    line[:-1].replace("\t", " ").strip()
                                )

                            content[filetype].append(line)

        with open(join(out_path, "nodes.csv"), "w") as nodes_file:
            nodes_file.writelines(content["nodes"])

        with open(join(out_path, "edges.csv"), "w") as nodes_file:
            nodes_file.writelines(content["edges"])
