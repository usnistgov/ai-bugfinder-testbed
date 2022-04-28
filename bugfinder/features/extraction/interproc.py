"""
"""
from concurrent.futures import ThreadPoolExecutor
from tqdm.contrib.concurrent import thread_map
from threading import Lock
from os import mkdir
from os.path import join, exists

import json

from bugfinder import settings
from bugfinder.processing.neo4j import Neo4J3Processing
from bugfinder.settings import LOGGER, POOL_SIZE


class FeatureExtractor(Neo4J3Processing):
    timeout = settings.NEO4J_DEFAULT_TIMEOUT
    cats = {}
    catlock = Lock()

    def configure_container_with_dict(self, container_config):
        self.timeout = container_config["timeout"]
        self.configure_container()

    def configure_container(self):
        super().configure_container()
        self.container_name = "fext-interprocedural-raw"
        self.environment["NEO4J_dbms_transaction_timeout"] = self.timeout

    def _get_entrypoint_list(self):
        # List all entrypoing nodes, i.e. nodes describing function "main"
        list_entrypoints_cmd = """
            MATCH (fl:GenericNode {type:"File"})-[:IS_FILE_OF]->(fn {type:"Function",code:"main"})-[:IS_FUNCTION_OF_CFG]->(en:GenericNode {type:"CFGEntryNode"})
            RETURN en.functionId AS id, fl.code AS filepath, fn.code AS name
        """
        return self.neo4j_db.run(list_entrypoints_cmd).data()

    def get_flowgraph_list_for_entrypoint(self, entrypoint):
        # Returns all control flows throughout all test cases. Each flow or
        # path has a hopefully unique random ID path_id. Steps of each path
        # are returned on separate, sequential rows. Paths have to be put back
        # together later on using their path_id. Each row contains the following:
        #  - path_id.: random ID that identifies a path
        #  - sink....: label describing if a particular node leads is a sink
        #  - id......: Neo4j ID of each step/node in the path
        #  - ast.....: ASTv3 of the current step/node in the path
        #  - iorder..: inflow variable names in order of use
        #  - inflow..: list of data flow input nodes described as follows:
        #      + ast.: ASTv3 of the source node
        #      + var.: variable name of the particular data flow
        #      + size: size of the variable, if known
        #  - outflow.: list of known output data flow sizes of the current node
        flowgraph_command = """
            MATCH p1=(entry:UpstreamNode {type:"CFGEntryNode"})-[:FLOWS_TO*]->(exit:GenericNode)
            WHERE entry.functionId="%s" AND NOT (exit)-[:FLOWS_TO]->()
            WITH p1, randomUUID() AS path_id
            UNWIND NODES(p1) AS n
            WITH path_id, n, "BugSinkNode" IN LABELS(n) AS sink
            MATCH p2=(n)-[:IS_AST_PARENT*]->(identifier:GenericNode {type:"Identifier"})
            WITH path_id, sink, n, identifier.code AS ivar ORDER BY REDUCE(gentree="", g IN NODES(p2) | gentree+TOSTRING(g.childNum))
            WITH path_id, sink, n, COLLECT(ivar) AS iorder
            OPTIONAL MATCH (n)<-[inflow_r:REACHES]-(inflow_n)
            OPTIONAL MATCH (n)-[outflow_r:REACHES]->()
            WITH DISTINCT path_id, sink, n, iorder, inflow_n, PROPERTIES(inflow_r) AS inflow_r, PROPERTIES(outflow_r) AS outflow_r
            WHERE inflow_r IS NOT NULL OR outflow_r IS NOT NULL
            RETURN path_id, sink, id(n) AS id, n.ast AS ast, iorder, COLLECT(DISTINCT [inflow_n.ast, inflow_r.var, inflow_r.size]) AS inflow, COLLECT(DISTINCT outflow_r.size) AS outflow
        """
        return self.neo4j_db.run(flowgraph_command % entrypoint["function_id"]).data()

    def extract_features_worker(self, args):
        # Extract all annotated control flows for a particular test case
        seqs = {}
        try:
            # Retrieve the annotated control flows
            paths = self.get_flowgraph_list_for_entrypoint(args)

            # Process the results by cleaning them up, rearranging them by
            # path, and updating the feature map.
            for step in paths:

                # Clean up empty fields
                if step["inflow"] == [[None, None, None]]:
                    step["inflow"] = []

                # Consolidate the inflows per variable name and size
                AST, VAR, SIZ = 0, 1, 2
                ivars = {}
                for inflow in step["inflow"]:
                    # FIXME We discard pointer/reference indicators and consider
                    # a pointer to a variable the same as the variable itself
                    # Note: return values from function calls are None
                    ivar = (
                        inflow[VAR].split(" ")[-1] if inflow[VAR] is not None else None
                    )
                    if ivar in ivars:
                        # This variable is already known, handle its size
                        if inflow[SIZ] is not None:
                            if ivars[ivar]["size"] == 0:
                                # Size was unknown until now, update it
                                ivars[ivar]["size"] = inflow[SIZ]
                            else:
                                # Ensure the size of this inflow is the
                                # same as any size previously recorded
                                assert inflow[SIZ] == ivars[ivar]["size"]
                        # Add the inflow node to the list for this variable
                        if inflow[AST] not in ivars[ivar]["nodes"]:
                            ivars[ivar]["nodes"].append(inflow[AST])
                    else:
                        # New variable, create a new entry
                        ivars[ivar] = {
                            "size": 0 if inflow[SIZ] is None else inflow[SIZ],
                            "nodes": [inflow[AST]],
                        }
                # Store the inflows in the order they are used by the node
                step["inflow"] = [ivars[iv] for iv in step["iorder"] if iv in ivars]

                # Add the step to the path
                path_id = step["path_id"]
                del step["path_id"]
                if not path_id in seqs:
                    seqs[path_id] = []
                seqs[path_id].append(step)

                # Add the feature to the category catalog
                cat = step["ast"]
                inflow = len(step["inflow"])
                if inflow > 3:
                    LOGGER.warning(
                        f"Large inflow for path {path_id}: node={step['id']} "
                        f"ast={step['ast']} inflow={step['inflow']}. "
                        f"Check that the test case has been fully processed "
                        f"or that this is not another Joern bug."
                    )
                with self.catlock:
                    if cat in self.cats:
                        if inflow not in self.cats[cat]:
                            self.cats[cat].append(inflow)
                    else:
                        self.cats[cat] = [inflow]
        except Exception as e:
            LOGGER.warning(f"Error processing testcase {args['filepath']}: {e}")
        return seqs

    def extract_features(self):
        # Retrieve the entry point (main) of each test case
        entrypoint_list = self._get_entrypoint_list()

        if len(entrypoint_list) == 0:
            LOGGER.warning("No entrypoint found. Returning None...")
            return None

        LOGGER.info(
            f"Retrieved {len(entrypoint_list)} "
            f"entrypoints. Querying for flowgraphs..."
        )

        # Extract features from each test case in a separate thread
        with ThreadPoolExecutor(max_workers=POOL_SIZE) as executor:
            # res = executor.map(self.extract_features_worker, entrypoint_list)
            res = thread_map(self.extract_features_worker, entrypoint_list)
            features = {k: v for d in res for k, v in d.items()}

        LOGGER.info(f"Retrieved {len(features)} paths.")

        return features

    def send_commands(self):
        super().send_commands()
        LOGGER.debug("Extracting features...")
        self.check_extraction_inputs()
        features = self.extract_features()
        self.write_extraction_outputs(features)

    def check_extraction_inputs(self):
        # Check if the "features" directory exists. Create it if it does not.
        if not exists(self.dataset.feats_dir):
            mkdir(self.dataset.feats_dir)
        return join(self.dataset.feats_dir, "interproc-features.json")

    def write_extraction_outputs(self, features):
        output_file = join(self.dataset.feats_dir, "interproc-features.json")
        with open(output_file, "w") as json_file:
            json.dump(features, json_file, sort_keys=True, indent="  ")

        featmap_file = join(self.dataset.feats_dir, "interproc-feature-map.json")
        with open(featmap_file, "w") as json_file:
            json.dump(self.cats, json_file, sort_keys=True, indent="  ")
