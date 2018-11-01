#!/usr/bin/python
from py2neo import Graph
from scipy.sparse import lil_matrix, vstack, hstack
from scipy.io import mmwrite
import numpy
import os

# Dictionary taking a flattened flow graph as key and an index as value for reverse-lookup
unique_graph_lookup = {}

# A sparse matrix to store the number of occurrences of each flow graph for each test case
features = lil_matrix((8, 8))

# A list keeping track of whether a test case is good or bad
labels = []

# Test case index
testcase_index = 0

# Neo4j database pre-loaded with Joern
db = Graph(
    scheme="http",
    host="0.0.0.0",
    port=7474
)

print "Retrieving test cases from the database..."

# Get a list of all test cases in the database
cql_get_testcase_list = """
    match (dir {type:'Directory'})
    where dir.filepath=~".*__[^/]*"
    return id(dir) as id, dir.filepath as filepath
    order by dir.filepath
"""

testcase_list = db.run(cql_get_testcase_list).data()

print "%d test cases to process..." % len(testcase_list)

# For each test case, extract interesting flow graphs
for testcase in testcase_list:

    print "Processing test case %d/%d (%d%%)\tMatrix size: %dx%d\tTestcase: %s\t(%s)" % \
          (testcase_index + 1, len(testcase_list), 100 * (testcase_index + 1) / len(testcase_list),
           features.shape[0], features.shape[1],
           testcase['filepath'].split('/')[-1], testcase['filepath'].split('/')[3])

    # Keep track of whether the current test case is good or bad, along with the test case name
    labels.append([testcase['filepath'].split('/')[3] == 'good', testcase['filepath'].split('/')[-1]])

    # Increase the height of the vector matrix if necessary
    # (to store more test case features)
    if features.shape[0] <= testcase_index:
        # features = features.reshape(tuple([2 * features.shape[0], features.shape[1]]))
        features = lil_matrix(vstack([features, lil_matrix((features.shape[0], features.shape[1]))]))

    # To speed things up, collect the entry points
    # of each function of the current test case
    cql_get_entrypoint_list = "match " + \
                              "(dir {type:'Directory'})-[:IS_PARENT_DIR_OF]->" + \
                              "({type:'File'})-[:IS_FILE_OF]->" + \
                              "({type:'Function'})-[:IS_FUNCTION_OF_CFG]->" + \
                              "(entry {type:'CFGEntryNode'})" + \
                              "where id(dir)=%d " % testcase['id'] + \
                              "return id(entry) as id"

    entrypoint_list = db.run(cql_get_entrypoint_list).data()

    # Get the interesting flow graphs for each function
    for entrypoint in entrypoint_list:

        cql_get_flowgraphs = """
            match (entrypoint {type:'CFGEntryNode'})-[r:FLOWS_TO|REACHES|CONTROLS*0..5]->(root1:UpstreamNode)
            where id(entrypoint)=%d
            with distinct root1
            match (root1:UpstreamNode)-[mr:FLOWS_TO|REACHES|CONTROLS*1..3]->(root2:DownstreamNode)
            where root1<>root2
            with extract(r in mr | type(r)) as flow, root1, root2
            match (root1)-[:IS_AST_PARENT*]->(sub1)
            with flow, root1, root2, sub1 order by id(sub1)
            with flow, root1, root2, collect(sub1.type) as source
            match (root2)-[:IS_AST_PARENT*]->(sub2)
            with flow, root1, root2, source, sub2 order by id(sub2)
            with flow, root1, root2, source, collect(sub2.type) as sink
            return source, flow, sink
        """ % entrypoint['id']

        flowgraph_list = db.run(cql_get_flowgraphs).data()

        # Record and count each unique flow graph
        for flowgraph in flowgraph_list:

            source = ':'.join(flowgraph['source'])
            sink = ':'.join(flowgraph['sink'])
            flow = ':'.join(flowgraph['flow'])

            key = source + '-[' + flow + ']->' + sink

            # Add the current graph to the books if it's new
            if key not in unique_graph_lookup:
                # Increase the width of the vector matrix if necessary
                # (to store counts for more types of graphs)
                if features.shape[1] <= len(unique_graph_lookup):
                    # features = features.reshape(tuple([features.shape[0], 2 * features.shape[1]]))
                    features = lil_matrix(hstack([features, lil_matrix((features.shape[0], features.shape[1]))]))
                # Add the new graph
                unique_graph_lookup[key] = len(unique_graph_lookup)

            # Increment the count for the current graph in the current test case's vector
            features[testcase_index, unique_graph_lookup[key]] += 1

    # Increment the test case index
    testcase_index += 1

# Reduce the vector matrix to its useful size
features = features[:testcase_index, :len(unique_graph_lookup)]

# Reverse the flow graph dictionary for storage
graphs = [None] * len(unique_graph_lookup)
for graph in unique_graph_lookup:
    graphs[unique_graph_lookup[graph]] = graph

print "Summary: analyzed %d test cases, extracting %d unique features" % (testcase_index, len(unique_graph_lookup))

# Create feature directory
if not os.path.exists("./data/features"):
    os.mkdir("data/features")

# Write data to disk in sparse format (Matrix Market)
mmwrite('data/features/features.mtx', features, field='integer')

# Write data to disk in dense format
numpy.savetxt('data/features/graphs.txt', graphs, delimiter='\n', fmt='%s')
numpy.savetxt('data/features/labels.txt', labels, delimiter=',', fmt='%s')

