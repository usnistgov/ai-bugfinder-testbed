# AI Bugfinder

## Disclaimer

This installation has been tested on Ubuntu 18.04LTS systems. The command
listed in this README file should be adapted depending on the system used.

## Pre-requisites 

* APT packages:
    * `unzip`
* Docker: https://docs.docker.com/install/#supported-platforms
* Python 3.6: https://www.python.org/downloads/release/python-369/
* Virtual environment:
	* With `venv`: https://virtualenv.pypa.io/en/stable/installation/
	* With `conda`: https://conda.io/docs/user-guide/install/index.html
	
Once the Python environment is setup and the repository downloaded, run 
`pip install -r requirements.txt`.

## Installation

### Download the Juliet dataset

Using the `download_juliet.sh` located in the **scripts/** folder, download the 
[Juliet Dataset for C/C++](https://samate.nist.gov/SRD/testsuite.php). The 
testcases will be split between healthy (good) and buggy (bad) code. The 
dataset is stored in the **data/juliet_orig/** folder and the annotated data 
are stored in **data/juliet_annot/**.

To only download the CWE-121 data, please use `./scripts/download_cwe121.sh`.

### Build the docker images

The necessary docker images can be built using `python ./build_images.py`.
Three images should be built:
* *joern-lite:0.3.1*: Latest release of Joern (11/21/2011).
* *joern-lite:0.4.0*: Latest code update from Joern (04/12/2017).
* *neo4j-ai:latest*: Neo4J v3 image package with additional shell tools.
* *right-fixer:latest*: Tool to modify rights of a given folder.

## Usage

Several scripts are available in this repository to manipulate datasets and
train a machine learning model to identify bugs in source code. The scripts are
written in python and, for every script, help is available by typing 
`python ./script.py --help`.

### Dataset utilities

Utilities scripts operates on the dataset folder and do not modify the data 
that it contains. The two utilities available are:
* `copy_dataset.py` to duplicate an existing dataset to another location.
* `extract_dataset.py` to extract a defined number of samples from a dataset.

Examples:
```bash
python ./copy_dataset.py \
    -i /path/to/existing_dataset \  # Input argument
    -o /path/to/new_dataset \  # Output argument
    -f  # Override directory if it already exists

python ./extract_dataset.py \
    -i /path/to/existing_dataset \  # Input argument
    -o /path/to/new_dataset \  # Output argument
    -n 200  # Extract 200 samples from original dataset
    -f  # Override directory if it already exists
```

### Prepare the dataset

There are several issues with the default Juliet dataset:
* C++ cannot be parsed correctly by *Joern*, these samples need to be remove 
from the dataset.
* *Joern* is not able to perfectly parse the C samples from *Juliet*. Instances 
of the code left unparsed need to be replaced by an equivalent code line that 
*Joern* can parse.
* In *Juliet*, `main(...)` functions are used to compile the correct (good or 
bad) code depending on pre-processor variables. These functions are not useful
and possible misleading for the classifier, they need to be removed.
* The current version of the tool does not work with interprocedural test 
cases which need to be removed from the dataset.

To handle all of these issues, the `clean_dataset.py` script is available and
works as such:
```bash
python ./clean_dataset.py /path/to/dataset \
    --no-cpp \  # Remove CPP test cases
    --no-interprocedural \  # Remove interprocedural test cases
    --no-litterals \  # Replace litterals from C code
    --no-main  # Remove main functions
```

### Run Joern

[Joern](http://mlsec.org/joern/index.shtml) then needs to be executed with the
script `run_joern.py`. Once the execution is done, the  *.joernIndex* is 
moved to *data/graph.db*. A Neo4j DB then loads the data for further 
processing.

Run the tool with `python ./run_joern.py /path/to/dataset -v ${JOERN_VERSION}`.
Use `--help` to see which version are available.

### AST Markup

The next step is to add labels to the nodes and build the AST notation for 
feature extraction. Run the following command to enhance the dataset with the
additional markup:
```bash
python ./ast_markup.py /path/to/dataset \
    -v ${AST_VERSION}  # AST markup version. See --help for details.
```

### Extract feature

Several feature extractors have been created for this classification task. The 
features need to be extracted with the following command:
```bash
# Create the feature maps
python ./extract_features.py /path/to/dataset \
    -e ${FEATURE_EXTRACTOR} \  # Choose a feature extractor.
    -m  # To create the feature maps.

# Run the extractor and apply PCA to reduce dimensionality
python ./extract_features.py /path/to/dataset \
    -e ${FEATURE_EXTRACTOR} \  # Choose a feature extractor
    -p ${VECTOR_LENGTH}  # Specify the final number of features
``` 

### Run model training

The last step is to train the model. Execute the TensorFlow script by typing:
```bash
python ./run_tensorflow.py /path/to/dataset \
    -m ${MODEL}  # Model to train. See help for details.
```

## Troubleshooting

The dataset is fairly important in size. Once loaded in Neo4j, executing the 
commands could be difficult. There are few tweaks that could facilitate the
training.

### More memory in Neo4J

If Neo4J container are crashing because they do not have enough memory, change
the setting `NEO4J_V3_MEMORY` in *tools/settings.py*.
