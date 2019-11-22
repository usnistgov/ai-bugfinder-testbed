import csv
import os
import pickle
from os.path import join

from hashlib import sha256

from tools.neo4j import Neo4J3Processing
from tools.settings import LOGGER


class ExtractorRelCountSingleAlpha(Neo4J3Processing):
    FLOWS = {
        "CONTROLS": 0,
        "FLOWS_TO": 1,
        "REACHES": 2,
    }

    COMMANDS = {
        "list_testcases": """
            MATCH (f {type:"File"})-[:IS_FILE_OF]->(n {type:"Function"}) 
            WHERE n.code<>"main"
            RETURN id(n) AS id, f.code AS filepath, n.code AS name
        """,
        "list_entrypoint": """
            MATCH (f)-[:IS_FUNCTION_OF_CFG]->(entry {type:'CFGEntryNode'})
            WHERE id(f)=%d
            RETURN entry.functionId AS id
        """,
        "get_flowgraphs": """
            MATCH p = (root1:UpstreamNode)-[rel:FLOWS_TO|:REACHES|:CONTROLS]->(root2:DownstreamNode)
            WHERE root1.functionId="%s"
            RETURN distinct root1.ast AS source, root2.ast AS sink, type(rel) AS flow, count(p) AS count
        """
    }

    def configure_container(self):
        super().configure_container()
        self.container_name = "fe-rel-count-single-v01"

    def send_commands(self):
        super().send_commands()

        # Get feature info calculated earlier
        with open("./features.bin", "rb") as features_file:
            features_refs = pickle.load(features_file)

        # Test case index
        testcase_index = 0

        LOGGER.info("Retrieving test cases from the database...")

        # Get a list of all test cases in the database
        testcase_list = self.neo4j_db.run(self.COMMANDS["list_testcases"]).data()
        LOGGER.info("%d test cases to process..." % len(testcase_list))

        #
        features = list()

        #
        last_progress = 0
        total_flow_count = 0

        # For each test case, extract interesting flow graphs
        for testcase in testcase_list:
            progress = int(100 * (testcase_index + 1) / len(testcase_list))

            if progress > 0 and progress % 10 == 0:
                if progress > last_progress:
                    LOGGER.info(
                        "Processed %d%% of the dataset." % progress
                    )
                    last_progress = progress

            # Keep track of whether the current test case is good or bad, along with
            # the test case name
            # labels.append([
            #     testcase['filepath'].split('/')[2] == 'good',
            #     testcase['filepath'].split('/')[-1]
            # ])
            test_case_feature = [
                testcase['filepath'].split('/')[2] == 'good',
                testcase['filepath'].split('/')[-1]
            ] + [0 for _ in range(len(features_refs))]

            # To speed things up, collect the entry points
            entrypoint_list = self.neo4j_db.run(
                self.COMMANDS["list_entrypoint"] % testcase['id']
            ).data()

            # Get the interesting flow graphs for each function
            for entrypoint in entrypoint_list:
                flowgraph_list = self.neo4j_db.run(
                    self.COMMANDS["get_flowgraphs"] % entrypoint['id']
                ).data()

                # Record and count each unique flow graph
                for flowgraph in flowgraph_list:
                    source = flowgraph["source"]
                    sink = flowgraph["sink"]
                    flow = flowgraph["flow"]

                    feature_ref = "%s-%s-%s" % (source, flow, sink)

                    # Add the current graph to the books if it's new
                    if feature_ref not in features_refs:
                        # raise KeyError("Feature %s never seen before" % feature_ref)
                        LOGGER.warning("Feature %s not found and ignored" % feature_ref)
                        continue

                    # Increment the count for the current graph in the current test
                    # case's vector
                    test_case_feature[
                        features_refs.index(feature_ref) + 2
                    ] += flowgraph["count"]
                    total_flow_count += flowgraph["count"]

            features.append(test_case_feature)

            # Increment the test case index
            testcase_index += 1

        LOGGER.info(
            "Analyzed %d test cases. Retrieved %d flowgrpha counts. "
            "Writing to disk..." % (testcase_index, total_flow_count)
        )

        # Create feature directory if needed
        if not os.path.exists(self.dataset.feats_dir):
            os.mkdir(self.dataset.feats_dir)

        # Write feature to CSV for easy reload
        with open(join(self.dataset.feats_dir, "features.csv"), "w") as csv_file:
            csv_writer = csv.writer(csv_file)

            csv_writer.writerow(["result", "name"] + [
                "f.%s" % sha256(feat.encode("utf-8")).hexdigest()
                for feat in features_refs
            ])
            csv_writer.writerows(features)

        LOGGER.info("Feature file created.")


