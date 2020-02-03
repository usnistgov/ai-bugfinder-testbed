#!/bin/bash
USAGE="/path/to/convert.sh \${PATH} \${USER} \${GROUP}"

if [[ $# -ne 3 ]]
then
  echo "Not enough parameters."
  exit 1
fi

chown -R $2:$3 $1