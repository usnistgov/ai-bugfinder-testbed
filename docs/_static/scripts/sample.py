""" Example script for dataset processing.
"""
from bugfinder.base.dataset import CodeWeaknessClassificationDataset as Dataset
from bugfinder.processing.cleaning.replace_litterals import (
    ReplaceLitterals,
)
from bugfinder.features.reduction.pca import FeatureSelector as PCA
from bugfinder.processing.dataset.fix_rights import RightFixer
from bugfinder.processing.dataset.extract import ExtractSampleDataset
from bugfinder.processing.cleaning.remove_cpp_files import (
    RemoveCppFiles,
)
from bugfinder.models.linear_classifier import LinearClassifierTraining
from bugfinder.features.extraction.bag_of_words.hops_n_flows import (
    FeatureExtractor as HopsNFlowsExtractor,
)
from bugfinder.processing.ast.v02 import Neo4JASTMarkup as Neo4JASTMarkupV02
from bugfinder.processing.neo4j.importer import Neo4J3Importer
from bugfinder.processing.neo4j.annot import Neo4JAnnotations
from bugfinder.processing.joern.v040 import JoernProcessing as Joern040DatasetProcessing

input_dataset_path = "/path/to/dataset.in"
output_dataset_path = "/path/to/dataset.out"

# Extract 50 samples from the dataset.
input_dataset = Dataset(input_dataset_path)
input_dataset.queue_operation(
    ExtractSampleDataset,
    {"to_path": output_dataset_path, "sample_nb": 50, "force": True},
)
input_dataset.process()

right_fixer_op = {
    "op_class": RightFixer,
    "op_args": {"command_args": "neo4j_v3.db 101 101"},
}

# Cleanup the dataset by removing C++ files and replacing litterals.
output_dataset = Dataset(output_dataset_path)
output_dataset.queue_operation(RemoveCppFiles)
output_dataset.queue_operation(ReplaceLitterals)
# Run version 0.4.0 of the Joern processor.
output_dataset.queue_operation(Joern040DatasetProcessing)
output_dataset.queue_operation(Neo4J3Importer)
output_dataset.queue_operation(**right_fixer_op)
output_dataset.queue_operation(Neo4JAnnotations)
# Use AST markup v2 to annotate the graph.
output_dataset.queue_operation(**right_fixer_op)
output_dataset.queue_operation(Neo4JASTMarkupV02)
# Run feature extraction.
output_dataset.queue_operation(HopsNFlowsExtractor, {"need_map_features": True})
output_dataset.queue_operation(HopsNFlowsExtractor)
# Run feature selection to fasten training.
output_dataset.queue_operation(PCA, {"dimension": 50, "dry_run": False})
# Run model training and display metrics.
output_dataset.queue_operation(
    LinearClassifierTraining,
    {
        "name": "lin-cls",
        "batch_size": 100,
        "max_items": None,
        "epochs": 1,
        "keep_best_model": False,
        "reset": False,
    },
)

output_dataset.process()
