6. VulGNN
---------

6.1. Pre-requisites
~~~~~~~~~~~~~~~~~~~
This pipeline uses the most recent version of Joern (version 2.0.147) to process the dataset and 
generate the Code Property Graphs. Joern is a tool written in Scala, which means it needs a Java
environment to be executed properly. This pipleline was tested with the OpenJDK version 17, so
if you want to replicate the same environment, run the following steps:

.. code:: bash

    wget https://download.java.net/java/GA/jdk17.0.2/dfd4a8d0985749f896bed50d7138ee7f/8/GPL/openjdk-17.0.2_linux-x64_bin.tar.gz
    tar xvf openjdk-17.0.2_linux-x64_bin.tar.gz
    sudo mv jdk-17.0.2 $PATH_TO_JDK

You can add the JDK into your JAVA_HOME environment variable, or you can just add the $PATH_TO_JDK
into the JAVA_PATH variable in the `settings.py` file.

After having the JDK installed and configured, just download Joern and add the path where Joern
is located in the JOERN_PATH variable in the `settings.py` file.

.. code:: bash
    wget https://github.com/joernio/joern/releases/download/v2.0.107/joern-cli.zip
    unzip joern-cli.zip
    sudo mv joern-cli $PATH_TO_JOERN_CLI

Then, in the `settings.py` file:

.. code:: bash
    JOERN_PATH = $PATH_TO_JOERN_CLI
    JAVA_HOME = $PATH_TO_JDK



6.2. Additional dataset cleaning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's not necessary to do any pre-processing on this pipeline besides removing comments from the source code.
The normalization step is done after the Code Property Graphs are generated, so the clean-up
step on `clean_dataset.py` is not necessary.

.. code:: bash

    python ./scripts/clean_dataset.py ${DATASET} \
        --no-comments  # Remove comments

6.3. Generating the Code Property Graphs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After cleaning the dataset, it's time to generate an intermediate representation 
known as the Code Property Graph. The `new_joern.py` script is responsible to parse
the source code, generate a binary file containing the graphs, and export the desired representation.

Joern supports several languages and output formats for the Code Propery Graphs.
For the VulGNN pipeline, the parameters used are:

language: c
graph_representation: cpg14
output_format: dot

So to generate the necessary graphs for the pipeline, run:

.. code:: bash

    python ./scripts/run_new_joern.py ${DATASET} \
        --language c \ 
        --repr cpg14 \
        --format dot

Do not confuse the `cpg14` representation with `cpg`: using `cpg` will output .dot files in 
a different format and the following normalization step will not work. The normalization step was
tested with exporting the dot files using `cpg14` and `pdg` representations.

6.4. Normalizing the Code Property Graphs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After executing Joern to generate the Code Property Graphs using the parameters described above, 
it's time to execute some processing steps. The expected output from the previous step is a list
of .dot files for each processed sample, stored in the newly created $CPG_DATASET folder.

IMPORTANT: The next steps of the pipeline expects the $CPG_DATASET folder as input, not the $DATASET folder.
Using the $DATASET folder might result in errors.

The processing steps consists of:
- Run a sed command to replace <> by "" on the nodes representation. This is 
done because the normalization process involves transforming the DOT files' 
content into a networkx graph, and by keeping <> around code it bugs out how 
networkx processes the graph.
- Removes bugged HTML tags such as `&lt;` and `&gt;`
- Replaces variables and functions by a generic token (VAR/FUN)

To execute those steps, run:

.. code:: bash

    python ./scripts/clean_dataset.py ${$CPG_DATASET} \
        --normalize-cpg

6.5. Combining all .dot files in a single one
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While exporting the `cpg14` or `pdg` representation, the result will be several .dot files based on
functions/assignments/operations. 

Before generating the embeddings, it's necessary to combine all those graphs in a single one, which
will be saved as `complete-cpg.dot`. This step processes all .dot files using the `networkx`, eliminating
all duplicated edges.

To execute this step, run:

.. code:: bash

    python ./scripts/clean_dataset.py ${$CPG_DATASET} \
        --combine-cpg

6.6. Generating the embeddigs for the VulGNN model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After finishing the necessary cleaning/normalization steps, the result is a single .dot file containing
the combined graph representation. This step is responsible to process the CPG and generate embeddings
using a Transformer model (CodeBERT as default). The result is a `torch` Data object containing the 
nodes/edges information, which is serialized in a Pickle file and saved in the same folder as the .dot file.

To execute this step, run:

.. code:: bash

    python ./scripts/run_embeddings.py ${$CPG_DATASET} \
        --model transformer
