Designing pipelines
===================

1. Design overview
------------------

All pipelines are designed with the same philosophy, illustrated by the following
figure.

.. image:: _static/img/pipeline.png
   :align: center

Assuming that the dataset is correctly organized in classes (the download scripts
provided should take care of it), the steps to produce a viable classifier are the
following:

* Process the dataset
    * Clean the dataset from any items that cannot or should not be parsed.
    * Create intermediate representations by parsing the code with external tools
      (Joern) or models (Word2Vec).
    * Enhance the intermediate representations by linking or annotating them.
* Extract the features
    * Select an extraction algorithm that will output the features in a CSV
      file. Assuming that ``n`` features are extracted and the dataset contains
      ``m`` samples, reloading the CSV file using pandas should create a DataFrame
      of shape ``(m,n+2)``.
    * Reduce the number of features by running one or several feature selectors
      on the dataset. This step will fasten the training of the model but might
      hinder further explainability steps.
* Train the model
    * Choose a model type (fully connected, reccurrent, etc.) fit for the extracted
      features and train it with the processed dataset.
* Evaluate the model
    * Run the model against unseen samples to see if the model can generalized what
      has been learned.

2. From prototype to release
----------------------------

To start designing a pipeline, it is strongly advised to use Jupyter notebooks.
Jupyter notebooks allow for fast prototyping by letting the user to inspect the
variables created at each step and run these steps several time in a row. Some
examples are available in the `notebooks <https://gitlab.nist.gov/gitlab/samate/ai-bugfinder/-/tree/master/notebooks>`__
folder.

Once the notebook runs seemlessly, the code can be bundle into a Python script (see
the `scripts <https://gitlab.nist.gov/gitlab/samate/ai-bugfinder/-/tree/master/scripts>`__
folder for more examples). With the help of ``argparse``, the script can be made
versatile. In addition, wrapping the Python script in a bash script can allow to
take care of dependency management that might not be straightforward for all users.

Few pipelines examples are documented `here <https://samate.ipages.nist.gov/ai-bugfinder/examples.html>`__
to help you get started.

3. Available processing
-----------------------

Here are the processing already integrated to the codebase and available when
designing new pipelines. If a processing needs to be fixed or added, please
`create an issue <https://gitlab.nist.gov/gitlab/samate/ai-bugfinder/-/issues>`__.
To create new processing classes, see `Designing processing classes <processing.html>`__.

* Dataset utilities
    * CopyDataset
    * ExtractSampleDataset
    * InverseDataset
    * RightFixer
* Dataset processing
    * RemoveMainFunction
    * ReplaceLitterals
    * RemoveCppFiles
    * RemoveInterproceduralTestCases
    * RemoveComments
    * ReplaceVariables
    * JoernDatasetProcessing
    * ASTMarkup
    * SinkTagging
    * InterproceduralProcessing
* Feature extraction
    * HopsNFlows
    * Word2Vec
    * Node2Vec
    * InterproceduralFeatureExtractor
* Feature reduction
    * AutoEncoder
    * PCA
    * RecursiveFeatureElimination
    * SelectFromModel
    * SequentialFeatureSelector
    * UnivariateSelect
    * VarianceThreshold
* Models
    * LinearClassifier
    * DNNClassifier
    * LSTMClassifier
    * BLSTMClassifier
    * InterprocLSTMClassifier
