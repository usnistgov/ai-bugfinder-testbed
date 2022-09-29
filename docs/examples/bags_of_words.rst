1. Bag of words
---------------

The bag of words pipeline was the initial pipeline designed in the AI bugfinder,
it has been improved over time and is the use case for the design of this
software.

1.1. Run Joern
~~~~~~~~~~~~~~

`Joern <https://joern.io/>`__ then needs to be executed with the script
``run_joern.py``. Once the execution is done, the *.joernIndex* is moved to
*data/graph.db*. A Neo4j DB then loads the data for further processing.

Run the tool with
``python ./scripts/run_joern.py ${DATASET} -v ${JOERN_VERSION}``. Use
``--help`` to see which version are available.

1.2. AST Markup
~~~~~~~~~~~~~~~

The next step is to add labels to the nodes and build the AST notation
for feature extraction. Run the following command to enhance the dataset
with the additional markup:

.. code:: bash

   python ./scripts/run_ast_markup.py ${DATASET} \
       -v ${AST_VERSION}  # AST markup version. See --help for details.

1.3. Extract features
~~~~~~~~~~~~~~~~~~~~~

Several feature extractors have been created for this classification
task. The features need to be extracted with the following command:

.. code:: bash

   # Create the feature maps
   python ./scripts/run_feature_extraction.py ${DATASET} \
       -e ${FEATURE_EXTRACTOR} \  # Choose a feature extractor.
       -m  # To create the feature maps.

   # Run the extractor
   python ./scripts/run_feature_extraction.py ${DATASET} \
       -e ${FEATURE_EXTRACTOR} \  # Choose a feature extractor

1.4. Reduce feature dimension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To fasten training of the model, feature reduction can be applied with the following
command:

.. code:: bash

   # Create the feature maps
   python ./scripts/run_feature_selection.py ${DATASET} \
       -s ${FEATURE_SELECTOR} \  # Choose a feature selector.
       ${FEATURES_SELECTOR_ARGS} # Parametrize the selector correctly

N.B.: Several feature reducer can be applied successively if necessary. Use
`--dry-run` to preview the final training set dimension.

1.5. Run model training
~~~~~~~~~~~~~~~~~~~~~~~

The last step is to train the model. Execute the TensorFlow script by typing:

.. code:: bash

   python ./scripts/run_model_training.py ${DATASET} \
       -m ${MODEL}  # Model to train. See help for details.
