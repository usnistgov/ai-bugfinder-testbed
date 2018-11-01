#!/bin/bash
DIR_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
DATA_PATH="${DIR_PATH}/data/annot"

docker build . -t joern-test
docker run -v ${DATA_PATH}:/code --rm -w /code joern-test:latest

# The DB has been created with root user
sudo mv ${DATA_PATH}/.joernIndex ${DATA_PATH}/../graph.db

# Create a dump of the original env 
if [ -f ${DIR_PATH}/.env.dump ]
then
  cp ${DIR_PATH}/.env.dump ${DIR_PATH}/.env
else
  cp ${DIR_PATH}/.env ${DIR_PATH}/.env.dump
fi

sed -i \
  -e 's;@DATA_DIR@;'"${DIR_PATH}"'/data/graph.db;' \
  ${DIR_PATH}/.env

docker-compose down \
  && docker-compose up -d

