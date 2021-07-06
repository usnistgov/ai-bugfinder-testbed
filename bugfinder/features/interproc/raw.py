"""
"""
from concurrent.futures import ThreadPoolExecutor

from bugfinder import settings
from bugfinder.neo4j import Neo4J3Processing
from bugfinder.settings import LOGGER, POOL_SIZE
from os.path import join, exists
from os import mkdir
import csv


class FeatureExtractor(Neo4J3Processing):
    timeout = settings.NEO4J_DEFAULT_TIMEOUT

    def configure_container_with_dict(self, container_config):
        self.timeout = container_config["timeout"]
        self.configure_container()

    def configure_container(self):
        super().configure_container()
        self.container_name = "fext-interprocedural-raw"
        self.environment["NEO4J_dbms_transaction_timeout"] = self.timeout

    def _get_entrypoint_list(self):
        list_entrypoints_cmd = """
            MATCH (fl:GenericNode {type:"File"})-[:IS_FILE_OF]->(fn {type:"Function",code:"main"})-[:IS_FUNCTION_OF_CFG]->(en:GenericNode {type:"CFGEntryNode"})
            RETURN en.functionId AS id, fl.code AS filepath, fn.code AS name
        """
        return self.neo4j_db.run(list_entrypoints_cmd).data()

    def get_flowgraph_list_for_entrypoint(self, entrypoint):
        flowgraph_command = """
            MATCH p=(entry:UpstreamNode {type:"CFGEntryNode"})-[:FLOWS_TO*]->(exit:GenericNode)
            WHERE entry.functionId="%s" AND NOT (exit)-[:FLOWS_TO]->()
            WITH p, randomUUID() AS path_id, ANY(n IN NODES(p) WHERE "BugSinkNode" IN LABELS(n)) AS bad
            UNWIND NODES(p) AS n
            OPTIONAL MATCH (n)<-[inflow:REACHES]-()
            OPTIONAL MATCH (n)-[outflow:REACHES]->()
            WITH DISTINCT path_id, bad, n, PROPERTIES(inflow) AS inflow, PROPERTIES(outflow) AS outflow
            WHERE inflow IS NOT null OR outflow IS NOT null
            RETURN path_id, bad, id(n), n.ast, COLLECT(DISTINCT inflow) AS inflow, COLLECT(DISTINCT outflow) AS outflow
        """
        return self.neo4j_db.run(flowgraph_command % entrypoint["id"]).data()

    def extract_features_worker(self, args):
        seqs = {}
        try:
            paths = self.get_flowgraph_list_for_entrypoint(args)
            for step in paths:
                path_id = step["path_id"]
                if not path_id in seqs:
                    seqs[path_id] = []
                seqs[path_id].append(step)
        except Exception as e:
            LOGGER.warning("Error processing testcase '%s': %s" % (args["filepath"], e))
        return seqs.values()

    def extract_features(self):
        entrypoint_list = self._get_entrypoint_list()

        if len(entrypoint_list) == 0:
            LOGGER.warning("No entrypoint found. Returning None...")
            return None

        LOGGER.info(
            "Retrieved %d entrypoints. Querying for "
            "flowgraphs..." % len(entrypoint_list)
        )

        with ThreadPoolExecutor(max_workers=POOL_SIZE) as executor:
            res = executor.map(
                self.extract_features_worker,
                entrypoint_list,
            )
            return list(res)

    def send_commands(self):
        super().send_commands()
        LOGGER.debug("Extracting features...")
        self.check_extraction_inputs()
        features = self.extract_features()
        self.write_extraction_outputs(features)

    def check_extraction_inputs(self):
        # Check if features directory exists. Create it if it does not.
        if not exists(self.dataset.feats_dir):
            mkdir(self.dataset.feats_dir)
        return join(self.dataset.feats_dir, "interproc-features.csv")

    def write_extraction_outputs(self, features):
        output_file = join(self.dataset.feats_dir, "interproc-features.csv")

        with open(output_file, "w") as csv_file:
            csv_writer = csv.writer(csv_file)

            # FIXME developer will not know how to setup its features
            # labels = self.get_labels_from_feature_map() + ["result", "name"]

            # Make sure the number of labels and the number of features are the
            # same.
            # if len(labels) != len(features[0]):
            #    raise IndexError(
            #        "Number of labels (%d) differs from number of features (%d)"
            #        % (len(labels), len(features[0]))
            #    )

            # Write headers and content to CSV file
            # csv_writer.writerow(labels)
            csv_writer.writerows(features)
