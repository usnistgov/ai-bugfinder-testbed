#!/bin/bash
# Script copying the AI-bugfinder dataset from
# https://gitlab.nist.gov/gitlab/samate/ai-dataset
#
# ==============================================================================
# Script parameters
CURRENT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
DATASET_NAME="ai-dataset"
ORIG_PATH="${CURRENT_PATH}/${DATASET_NAME}.tar.xz"

DATA_PATH="${CURRENT_PATH}/../data"
DEST_PATH="${DATA_PATH}/ai-dataset_orig"
#
# ==============================================================================
# Remove destination path if it already exists
if [[ -d ${DEST_PATH} ]]
then
  rm -rf ${DEST_PATH}
fi

mkdir -p ${DATA_PATH}

# Copy the dataset in the data folder and name it correctly
tar -xf ${ORIG_PATH} -C ${DATA_PATH}
mv "${DATA_PATH}/${DATASET_NAME}" ${DEST_PATH}


