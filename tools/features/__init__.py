"""
"""
import csv
import pickle
from abc import abstractmethod
from os import mkdir
from os.path import join, exists, basename, dirname
from shutil import copy

import pandas as pd
from sklearn.decomposition import TruncatedSVD

from tools.dataset.processing import DatasetProcessing
from tools.neo4j import Neo4J3Processing
from tools.settings import LOGGER, ROOT_DIR

IMPLEMENTATION_ERROR = "%s needs to be implemented."


class GraphFeatureExtractor(Neo4J3Processing):
    need_map_features = False
    feature_map_filepath = None

    def _get_entrypoint_list(self):
        list_testcases_cmd = """
            MATCH (f {type:"File"})-[:IS_FILE_OF]->(n {type:"Function"}) 
            WHERE n.code<>"main"
            RETURN id(n) AS id, f.code AS filepath, n.code AS name
        """
        list_entrypoint_cmd = """
            MATCH (f)-[:IS_FUNCTION_OF_CFG]->(entry {type:'CFGEntryNode'})
            WHERE id(f)=%d
            RETURN entry.functionId AS id
        """

        entrypoint_list = list()

        # Get a list of all test cases in the database
        testcase_list = self.neo4j_db.run(list_testcases_cmd).data()

        # For each test case, extract interesting flow graphs
        for testcase in testcase_list:
            testcase_info = {"filepath": testcase["filepath"]}

            # Collect the entry points and merge with test case info.
            entrypoint_list += [
                {**entrypoint_info, **testcase_info}
                for entrypoint_info in self.neo4j_db.run(
                    list_entrypoint_cmd % testcase['id']
                ).data()
            ]

        return entrypoint_list

    def _create_feature_map_file(self, feature_map_filepath):
        if feature_map_filepath is None:
            feature_map_dir = join(ROOT_DIR, "feature_maps")

            if not exists(feature_map_dir):
                mkdir(feature_map_dir)

            self.feature_map_filepath = join(
                feature_map_dir, "%s.bin" % basename(dirname(self.dataset.path))
            )
            LOGGER.debug("No feature file specified. Using %s..." %
                         self.feature_map_filepath)
        else:
            self.feature_map_filepath = feature_map_filepath

    def execute(self, command_args=None, feature_map_filepath=None,
                need_map_features=False):
        self._create_feature_map_file(feature_map_filepath)
        self.need_map_features = need_map_features

        super().execute(command_args=command_args)

    def send_commands(self):
        super().send_commands()

        if not self.need_map_features:
            LOGGER.debug("Extracting features...")
            self.check_extraction_inputs()
            features = self.extract_features()
            self.write_extraction_outputs(features)
        else:
            LOGGER.debug("Mapping features...")
            labels = self.map_features()
            self.save_labels_to_features_map(labels)

    def check_extraction_inputs(self):
        # Check if features directory exists. Create it if it does not.
        if not exists(self.dataset.feats_dir):
            mkdir(self.dataset.feats_dir)
            # TODO return new version

        # Save the feature file if it exists

        # Update the feature version number
        return join(self.dataset.feats_dir, "features.csv")

    def write_extraction_outputs(self, features):
        # output_file = self.dataset.get_next_feature_filepath()
        output_file = join(self.dataset.feats_dir, "features.csv")

        with open(output_file, "w") as csv_file:
            csv_writer = csv.writer(csv_file)

            # FIXME developer will not know how to setup its features
            labels = self.get_labels_from_features_map() + ["result", "name"]

            # Make sure the number of labels and the number of features are the
            # same.
            if len(labels) != len(features[0]):
                raise IndexError(
                    "Number of labels (%d) differs from number of features (%d)"
                    % (len(labels), len(features[0]))
                )

            # Write headers and content to CSV file
            csv_writer.writerow(labels)
            csv_writer.writerows(features)

    def save_labels_to_features_map(self, labels):
        existing_labels = self.get_labels_from_features_map()
        orig_labels_count = len(existing_labels)

        LOGGER.debug("Retrieved %d existintg labels. Adding new labels..." %
                     orig_labels_count)

        existing_labels += labels
        existing_labels = set(existing_labels)

        LOGGER.debug("New label count is %d." % len(existing_labels))

        if len(existing_labels) == orig_labels_count:
            return

        LOGGER.debug("Writing label set to disk...")
        with open(join(ROOT_DIR, self.feature_map_filepath), "wb") \
                as feature_map_file:
            pickle.dump(existing_labels, feature_map_file)

    def get_labels_from_features_map(self):
        feature_map_filepath = join(ROOT_DIR, self.feature_map_filepath)

        if not exists(feature_map_filepath):
            return []

        with open(feature_map_filepath, "rb") \
                as feature_map_file:
            labels = pickle.load(feature_map_file)

        return list(labels)

    @abstractmethod
    def extract_features(self):
        raise NotImplementedError(IMPLEMENTATION_ERROR % "extract_features")

    @abstractmethod
    def map_features(self):
        raise NotImplementedError(IMPLEMENTATION_ERROR % "map_features")


