"""
"""
import logging
from os.path import realpath

from py2neo import Graph

from tools.dataset import CWEClassificationDataset as Dataset
from tools.dataset.processing.content_ops import *
from tools.dataset.processing.dataset_ops import *
from tools.dataset.processing.file_ops import *
from tools.features.rel_count_single_hop_v02 import extract_features
from tools.libs.ast.v02 import main as ast_v02
from tools.libs.joern.v040 import main as run_joern_v040
from tools.libs.neo4j.ai import start_container as run_neo4j_v3
from tools.utils.containers import stop_container_by_name

LOGGER.setLevel(logging.INFO)

if __name__ == "__main__":
    extracted_dataset_path = "./data/cwe121_annot"
    cleaned_dataset_path = "./data/cwe121_dataset"
    cwe121_1000_ref_dataset_path = "./data/cwe121_1000"
    cwe121_1000_dataset_path = "./data/cwe121_1000a"

    # Create a copy of the annotated dataset to avoid overwriting
    extracted_dataset = Dataset(extracted_dataset_path)
    extracted_dataset.queue_operation(
        CopyDataset, {"to_path": cleaned_dataset_path, "force": True}
    )
    extracted_dataset.process()

    # Cleanup new dataset
    cleaned_dataset = Dataset(cleaned_dataset_path)

    cleaned_dataset.queue_operation(RemoveCppFiles)
    cleaned_dataset.queue_operation(RemoveMainFunction)
    cleaned_dataset.queue_operation(ReplaceLitterals)

    cleaned_dataset.process()

    # Extract a subset of 1000 samples for training, test and validation
    # purposes.
    cleaned_dataset.queue_operation(
        ExtractSampleDataset,
        {
            "to_path": cwe121_1000_ref_dataset_path,
            "sample_nb": 1000,
            "force": True
        }
    )
    cleaned_dataset.process()

    # Copy the dataset for future references.
    cwe121_1000_ref_dataset = Dataset(cwe121_1000_ref_dataset_path)
    cwe121_1000_ref_dataset.queue_operation(
        CopyDataset, {"to_path": cwe121_1000_dataset_path, "force": True}
    )

    cwe121_1000_ref_dataset.process()

    # Build the dataset that is going to be used
    cwe121_1000_dataset = Dataset(cwe121_1000_dataset_path)
    run_joern_v040(realpath(cwe121_1000_dataset.path))
    ast_v02(realpath("%s/neo4j_v3.db" % cwe121_1000_dataset.path))

    db_path = realpath("%s/neo4j_v3.db" % cwe121_1000_dataset.path)

    neo4j_container_obj, neo4j_container_name = run_neo4j_v3(
        db_path, stop_after_execution=False
    )

    # Neo4j database pre-loaded with Joern
    neo4j_db = Graph(
        scheme="http",
        host="0.0.0.0",
        port="7474"
    )

    extract_features(neo4j_db, cwe121_1000_dataset.path)

    stop_container_by_name(neo4j_container_name)
