"""
"""
import csv
import os
from os.path import join

from hashlib import sha256

import numpy
from past.utils import old_div
from scipy.io import mmwrite
from scipy.sparse import lil_matrix, vstack, hstack

from tools.neo4j import Neo4J3Processing
from tools.settings import LOGGER


class ExtractorRelCountMulti(Neo4J3Processing):
    COMMANDS = {
        "list_testcases": """
            MATCH (f {type:"File"})-[:IS_FILE_OF]->(n {type:"Function"}) 
            WHERE n.code<>"main"
            RETURN id(n) AS id, f.code AS filepath, n.code AS name
        """,
        "list_entrypoint": """
            MATCH (f)-[:IS_FUNCTION_OF_CFG]->(entry {type:'CFGEntryNode'})
            WHERE id(f)=%d
            RETURN entry.functionId AS id
        """,
        "get_flowgraphs": """
            MATCH (entry)-[:FLOWS_TO|REACHES|CONTROLS*0..5]->(root1:UpstreamNode)
            WHERE entry.functionId="%s"
            WITH distinct root1
            MATCH 
                p=(root1)-[:FLOWS_TO|REACHES|CONTROLS*1..3]->(root2:DownstreamNode)
            WHERE root1<>root2
            WITH extract(r in relationships(p) | type(r)) as flow, 
                root1.ast as source, root2.ast as sink
            RETURN source, flow, sink
        """
    }

    def configure_container(self):
        super().configure_container()
        self.container_name = "fe-rel-count-multi"

    def send_commands(self):
        super().send_commands()

        # Dictionary taking a flattened flow graph as key and an index as value for
        # reverse-lookup
        unique_graph_lookup = {}

        # A sparse matrix to store the number of occurrences of each flow graph for
        # each test case
        features = lil_matrix((8, 8))
        # features = list()

        # A list keeping track of whether a test case is good or bad
        labels = []

        # Test case index
        testcase_index = 0

        # Get a list of all test cases in the database
        testcase_list = self.neo4j_db.run(
            self.COMMANDS["list_testcases"]
        ).data()

        # Keep track of the progress made
        last_progress = 0

        # For each test case, extract interesting flow graphs
        for testcase in testcase_list:
            progress = int(100 * (testcase_index + 1) / len(testcase_list))

            if progress > 0 and progress % 10 == 0:
                if progress > last_progress:
                    LOGGER.info(
                        "Processed %d%% of the dataset (%d test cases)." %
                        (progress, len(testcase_list))
                    )
                    last_progress = progress
            # LOGGER.info(
            #     "Processing test case %d/%d (%d%%)\tMatrix size: %dx%d\t"
            #     "Testcase: %s\t(%s)" % (
            #         testcase_index + 1, len(testcase_list),
            #         old_div(100 * (testcase_index + 1), len(testcase_list)),
            #         features.shape[0], features.shape[1],
            #         testcase['filepath'].split('/')[-1],
            #         testcase['filepath'].split('/')[3] + "." + testcase["name"]
            #         )
            # )

            # Keep track of whether the current test case is good or bad, along with
            # the test case name
            labels.append([
                testcase['filepath'].split('/')[2] == 'good',
                testcase['filepath'].split('/')[-1]
            ])

            # Increase the height of the vector matrix if necessary
            # (to store more test case features)
            if features.shape[0] <= testcase_index:
                features = lil_matrix(
                    vstack([
                        features,
                        lil_matrix((features.shape[0], features.shape[1]))
                    ])
                )

            # To speed things up, collect the entry points
            entrypoint_list = self.neo4j_db.run(
                self.COMMANDS["list_entrypoint"] % testcase['id']
            ).data()

            # Get the interesting flow graphs for each function
            for entrypoint in entrypoint_list:
                flowgraph_list = self.neo4j_db.run(
                    self.COMMANDS["get_flowgraphs"] % entrypoint['id']
                ).data()

                # Record and count each unique flow graph
                for flowgraph in flowgraph_list:

                    source = flowgraph["source"]
                    sink = flowgraph["sink"]
                    flow = ':'.join(flowgraph["flow"])

                    key = "%s-[%s]->%s" % (source, flow, sink)

                    # Add the current graph to the books if it's new
                    if key not in list(unique_graph_lookup.keys()):
                        # Increase the width of the vector matrix if necessary
                        # (to store counts for more types of graphs)
                        if features.shape[1] <= len(unique_graph_lookup):
                            features = lil_matrix(hstack([
                                features,
                                lil_matrix((features.shape[0], features.shape[1]))
                            ]))

                        # Add the new graph
                        unique_graph_lookup[key] = len(unique_graph_lookup)

                    # Increment the count for the current graph in the current test
                    # case's vector
                    features[testcase_index, unique_graph_lookup[key]] += 1

            # Increment the test case index
            testcase_index += 1

        # Reduce the vector matrix to its useful size
        features = features[:testcase_index, :len(unique_graph_lookup)]

        # Reverse the flow graph dictionary for storage
        graphs = [""] * len(list(unique_graph_lookup.keys()))
        for unique_graph in list(unique_graph_lookup.keys()):
            graphs[unique_graph_lookup[unique_graph]] = unique_graph

        LOGGER.info(
            "Summary: analyzed %d test cases, extracting %d unique features" % (
                testcase_index, len(unique_graph_lookup)
            )
        )

        if not os.path.exists(self.dataset.feats_dir):
            os.mkdir(self.dataset.feats_dir)

        # # Write data to disk in sparse format (Matrix Market)
        # mmwrite(join(self.dataset.feats_dir, "features.mtx"), features, field="integer")
        #
        # # Write data to disk in dense format
        # numpy.savetxt(
        #     join(self.dataset.feats_dir, "graphs.txt"), graphs, delimiter="\n", fmt="%s"
        # )
        # numpy.savetxt(
        #     join(self.dataset.feats_dir, "labels.txt"), labels, delimiter=",", fmt="%s"
        # )

        with open(join(self.dataset.feats_dir, "features.csv"), "w") as csv_file:
            csv_writer = csv.writer(csv_file)

            csv_writer.writerow(["result", "name"] + [
                "f.%s" % sha256(feat.encode("utf-8")).hexdigest()
                for feat in graphs
            ])
            csv_writer.writerows(
                numpy.hstack((
                    numpy.array(labels),
                    features.toarray()
                ))
            )
