#!/bin/sh
CHOWN_IDS=$(stat -c "%u:%g" /code)
java -Xmx4G -jar /usr/local/bin/joern.jar -outdir /code/joern.db /code
chown -R ${CHOWN_IDS} /code
