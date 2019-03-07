#!/bin/bash
#
#
pyenv="/path/to/my/env"
training_folder="/path/to/training/set"
test_folder="/path/to/test/set"

cleanup=0
joern_version="0.3.1"
markup_version="v01"

source activate ${pyenv}

if [[ "${cleanup}" -eq "1" ]]
then
    python ./tools/prepare_data.py ${training_folder}
    sleep 2
    python ./tools/prepare_data.py ${test_folder}
    sleep 2
fi

python ./tools/run_joern.py ${training_folder} ${joern_version}
sleep 2
python ./tools/run_joern.py ${test_folder} ${joern_version}
sleep 2

python ./tools/ast_markup.py ${training_folder} ${markup_version}
sleep 2
python ./tools/ast_markup.py ${test_folder} ${markup_version}
sleep 2

python ./tools/extract_features.py ${training_folder} ${joern_version}
sleep 2
python ./tools/extract_features.py ${test_folder} ${joern_version}
sleep 2
