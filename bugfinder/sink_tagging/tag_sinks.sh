#!/bin/bash

# Run this from the repository root
# FIXME This is limited to CWE121. To change it, edit the grep command below.

# Start the neo4j container if necessary
docker-compose -f bugfinder/interproc/docker-compose.yml up -d

# Wait a bit to make sure neo4j is up and running
sleep 60

# Limit the number of processes to 32
NP=$(nproc)
if (($NP > 32))
then
  NP=32
fi

# Build cypher queries from the Juliet sink text file
# and run all them in parallel inside the container
cat bugfinder/sink_tagging/juliet.sinks.txt | grep CWE121 | sed 's/^synthetic-c\/testcases\/.*\/\([^\t]*\)\t*\([0-9]*\)\t*.*$/match (:GenericNode {type:\\"Testcase\\",label:\\"bad\\"})<-[:IS_FILE_OF]-(:GenericNode {type:\\"File\\",basename:\\"\1\\"})-[:IS_FILE_OF]->(:GenericNode {type:\\"Function\\"})-[:IS_FUNCTION_OF_CFG]->(e:UpstreamNode {type:\\"CFGEntryNode\\"}) with distinct e match shortestPath((e)-[:CONTROLS*]->(n1:GenericNode)) where e<>n1 and exists(n1.lineno) and n1.lineno=\2-1 set n1:BugSinkNode;/' | docker exec -i interproc_neo4j_1 xargs -I {} -P${NP} cypher-shell {}

