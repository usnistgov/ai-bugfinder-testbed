#!/usr/bin/env bash
# Example script for dataset processing.
#
dataset_main="/path/to/dataset.in"
dataset="/path/to/dataset.out"

# Extract 50 samples from the dataset.
python ./extract_dataset.py \
  -i ${dataset_main} \
  -o ${dataset} \
  -n 50 -f
# Cleanup the dataset by removing C++ files and replacing litterals.
python ./clean_dataset.py ${dataset} \
  --no-cpp --no-main --no-litterals
# Run version 0.4.0 of the Joern processor.
python ./run_joern.py ${dataset} -v0.4.0
# Use AST markup v2 to annotate the graph.
python ./run_ast_markup.py ${dataset} -v2
# Run feature extraction.
python ./run_feature_extraction.py ${dataset} -e shr -m
python ./run_feature_extraction.py ${dataset} -e shr
## Run model training and display metrics.
python ./run_model_training.py \
  -m linear_classifier -n lin_cls \
  ${dataset}