class ExtractorRelCountSingleBeta(Neo4J3Processing):
    FLOWS = {
        "CONTROLS": 0,
        "FLOWS_TO": 1,
        "REACHES": 2,
    }

    COMMANDS = {
        "list_testcases": """
            MATCH (f {type:"File"})-[:IS_FILE_OF]->(n {type:"Function"}) 
            WHERE n.code<>"main"
            RETURN id(n) AS id, f.code AS filepath, n.code AS name
        """,
        "list_entrypoint": """
            MATCH (f)-[:IS_FUNCTION_OF_CFG]->(entry {type:'CFGEntryNode'})
            WHERE id(f)=%d
            RETURN entry.functionId AS id
        """,
        "get_flowgraphs": """
            MATCH p = (root1:UpstreamNode)-[:%s*]->(root2:DownstreamNode)
            WHERE root1.functionId="%s"
            RETURN distinct root1.ast AS source, root2.ast AS sink, count(p) as count
        """
    }

    def configure_container(self):
        super().configure_container()
        self.container_name = "fe-rel-count-single-v02"

    def send_commands(self):
        super().send_commands()

        # Get feature info calculated earlier
        with open("./features.bin", "rb") as features_file:
            features_refs = pickle.load(features_file)

        # Test case index
        testcase_index = 0

        LOGGER.info("Retrieving test cases from the database...")

        # Get a list of all test cases in the database
        testcase_list = self.neo4j_db.run(self.COMMANDS["list_testcases"]).data()
        LOGGER.info(
            "%d test cases to process (%d features)..." %
            (len(testcase_list), len(features_refs))
        )

        # A sparse matrix to store the number of occurrences of each flow graph for
        # each test case
        # features = lil_matrix((len(testcase_list), len(features_refs)), dtype=float)
        # features = DataFrame()
        features = list()

        # A list keeping track of whether a test case is good or bad
        # labels = []
        last_progress = 0

        # For each test case, extract interesting flow graphs
        for testcase in testcase_list:
            progress = int(100 * (testcase_index + 1) / len(testcase_list))

            if progress > 0 and progress % 10 == 0:
                if progress > last_progress:
                    LOGGER.info(
                        "Processed %d%% of the dataset." % progress
                    )
                    last_progress = progress

            # Keep track of whether the current test case is good or bad, along with
            # the test case name
            # labels.append([
            #     testcase['filepath'].split('/')[2] == 'good',
            #     testcase['filepath'].split('/')[-1]
            # ])
            test_case_features = [
                testcase['filepath'].split('/')[2] == 'good',
                testcase['filepath'].split('/')[-1]
            ] + [0 for _ in range(len(features_refs))]

            # To speed things up, collect the entry points
            entrypoint_list = self.neo4j_db.run(
                self.COMMANDS["list_entrypoint"] % testcase['id']
            ).data()

            # Get the interesting flow graphs for each function
            for entrypoint in entrypoint_list:
                for flow in list(self.FLOWS.keys()):
                    # features_info = dict()
                    total_flow = 0

                    flowgraph_list = self.neo4j_db.run(
                        self.COMMANDS["get_flowgraphs"] % (flow, entrypoint['id'])
                    ).data()

                    # Record and count each unique flow graph
                    for flowgraph in flowgraph_list:
                        source = flowgraph["source"]
                        sink = flowgraph["sink"]

                        feature_ref = "%s-%s-%s" % (source, flow, sink)

                        # Add the current graph to the books if it's new
                        if feature_ref not in features_refs:
                            # raise KeyError("Feature %s never seen before" % feature_ref)
                            LOGGER.warning("Feature %s not found and ignored" % feature_ref)
                            continue

                        # Increment the count for the current graph in the current test
                        # case's vector
                        # if features_refs not in list(features_info.keys()):
                        #     features_info[feature_ref] = 0

                        # features_info[feature_ref] += flowgraph["count"]
                        test_case_features[
                            features_refs.index(feature_ref) + 2
                        ] += flowgraph["count"]
                        total_flow += flowgraph["count"]

                    # for feature_ref, feature_count in list(features_info.items()):
                    #     features[testcase_index, features_refs.index(feature_ref)] = \
                    #         float(feature_count) / float(total_flow)
                    if total_flow != 0:
                        for feat_index in range(len(features_refs)):
                            test_case_features[feat_index + 2] /= total_flow

            features.append(test_case_features)

            # Increment the test case index
            testcase_index += 1

        LOGGER.info("Analyzed %d test cases" % testcase_index)

        # Create feature directory
        # features_dir = join(data_dir, "features")

        if not os.path.exists(self.dataset.feats_dir):
            os.mkdir(self.dataset.feats_dir)

        # Write data to disk in sparse format (Matrix Market)
        # mmwrite(join(features_dir, "features.mtx"), features, field="integer")
        # mmwrite(join(self.dataset.feats_dir, "features.mtx"), features)
        #
        # numpy.savetxt(
        #     join(self.dataset.feats_dir, "labels.txt"), labels, delimiter=",", fmt="%s"
        # )

        with open(join(self.dataset.feats_dir, "features.csv"), "w") as csv_file:
            csv_writer = csv.writer(csv_file)

            csv_writer.writerow(["result", "name"] + [
                "f.%s" % sha256(feat.encode("utf-8")).hexdigest()
                for feat in features_refs
            ])
            csv_writer.writerows(features)

        LOGGER.info("Feature file created.")
