Designing processing classes
============================

1. Design overview
------------------

When designing a new processing class, it is important to clearly identify
the abstract class that will provide the base functionalities needed to process
the dataset. A list of available abstract classes is provided below.

The abstract methods from the chosen abstract processing class will provide the
guidelines for designing the processing class. If something cannot be done with
the selected base class, it is probably too specific for the processing to be
implemented. Work up the inheritance chain to find the appropriate abstract
class.

Every processing class should come with its own set of tests. Browse the
``tests/`` folder for implementation examples of tests. There are several types
of tests that can be written:

* Unit tests ensure the code logic is working as expected.
* Regression tests ensure that the various processing steps work correctly when
  used together.

2. Base classes
---------------

Here are the base abstract classes available for designing new processing
classes.

* Raw bases classes:
    * DatasetProcessing
    * DatasetFileProcessing
    * DatasetProcessingWithContainer
* Dataset utilities
    * DatasetFileRemover
* Dataset processing
    * JoernDefaultDatasetProcessing
    * Neo4J3Processing
    * AbstractASTMarkup
* Feature extraction
    * GraphFeatureExtractor
    * FlowGraphFeatureExtractor
* Feature reduction
    * AbstractFeatureSelector
* Models
    * ClassifierModel