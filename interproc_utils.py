"""
Temporary utility functions for the interproc LSTM model
"""
import json
import numpy as np
from bugfinder.settings import LOGGER


def process_features(features_file, feature_map_file, test_data_ratio=0.33):

    assert 0.0 <= test_data_ratio <= 1.0

    LOGGER.info("Loading feature map...")
    with open(feature_map_file, "rt") as fmap_file:
        fmap = json.load(fmap_file)

    LOGGER.info("Loading features...")
    with open(features_file, "rt") as feat_file:
        feat = json.load(feat_file)

    # Map node types (ASTv3) to one-hot tensors
    nmap = dict(zip(fmap.keys(), np.eye(len(fmap))))
    # TODO Save mapping for later use

    # Calculate the max number of inflows, outflows and path length
    max_inflow = max([max(v) for v in fmap.values()])
    max_outflow = max([len(s["outflow"]) for f in feat.values() for s in f])
    max_pathlen = max([len(path) for path in feat.values()])
    LOGGER.info(f"Longest seq.: {max_pathlen}")

    # x: ast, inflow, outflow, end_of_path for each step
    x_len = max_pathlen * (len(fmap) + max_inflow * (1 + len(fmap)) + max_outflow)
    LOGGER.info(f"Feature size: {x_len}")
    # y: sink for each step
    y_len = max_pathlen * 1
    x = np.zeros((len(feat), x_len))
    y = np.zeros((len(feat), y_len))
    xy_idx = 0
    for path_id, path in feat.items():
        _x = x[xy_idx]
        _y = y[xy_idx]
        xy_idx += 1
        _x_idx, _y_idx = 0, 0
        for step in path:
            # Append a flag describing if the current node/step is a sink
            _y[_y_idx] = 1.0 if step["sink"] else 0.0
            _y_idx += 1
            # Convert node's AST to one-hot tensor
            x_len = len(fmap)
            _x[_x_idx : _x_idx + x_len] = nmap[step["ast"]]
            _x_idx += x_len
            # Calculate the largest data size to enable scaling
            max_size = float(
                max(
                    max(step["outflow"]) if step["outflow"] else 0.0,
                    max([ifl["size"] for ifl in step["inflow"]])
                    if step["inflow"]
                    else 0.0,
                )
            )
            for inflow in step["inflow"]:
                # Inflow tensor: [size, multiplexed one-hot tensor of inflow node's AST]
                # Size is scaled between 0. and 1.
                _x[_x_idx] = float(inflow["size"]) / max_size if max_size > 0.0 else 0.0
                _x_idx += 1
                # Append the current inflow tensor to the full input tensor
                for ast in inflow["nodes"]:
                    # Multiplex one-hot vector of all inflow nodes' AST
                    x_len = len(fmap)
                    _x[_x_idx : _x_idx + x_len] += nmap[ast]
                    _x_idx += x_len
            for outflow_size in step["outflow"]:
                # Outflow tensor: [size]
                _x[_x_idx] = float(outflow_size) / max_size if max_size > 0.0 else 0.0
                _x_idx += 1
            # Append a flag describing whether this step is the last in the path
            _x[_x_idx] = 0.0
        # Flip the flag to indicate this was the last step in the path
        _x[-1] = 1.0

    # Split the dataset
    rvals = np.random.rand(len(feat))
    split = rvals < np.percentile(rvals, int(100.0 * (1.0 - test_data_ratio)))
    x_train, x_test = x[split], x[~split]
    y_train, y_test = y[split], y[~split]

    return x_train, x_test, y_train, y_test


if __name__ == "__main__":
    # FIXME These are just unit tests
    features_file = "/home/delaitre2/Documents/ai-bugfinder/data/cwe121_small/features/interproc-features.json"
    feature_map_file = "/home/delaitre2/Documents/ai-bugfinder/data/cwe121_small/features/interproc-feature-map.json"
    xtr, xte, ytr, yte = process_features(
        features_file, feature_map_file, test_data_ratio=0.33
    )
    print(xtr.shape, xte.shape, ytr.shape, yte.shape)
