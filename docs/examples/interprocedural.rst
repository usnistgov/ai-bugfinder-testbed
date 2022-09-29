4. Interprocedural
------------------

4.1. Identify sinks
~~~~~~~~~~~~~~~~~~~

To extract interprocedural features, it is necessary to first identify all sinks in a
given dataset. SARD test cases have a SARIF manifest bundled with the code that allows
to perform sink identification. Run the following command to do so.

.. code:: bash

    export SARIF_DIR=/path/to/sarif_manifests

    find ${SARIF_DIR} -maxdepth 1 -type d -printf '%f\n' | grep '^[0-9]\+$' \
        | nice parallel --lb -I {} \
            "jq -r '.runs[0] | (.properties.id|tostring) + \",\" \
                + (.results[0].locations[0].physicalLocation | .artifactLocation.uri \
                + \",\" + (.region.startLine|tostring))' ${SARIF_DIR}/{}/manifest.sarif" \
        | grep -v ,,null > ${DATASET}/sinks.csv


N.B.: Manifests are still being created and not available to the general public

4.2. Run Joern
~~~~~~~~~~~~~~

`Joern <https://joern.io/>`__ then needs to be executed with the script
``run_joern.py``. Once the execution is done, the *.joernIndex* is moved to
*data/graph.db*. A Neo4j DB then loads the data for further processing.

Run the tool with
``python ./scripts/run_joern.py ${DATASET} -v ${JOERN_VERSION}``. Use
``--help`` to see which version are available.

4.3. Sink tagging
~~~~~~~~~~~~~~~~~

To link data and control flow to compute interprocedural features, it is necessary to
tag the sinks, using the CSV obtain earlier. Sink tagging can be done using:

.. code:: bash

    # Tag sinks with a maximum runtime of 15min
    python ./scripts/run_sinktagging.py --log_failed /tmp/sink.failed.15m.log \
        --timeout 15m --sinks ${DATASET}/sinks.csv ${DATASET}

    # Retry tagging sinks for a longer period, using previous log files
    python ./scripts/run_sinktagging.py --run_failed /tmp/sink.failed.15m.log \
        --log_failed /tmp/sink.failed.24h.log \
        --timeout 24h --sinks ${DATASET}/sinks.csv ${DATASET}

4.4. Link data and control flows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To link data and control flow, the following commands need to be run:

.. code:: bash

    # Connect data and control flows at function calls
    python ./scripts/run_interproc.py --log_failed /tmp/failed.15m.log \
        --timeout 15m ${DATASET}

    # Retry linking flows for a longer period, using previous log files
    python ./scripts/run_interproc.py --run_failed /tmp/failed.15m.log \
        --timeout 24h --log_failed /tmp/failed.24h.log ${DATASET}

4.5. AST Markup
~~~~~~~~~~~~~~~

The next step is to add labels to the nodes and build the AST notation
for feature extraction. Run the following command to enhance the dataset
with the additional markup:

.. code:: bash

   python ./scripts/run_ast_markup.py ${DATASET} \
       -v ${AST_VERSION}  # AST markup version. See --help for details.

4.6. Extract feature
~~~~~~~~~~~~~~~~~~~~

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

4.7. Reduce feature dimension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To fasten training of the model, feature reduction can be applied with the following
command:

.. code:: bash

   # Create the feature maps
   python ./scripts/run_feature_selection.py ${DATASET} \
       -s ${FEATURE_SELECTOR} \  # Choose a feature selector.
       ${FEATURES_SELECTOR_ARGS} \  # Parametrize the selector correctly
       -m  # To create the feature maps.

N.B.: Several feature reducer can be applied successively if necessary. Use `--dry-run`
to preview the final training set dimension.

4.8. Run model training
~~~~~~~~~~~~~~~~~~~~~~~

The last step is to train the model. Execute the TensorFlow script by
typing:

.. code:: bash

   python ./scripts/run_model_training.py ${DATASET} \
       -m ${MODEL}  # Model to train. See help for details.



