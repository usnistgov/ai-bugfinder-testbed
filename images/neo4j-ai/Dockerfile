FROM neo4j:3.5.0

ARG ZIP_FILE="/tmp/neo4j-shell-tools.zip"
ARG LIB_FOLDER="/var/lib/neo4j/lib"

RUN wget http://dist.neo4j.org/jexp/shell/neo4j-shell-tools_3.0.1.zip -O ${ZIP_FILE} \
    && rm -rf ${LIB_FOLDER}/opencsv-2.3.jar \
    && unzip ${ZIP_FILE} -d ${LIB_FOLDER}
