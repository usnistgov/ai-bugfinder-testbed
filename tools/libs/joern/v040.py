""" Execute code analysis with Joern v0.4.0
"""
import os
from os import makedirs
from os.path import splitext, join, exists

from libs.joern.common import run_joern_lite
from libs.neo4j.ai import import_csv_files
from settings import LOGGER


def csv_packer(db_path):
    content = {
        "edges": [],
        "nodes": []
    }

    warn_count = 0

    in_path = join(db_path, "code")
    out_path = join(db_path, "import")

    if not exists(out_path):
        makedirs(out_path)

    for dirname, sudirs, filelist in os.walk(in_path):
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
                            LOGGER.info(
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


def main(code_path):
    LOGGER.info("Starting Joern 0.4.0...")
    run_joern_lite("0.4.0", code_path)

    LOGGER.info("Joern database generated. Formatting CSV files...")
    csv_packer(join(code_path, "joern.db"))

    LOGGER.info("CSV files formatted. Preparing import in Neo4j 3.5...")
    db_path = join(code_path, "neo4j_v3.db")
    import_dir = join(code_path, "joern.db", "import")
    makedirs(db_path)

    LOGGER.info("Import to Neo4j 3.5 ready. Importing...")
    import_csv_files(db_path, import_dir)

    LOGGER.info("Successful import to Neo4j 3.5.")
