"""
"""
from __future__ import division

import os
import pickle
from os.path import join

import numpy
from scipy.io import mmwrite
from scipy.sparse import lil_matrix

from settings import LOGGER

FLOWS = {
    "CONTROLS": 0,
    "FLOWS_TO": 1,
    "REACHES": 2,
}

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
        MATCH p = (root1:UpstreamNode)-[:%s*]->(root2:DownstreamNode)
        WHERE root1.functionId="%s"
        RETURN distinct root1.ast AS source, root2.ast AS sink, count(p) as count
    """
}


def extract_features(neo4j_db, data_dir):
    # Get feature info calculated earlier
    with open("./features.bin", "rb") as features_file:
        features_refs = pickle.load(features_file)

    # Test case index
    testcase_index = 0

    LOGGER.info("Retrieving test cases from the database...")

    # Get a list of all test cases in the database
    testcase_list = neo4j_db.run(COMMANDS["list_testcases"]).data()
    LOGGER.info("%d test cases to process..." % len(testcase_list))

    # A sparse matrix to store the number of occurrences of each flow graph for
    # each test case
    features = lil_matrix((len(testcase_list), len(features_refs)), dtype=float)

    # A list keeping track of whether a test case is good or bad
    labels = []

    # For each test case, extract interesting flow graphs
    for testcase in testcase_list:
        LOGGER.info(
            "Processing %d/%d (%d%%)\tMatrix: %dx%d\tTestcase: %s" %
            (
                testcase_index + 1, len(testcase_list),
                100 * (testcase_index + 1) / len(testcase_list),
                features.shape[0], features.shape[1],
                testcase["name"]
            )
        )

        # Keep track of whether the current test case is good or bad, along with
        # the test case name
        labels.append([
            testcase['filepath'].split('/')[2] == 'good',
            testcase['filepath'].split('/')[-1]
        ])

        # To speed things up, collect the entry points
        entrypoint_list = neo4j_db.run(
            COMMANDS["list_entrypoint"] % testcase['id']
        ).data()

        # Get the interesting flow graphs for each function
        for entrypoint in entrypoint_list:
            for flow in list(FLOWS.keys()):
                features_info = dict()
                total_flow = 0

                flowgraph_list = neo4j_db.run(
                    COMMANDS["get_flowgraphs"] % (flow, entrypoint['id'])
                ).data()

                # Record and count each unique flow graph
                for flowgraph in flowgraph_list:

                    source = flowgraph["source"]
                    sink = flowgraph["sink"]

                    feature_ref = "%s-%s-%s" % (source, flow, sink)

                    # Add the current graph to the books if it's new
                    if feature_ref not in features_refs:
                        raise KeyError("Feature %s never seen before" % feature_ref)

                    # Increment the count for the current graph in the current test
                    # case's vector
                    if features_refs not in list(features_info.keys()):
                        features_info[feature_ref] = 0

                    features_info[feature_ref] += flowgraph["count"]
                    total_flow += flowgraph["count"]

                for feature_ref, feature_count in list(features_info.items()):
                    features[testcase_index, features_refs.index(feature_ref)] = \
                        float(feature_count) / float(total_flow)

        # Increment the test case index
        testcase_index += 1

    LOGGER.info("Analyzed %d test cases" % testcase_index)

    # Create feature directory
    features_dir = join(data_dir, "features")

    if not os.path.exists(features_dir):
        os.mkdir(features_dir)

    # Write data to disk in sparse format (Matrix Market)
    # mmwrite(join(features_dir, "features.mtx"), features, field="integer")
    mmwrite(join(features_dir, "features.mtx"), features)

    numpy.savetxt(
        join(features_dir, "labels.txt"), labels, delimiter=",", fmt="%s"
    )
