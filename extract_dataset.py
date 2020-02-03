import argparse

from tools.dataset import CWEClassificationDataset as Dataset
from tools.dataset.processing.dataset_ops import ExtractSampleDataset

if __name__ == "__main__":
    # Setup the argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", metavar="path/to/input", required=True,
                        help="path to the dataset to copy")
    parser.add_argument("--output", "-o", metavar="path/to/output", required=True,
                        help="destination path of the new dataset")
    parser.add_argument("--number", "-n", metavar="sample_number", required=True,
                        type=int, help="number of sample to extract")
    parser.add_argument("--force", "-f", action="store_true",
                        help="force copy if output path exists")

    # Parse input arguments
    args = parser.parse_args()

    # Extract a subset of samples from input dataset.
    input_dataset = Dataset(args.input)
    input_dataset.queue_operation(
        ExtractSampleDataset,
        {"to_path": args.output, "sample_nb": args.number, "force": args.force}
    )

    input_dataset.process()
