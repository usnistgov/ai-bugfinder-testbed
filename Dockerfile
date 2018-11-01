FROM neepl/joern:latest

RUN apt-get install -y python-scipy

CMD echo 'Importing code... ' \
    && java -jar /joern/bin/joern.jar . \
    && echo 'done' \
    && /var/lib/neo4j/bin/neo4j start \
    && /var/lib/neo4j/bin/neo4j status \
    && echo -n 'Computing embeddings... ' \
    && /usr/local/bin/joern-stream-apiembedder -d /code/embeddings \
    && echo 'done' \
    && /var/lib/neo4j/bin/neo4j stop

