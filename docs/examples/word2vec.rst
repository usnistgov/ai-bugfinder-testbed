2. Word2Vec
-----------

2.1. Additional dataset cleaning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to train a word2vec model in this dataset, there is no need to run
Joern. After you finished preparing the dataset with the ``clean_dataset.py``
script, it is necessary to run an additional script to deal with:

- Removal of code comments
- Replacement of variables names by similar tokens
- Replacement of function names by similar tokens

To handle this additional cleanup, you need to use the ``clean_dataset.py`` script:

.. code:: bash

   python ./scripts/clean_dataset.py ${DATASET} \
       --no-comments  # Remove comments

2.2. Tokenizing the dataset
~~~~~~~~~~~~~~~~~~~~~~~~~~~

After finishing the cleanup, it is necessary to separate the code in tokens to be used
as input for the word2vec model. That can be done by an additional parameter in the
``run_tokenizer.py``, so after finishing the previous command, run:

.. code:: bash

   python ./scripts/run_tokenizer.py ${DATASET} \
       --replace-funcs \  # Replace functions by a FUN token
       --replace-vars  # Replace variables by a VAR token
       --tokenize

2.3. Training the word2vec model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After the tokenization process, you can train the word2vec model, using the
``run_model_training.py`` script with word2vec as the parameter. Run the command:

.. code:: bash

   python ./scripts/run_model_training.py ${DATASET} \
       -m word2vec \  # word2vec model
       -n {MODEL_NAME} \  # path where the model will be saved

2.4. Generate the embeddings for the BLSTM model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After the model training is complete, it's necessary to generate
embeddings which will be used as input for the BLSTM model. These
embeddings are saved in a folder with the dataset, in .CSV format.
Execute the following script:

.. code:: bash

   python ./scripts/run_embeddings.py ${DATASET} \
       -m word2vec \  # Type of the model
       -n {MODEL_DIR}  # Previous trained word2vec model

2.5. Train the BLSTM model with the word2vec embeddings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After generating the embeddings, the BLSTM model is ready to use.
Execute the following script:

.. code:: bash

   python ./scripts/run_model_training.py ${DATASET} \
       -m bidirectional_lstm \  # BLSTM
       -n {MODEL_NAME} \ # path where the model will be saved
       -e {EPOCHS} \ # number of epochs
       -b {BATCH_SIZE} # Size of the batch used for training
