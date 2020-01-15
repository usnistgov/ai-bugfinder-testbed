FROM neo4j:3.5

ARG ZIP_FILE="/tmp/neo4j-shell-tools.zip"
ARG LIB_FOLDER="/var/lib/neo4j/lib"

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        unzip wget \
    && rm -rf \
        /var/lib/apt/lists/* \
        ${LIB_FOLDER}/opencsv-2.3.jar \
    && wget http://dist.neo4j.org/jexp/shell/neo4j-shell-tools_3.0.1.zip \
        -O ${ZIP_FILE} \
    && unzip ${ZIP_FILE} -d ${LIB_FOLDER}
