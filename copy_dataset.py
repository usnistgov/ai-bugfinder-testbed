import argparse

from bugfinder.dataset import CWEClassificationDataset as Dataset
from bugfinder.dataset.processing.dataset_ops import CopyDataset

if __name__ == "__main__":
    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", metavar="path/to/input", required=True,
                        help="path to the dataset to copy")
    parser.add_argument("--output", "-o", metavar="path/to/output", required=True,
                        help="destination path of the new dataset")
    parser.add_argument("--force", "-f", action="store_true",
                        help="force copy if output path exists")

    # Parse input arguments
    args = parser.parse_args()

    # Create a copy of the annotated dataset to avoid overwriting
    input_dataset = Dataset(args.input)
    input_dataset.queue_operation(
        CopyDataset, {"to_path": args.output, "force": args.force}
    )
    input_dataset.process()