class FlowGraphFeatureExtractor(GraphFeatureExtractor):
    @abstractmethod
    def get_flowgraph_list_for_entrypoint(self, entrypoint):
        raise NotImplementedError(
            IMPLEMENTATION_ERROR % "get_flowgraph_list_for_entrypoint"
        )

    @abstractmethod
    def get_label_from_flowgraph(self, flowgraph):
        raise NotImplementedError(
            IMPLEMENTATION_ERROR % "get_label_from_flowgraph"
        )

    @staticmethod
    def initialize_features(entrypoint, label_list):
        return [0.] * len(label_list) + [
            entrypoint['filepath'].split('/')[2] == 'good',
            entrypoint['filepath'].split('/')[-1]
        ]

    @abstractmethod
    def get_flowgraph_count(self, flowgraph):
        raise NotImplementedError(
            IMPLEMENTATION_ERROR % "get_flowgraph_count"
        )

    @staticmethod
    def finalize_features(features, labels):
        return features

    def extract_features(self):
        labels = self.get_labels_from_features_map()
        entrypoint_list = self._get_entrypoint_list()
        entrypoint_index = 0
        last_progress = 0

        LOGGER.info("Retrieved %d entrypoints and %d labels. Querying for "
                    "flowgraphs..." % (len(entrypoint_list), len(labels)))

        features = list()

        for entrypoint in entrypoint_list:
            progress = int(100 * (entrypoint_index + 1) / len(entrypoint_list))

            if progress > 0 and progress % 10 == 0:
                if progress > last_progress:
                    LOGGER.info("Processed %d%% of the dataset." % progress)
                    last_progress = progress

            features_row_entrypoint = self.initialize_features(
                entrypoint, labels
            )

            # Record and count each unique flow graph
            for flowgraph in self.get_flowgraph_list_for_entrypoint(entrypoint):
                label = self.get_label_from_flowgraph(flowgraph)

                if label not in labels:
                    LOGGER.debug("Feature %s not found and ignored" % label)
                    continue

                # Increment the count for the current graph in the current test
                # case's vector
                features_row_entrypoint[
                    labels.index(label)
                ] += self.get_flowgraph_count(flowgraph)

            # Add the entrypoint features to the feature list
            features.append(features_row_entrypoint)

            # Keep track of the progress
            entrypoint_index += 1

        LOGGER.info("Extracted %dx%d features matrix. Finalizing features..." %
                    (len(features), len(features[0])))

        return self.finalize_features(features, labels)

    def map_features(self):
        # List of feature labels to return
        labels = []
        entrypoint_list = self._get_entrypoint_list()
        entrypoint_index = 0
        last_progress = 0

        LOGGER.info("Retrieved %d entrypoints. Querying for flowgraphs..." %
                    len(entrypoint_list))

        # Get the interesting flow graphs for each function
        for entrypoint in entrypoint_list:
            progress = int(100 * (entrypoint_index + 1) / len(entrypoint_list))

            if progress > 0 and progress % 10 == 0:
                if progress > last_progress:
                    LOGGER.info(
                        "Processed %d%% of the dataset." % progress
                    )
                    last_progress = progress

            # Record and count each unique flow graph
            for flowgraph in self.get_flowgraph_list_for_entrypoint(entrypoint):
                labels.append(self.get_label_from_flowgraph(flowgraph))

            entrypoint_index += 1

        labels = set(labels)

        LOGGER.info("Extracted %d labels." % len(labels))

        return list(labels)



