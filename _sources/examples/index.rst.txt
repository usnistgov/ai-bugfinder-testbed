Example pipelines
=================

In this document, are presented the various ways to interact with the dataset
of code samples. Several scripts are available in the repository to manipulate
datasets and train a machine learning model to identify bugs in source code.
The scripts are written in python and, for every script, an help page is
available by typing ``python ./script.py --help``.

1. Dataset utilities
--------------------

Utilities scripts operates on the dataset folder and do not modify the
data that it contains. The two utilities available are:

- ``copy_dataset.py`` to duplicate an existing dataset to another
  location.
- ``extract_dataset.py`` to extract a defined number of
  samples from a dataset.

Examples:

.. code:: bash

   python ./copy_dataset.py \
       -i /path/to/existing_dataset \  # Input argument
       -o /path/to/new_dataset \  # Output argument
       -f  # Override directory if it already exists

   python ./extract_dataset.py \
       -i /path/to/existing_dataset \  # Input argument
       -o /path/to/new_dataset \  # Output argument
       -n 200  # Extract 200 samples from original dataset
       -f  # Override directory if it already exists

2. Prepare the dataset
----------------------

There are several issues with the default datasets:

- C++ cannot be parsed correctly by *Joern*, these samples need to be
  remove from the dataset.
- *Joern* is not able to perfectly parse the C samples from *Juliet*.
  Instances of the code left unparsed need to be replaced by an
  equivalent code line that *Joern* can parse.
- In *Juliet*, ``main(...)`` functions are used to compile the correct
  (good or bad) code depending on pre-processor variables. These
  functions are not useful and possibly misleading for the classifier,
  they need to be removed.
- The current version of the tool does not work with interprocedural
  test cases which need to be removed from the dataset.

To handle all of these issues, the ``clean_dataset.py`` script is
available and works as such:

.. code:: bash

   export DATASET=/path/to/dataset

   python ./clean_dataset.py ${DATASET} \
       --no-cpp \  # Remove CPP test cases
       --no-interprocedural \  # Remove interprocedural test cases
       --no-litterals \  # Replace litterals from C code
       --no-main  # Remove main functions

N.B.: If interprocedural features are computed, make sure to leave interprocedural
test cases (do not use `--no-interprocedural`) and do not remove main functions
(do not use `--no-main`).


3. Pipelines
------------

.. toctree::
    :maxdepth: 1

    bags_of_words
    word2vec
    node2vec
    interprocedural
