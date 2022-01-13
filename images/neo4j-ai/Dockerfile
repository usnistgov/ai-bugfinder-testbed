FROM neo4j:3.5

ARG ZIP_FILE="/tmp/neo4j-shell-tools.zip"
ARG LIB_FOLDER="/var/lib/neo4j/lib"

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        unzip wget parallel \
    && rm -rf \
        /var/lib/apt/lists/* \
        ${LIB_FOLDER}/opencsv-2.3.jar \
    && wget http://dist.neo4j.org/jexp/shell/neo4j-shell-tools_3.0.1.zip \
        -O ${ZIP_FILE} \
    && unzip ${ZIP_FILE} -d ${LIB_FOLDER} \
    && wget https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/3.5.0.11/apoc-3.5.0.11-all.jar \
      -O /var/lib/neo4j/plugins/apoc-3.5.0.11-all.jar
