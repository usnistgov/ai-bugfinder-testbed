# AI Bugfinder

## Disclaimer

This installation has been tested on a Ubuntu 18.04LTS system. The command
listed in this README file should be adapted in case of use with any other 
system.


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

Using the `download_juliet.sh` located in the **tools/** folder, download the 
[Juliet Dataset for C/C++](https://samate.nist.gov/SRD/testsuite.php). The 
testcases will be split between healthy (good) and buggy (bad) code. The 
dataset is stored in the **data/juliet_orig/** folder and the annotated data 
are stored in **data/juliet_annot/**.

To only download the CWE-121 data, please use `./tools/download_cwe121.sh`.

### Prepare the dataset

C++ cannot be parsed correctly by *Joern*. The samples need to be remove from
the dataset with the command `python tools/filter_cpp_tc.py ${DATA_DIR}`.

*Joern* is not able to perfectly parse the C samples from *Juliet*. To remedy 
this issue, please use `python tools/prepare_data.py ${DATA_DIR}`. It replaces
instances of the code left unparsed by an equivalent code line that Joern is 
able to parse.

Additional dataset scripts are located in the **./tools/dataset/** folder. To
use them, type `PYTHONPATH=./tools python ./dataset/script.py ${ARGS}`. Help is
available for every script to help you design your dataset.

### Build the docker images

The necessary docker images can be built using `python tools/build_images.py`.
Three images should be built:
* *joern-lite:0.3.1*: The latest release of Joern (released on 11/21/2011).
* *joern-lite:0.4.0*: The latest code from Joern (pushed on 04/12/2017).
* *neo4j-ai:latest*: A Neo4J v3 image package with additional shell tools.

### Run Joern

[Joern](http://mlsec.org/joern/index.shtml) then needs to be executed with the
script `run_joern.py`. Once the execution is done, the  *.joernIndex* is 
moved to *data/graph.db*. A Neo4j DB then loads the data for further 
processing.

Run the tool with `python ./tools/run_joern.py ${DATA_DIR} ${JOERN_VERSION}`.

### AST Markup

The next step is to add labels to the nodes and build the AST notation for 
feature extraction. Run `python ./tools/ast_markup.py ${DATA_DIR} ${VERSION}`
to enhance the dataset with the additional markup.

### Extract the feature and run Tensorflow

The features need to be extracted with the following command:
`python ./tools/extract_features.py ${DATA_DIR} ${DATA_VERSION}`. 

Lastly, execute the TensorFlow script `tools/run-tensorflow.py` by typing:
```bash
python tools/run-tensorflow.py \
    ${TRAIN_DIR} ${TEST_DIR} ${NN_DIR} ${NN_STRUCTURE} \
    ${NN_LRATE} ${BATCH_SIZE} ${EPOCH}
```

The trained network is stored in `${NN_DIR}`.


## Troubleshooting

The dataset is fairly important in size. Once loaded in Neo4j, executing the 
commands could be fairly difficult. There are few tweaks that could ease this
process.


### More memory

Tweak the environment variables in the `docker-compose.yml` file to allow Neo4j
to use more memory.


### Split queries

Queries can be split to be executed for bigger datasets. Here are the commands 
that could be used:

```bash
$ match (n) where size(labels(n)) = 0 
  with n skip 0 limit 500000
  set n:GenericNode
  
$ create index on :GenericNode(type)
$ create index on :GenericNode(filepath)

$ match (root1:GenericNode)-[:FLOWS_TO|REACHES|CONTROLS]->()
  where root1.type in [ 'Condition', 'ForInit', 'IncDecOp' ]
  set root1:UpstreamNode
$ match (root1:GenericNode)-[:FLOWS_TO|REACHES|CONTROLS]->()
  where root1.type in [ 'ExpressionStatement', 'IdentifierDeclStatement', 
    'CFGEntryNode' ]
  set root1:UpstreamNode
$ match (root1:GenericNode)-[:FLOWS_TO|REACHES|CONTROLS]->()
  where root1.type in [ 'BreakStatement', 'Parameter', 'ReturnStatement', 
    'Label' ]
  set root1:UpstreamNode
$ match (root1:GenericNode)-[:FLOWS_TO|REACHES|CONTROLS]->()
  where root1.type in [ 'GotoStatement', 'Statement', 'UnaryExpression' ]
  set root1:UpstreamNode

$ match ()-[:FLOWS_TO|REACHES|CONTROLS]->(root2:GenericNode)
  where root2.type in [ 'BreakStatement', 'Parameter', 'ReturnStatement', 
    'Label' ]
  set root2:DownstreamNode
$ match ()-[:FLOWS_TO|REACHES|CONTROLS]->(root2:GenericNode)
  where root2.type in [ 'CFGExitNode', 'IncDecOp', 'Condition' ]
  set root2:DownstreamNode
$ match ()-[:FLOWS_TO|REACHES|CONTROLS]->(root2:GenericNode)
  where root2.type in [ 'ExpressionStatement', 'ForInit', 
    'IdentifierDeclStatement' ]
  set root2:DownstreamNode
$ match ()-[:FLOWS_TO|REACHES|CONTROLS]->(root2:GenericNode)
  where root2.type in [ 'GotoStatement', 'Statement', 'UnaryExpression' ]
  set root2:DownstreamNode
```


### Smaller dataset

The dataset is specified in `download-juliet.sh` under the `${DATASET}` 
variable. To obtain a smaller dataset, specify a subset of the dataset, for
example *.../s01*.
