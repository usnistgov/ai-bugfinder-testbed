# AI Bugfinder

## Pre-requisites

* Docker: https://docs.docker.com/install/#supported-platforms
* Python 2.7: https://www.python.org/download/releases/2.7/
* Virtual environment:
	* With `venv`: https://virtualenv.pypa.io/en/stable/installation/
	* With `conda`: https://conda.io/docs/user-guide/install/index.html
	
Once the Python environment is setup, run `pip install -r requirements.txt`


## Installation

### Download the Juliet dataset

Using the `download-juliet.sh` located in the **tools/** folder, download the 
[Juliet Dataset for C/C++](https://samate.nist.gov/SRD/testsuite.php). The 
testcases will be split between healthy (good) and buggy (bad) code. The 
dataset is stored in the *data/cwe121_orig/* folder and the annotated data are 
stored in *data/cwe121_annot/*.

### Build the docker images

The necessary docker images can be built using `python tools/build_images.py`.
Three images should be built:
* *joern-lite:0.3.1*: The latest release of Joern (released on 11/21/2011).
* *joern-lite:0.4.0*: The latest code from Joern (pushed on 04/12/2017).
* *neo4j-ai:latest*: A Neo4J v3 image package with additional shell tools.

### Run Joern

[Joern](http://mlsec.org/joern/index.shtml) then needs to be executed with the 
script `run-joern.sh`. Once the execution is done, the  *.joernIndex* is moved 
to *data/graph.db*. A Neo4j DB then loads the data for further processing.

### Enhance the dataset

At this point, use the neo4j shell (`docker exec -it neo4j-ai bin/neo4j-shell`)
or connect to the web interface listening on **port 7474** to run the following
commands:

```bash
$ match (n) set n:GenericNode

$ create index on :GenericNode(type)
$ create index on :GenericNode(filepath)

$ match (root1:GenericNode)-[:FLOWS_TO|REACHES|CONTROLS]->()
  where root1.type in [ 'Condition', 'ForInit', 'IncDecOp',
    'ExpressionStatement', 'IdentifierDeclStatement', 'CFGEntryNode',
	'BreakStatement', 'Parameter', 'ReturnStatement', 'Label',
	'GotoStatement', 'Statement', 'UnaryExpression' ]
  set root1:UpstreamNode
  
$ match ()-[:FLOWS_TO|REACHES|CONTROLS]->(root2:GenericNode)
  where root2.type in [ 'CFGExitNode', 'IncDecOp', 'Condition',
    'ExpressionStatement', 'ForInit', 'IdentifierDeclStatement',
	'BreakStatement', 'Parameter', 'ReturnStatement', 'Label',
	'GotoStatement', 'Statement', 'UnaryExpression' ]
  set root2:DownstreamNode
```

### Extract the feature and run Tensorflow

The features need to be extracted using `python extract-features-from-db.py`. 
Resulting features will be stored in *data/features*. Lastly, execute 
TensorFlow by typing `python run-tensorflow.py`. The trained network is stored
in *data/neuralnet*.


## Troubleshooting

The dataset is fairly important in size. Once loaded in Neo4j, executing the 
commands could be fairly difficult. There are few tweaks that could ease this
process.


### More memory

Tweak the environment variables in the `docker-compose.yml` file to allow Neo4j
to use more memory.


### Split queries

Queries can be split to be executed in less time. Here are the commands that
could be used:

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
