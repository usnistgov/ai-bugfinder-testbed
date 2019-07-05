"""
"""
import os
from os.path import join

import numpy
from scipy.io import mmwrite
from scipy.sparse import lil_matrix, vstack, hstack

COMMANDS = {
    "list_testcases": """
        MATCH (f {type:"File"})-[:IS_FILE_OF]->(n {type:"Function"}) 
        WHERE n.code<>"main"
        RETURN id(n) AS id, f.code AS filepath, n.code AS name
    """,
    "list_entrypoint": """
        MATCH (f)-[:IS_FUNCTION_OF_CFG]->(entry {type:'CFGEntryNode'})
        WHERE id(f)=%d
        RETURN id(entry) AS id
    """,
    "get_flowgraphs": """
        MATCH (entry)-[:FLOWS_TO|REACHES|CONTROLS*0..5]->(root1:UpstreamNode)
        WHERE id(entry)=%d
        WITH distinct root1
        MATCH 
            p=(root1)-[:FLOWS_TO|REACHES|CONTROLS*1..3]->(root2:DownstreamNode)
        WHERE root1<>root2
        WITH extract(r in relationships(p) | type(r)) as flow, 
            root1.ast as source, root2.ast as sink
        RETURN source, flow, sink
    """
}


def extract_features(neo4j_db, data_dir):
    # Dictionary taking a flattened flow graph as key and an index as value for
    # reverse-lookup
    unique_graph_lookup = {}

    # A sparse matrix to store the number of occurrences of each flow graph for
    # each test case
    features = lil_matrix((8, 8))

    # A list keeping track of whether a test case is good or bad
    labels = []

    # Test case index
    testcase_index = 0

    print "Retrieving test cases from the database..."

    # Get a list of all test cases in the database
    testcase_list = neo4j_db.run(COMMANDS["list_testcases"]).data()
    print "%d test cases to process..." % len(testcase_list)

    # For each test case, extract interesting flow graphs
    for testcase in testcase_list:
        print "Processing test case %d/%d (%d%%)\t" \
              "Matrix size: %dx%d\tTestcase: %s\t(%s)" % \
              (
                  testcase_index + 1, len(testcase_list),
                  100 * (testcase_index + 1) / len(testcase_list),
                  features.shape[0], features.shape[1],
                  testcase['filepath'].split('/')[-1],
                  testcase['filepath'].split('/')[3] + "." + testcase["name"]
              )

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
        entrypoint_list = neo4j_db.run(
            COMMANDS["list_entrypoint"] % testcase['id']
        ).data()

        # Get the interesting flow graphs for each function
        for entrypoint in entrypoint_list:
            flowgraph_list = neo4j_db.run(
                COMMANDS["get_flowgraphs"] % entrypoint['id']
            ).data()

            # Record and count each unique flow graph
            for flowgraph in flowgraph_list:

                source = flowgraph["source"]
                sink = flowgraph["sink"]
                flow = ':'.join(flowgraph["flow"])

                key = "%s-[%s]->%s" % (source, flow, sink)

                # Add the current graph to the books if it's new
                if key not in unique_graph_lookup.keys():
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
    graphs = [""] * len(unique_graph_lookup.keys())
    for unique_graph in unique_graph_lookup.keys():
        graphs[unique_graph_lookup[unique_graph]] = unique_graph

    print "Summary: analyzed %d test cases, extracting %d unique features" % \
          (testcase_index, len(unique_graph_lookup))

    # Create feature directory
    features_dir = join(data_dir, "features")

    if not os.path.exists(features_dir):
        os.mkdir(features_dir)

    # Write data to disk in sparse format (Matrix Market)
    mmwrite(join(features_dir, "features.mtx"), features, field="integer")

    # Write data to disk in dense format
    numpy.savetxt(
        join(features_dir, "graphs.txt"), graphs, delimiter="\n", fmt="%s"
    )
    numpy.savetxt(
        join(features_dir, "labels.txt"), labels, delimiter=",", fmt="%s"
    )

