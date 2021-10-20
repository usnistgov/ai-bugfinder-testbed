#!/usr/bin/env bash
USAGE="$0 \${CONTAINER_NAME} \${DATASET_FOLDER}"

if [[ $# -ne 2 ]]
then
    echo "Illegal number of arguments. Usage: ${USAGE}"
    exit 1
fi

CONTAINER_NAME="$1"
DATABASE_FOLDER="$(realpath $2)/neo4j_v3.db"
echo "Starting container '${CONTAINER_NAME}' with database ${DATABASE_FOLDER}"

docker run -dt --name ${CONTAINER_NAME} \
    -e NEO4J_dbms_memory_pagecache_size=4G \
    -e NEO4J_dbms_memory_heap_max__size=4G \
    -e NEO4J_dbms_allow__upgrade=true \
    -e NEO4J_dbms_shell_enabled=true \
    -e NEO4J_dbms_transaction_timeout=2h \
    -e NEO4J_AUTH=none \
    -p 7474:7474 -p 7473:7473 -p 7687:7687 \
    -v ${DATABASE_FOLDER}:/data/databases/graph.db \
    neo4j-ai:latest