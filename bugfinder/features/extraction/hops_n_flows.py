""" Feature extractor module for HopNFlows algorithm
"""
from sys import exit
from copy import deepcopy

from bugfinder.features.extraction import FlowGraphFeatureExtractor
from bugfinder.settings import LOGGER


class FeatureExtractor(FlowGraphFeatureExtractor):
    """HopNFlows feature extractor"""

    flows = ["CONTROLS", "FLOWS_TO", "REACHES"]
    min_hops = 1
    max_hops = -1

    def configure_container(self):
        """Setting up the container variables"""
        super().configure_container()
        self.container_name = "fext-hops-n-flows"

    def execute(
        self,
        command_args=None,
        flows=None,
        min_hops=1,
        max_hops=-1,
        feature_map_filepath=None,
        need_map_features=False,
    ):
        """Run the feature extraction algorithm"""
        if not flows:
            LOGGER.debug(
                "No flows selected, using 'CONTROLS', 'FLOWS_TO' and 'REACHES' by "
                "default."
            )
        else:
            self.flows = flows

        if min_hops < 1:
            LOGGER.error("Should select a min_hops value greater than 1.")
            exit(1)

        if max_hops != -1 and max_hops < min_hops:
            LOGGER.error("Should select a max_hops value greater than min_hops.")
            exit(1)

        LOGGER.debug(
            "flows: %s, min_hops: %d, max_hops: %d", str(flows), min_hops, max_hops
        )
        super().execute(command_args, feature_map_filepath, need_map_features)

    def get_flowgraph_list_for_entrypoint(self, entrypoint):
        """Extract flowgraphs for a given entrypoint"""
        flowgraph_command = f"""
            MATCH (n) WHERE id(n)={entrypoint["entry_id"]}
            CALL apoc.path.subgraphAll(
                n, {{relationshipFilter: "{'|'.join(self.flows)}"}}
            )
            YIELD nodes, relationships
            RETURN nodes, relationships
        """

        flowgraph_data_list = self.neo4j_db.run(flowgraph_command).data()

        # Ensure the command returned only one subgraph per entrypoint
        assert len(flowgraph_data_list) == 1

        # Collect nodes and relationships info
        nodes = {node.identity: node for node in flowgraph_data_list[0]["nodes"]}
        relationship_list = [
            (
                rel.start_node.identity,
                rel.end_node.identity,
                [rel.identity],
                type(rel).__name__,
            )
            for rel in flowgraph_data_list[0]["relationships"]
            if type(rel).__name__ in self.flows
        ]

        # Create a map linking a node to all of their outbound relationships
        relationship_map = {}
        for relationship in relationship_list:
            if relationship[0] in relationship_map.keys():
                relationship_map[relationship[0]].append(relationship)
            else:
                relationship_map[relationship[0]] = [relationship]

        # Base variables
        all_relationships = deepcopy(relationship_list)
        previous_relationships = deepcopy(relationship_list)

        # Loop to raise the length of the relationship as long as possible
        while len(previous_relationships) > 0:
            next_relationships = []

            for relationship in previous_relationships:
                if self.max_hops != -1 and len(relationship[2]) == self.max_hops:
                    continue

                # The start node of this relationship is not a start node of any
                # other relationship.
                if relationship[1] not in relationship_map.keys():
                    continue

                # Loop over all relationship for the given start node
                for mapped_relationship in relationship_map[relationship[1]]:
                    # Make sure the relationship has not already been included
                    # to avoid infinite loops.
                    if mapped_relationship[2][0] in relationship[2]:
                        continue

                    # Make sure this is the same type of relationship.
                    if mapped_relationship[3] != relationship[3]:
                        continue

                    # Add the concatenated relationship to the list.
                    next_relationships.append(
                        (
                            relationship[0],
                            mapped_relationship[1],
                            relationship[2] + mapped_relationship[2],
                            relationship[3],
                        )
                    )

            # Save the new relationship and set them up for next iteration.
            all_relationships += next_relationships
            previous_relationships = deepcopy(next_relationships)

        flowgraph_list = [
            {
                "source": nodes[rel[0]]["ast"],
                "sink": nodes[rel[1]]["ast"],
                "flow": rel[3],
                "count": len(rel[2]),
            }
            for rel in all_relationships
            if (
                rel[0] != rel[1]
                and nodes[rel[0]].has_label("UpstreamNode")
                and nodes[rel[1]].has_label("DownstreamNode")
                and len(rel[2]) >= self.min_hops
            )
        ]

        if self.max_hops != -1:
            flowgraph_list = [
                flowgraph
                for flowgraph in flowgraph_list
                if flowgraph["count"] <= self.max_hops
            ]

        return flowgraph_list

    def get_flowgraph_count(self, flowgraph):
        """Retrieve the flowgraph count."""
        return flowgraph["count"]

    def get_label_from_flowgraph(self, flowgraph):
        """Create the label for the flowgraph."""
        source = flowgraph["source"]
        sink = flowgraph["sink"]
        flow = flowgraph["flow"]

        return "%s-%s-%s" % (source, flow, sink)

    def finalize_features(self, features, labels):
        """Perform final touches on the features before saving them to CSV."""
        # normalized_features = list()
        #
        # # Find all labels related to each type of flow
        # labels_in_flow = [
        #     [labels.index(label) for label in labels if flow in label]
        #     for flow in self.FLOWS
        # ]
        #
        # # Determine index of each labels
        # labels_index = [0] * len(labels)
        # for flow_index in range(len(labels_in_flow) - 1):
        #     for label_index in labels_in_flow[flow_index + 1]:
        #         labels_index[label_index] = flow_index + 1
        #
        # for feature_row in features:
        #     trimmed_feature_row = feature_row[:-2]
        #
        #     summed_row = [
        #         sum(
        #             [
        #                 trimmed_feature_row[label_index]
        #                 for label_index in labels_in_flow[flow_index]
        #             ]
        #         )
        #         for flow_index in range(len(self.FLOWS))
        #     ]
        #
        #     normalized_features.append(
        #         [
        #             trimmed_feature_row[i] / summed_row[labels_index[i]]
        #             if summed_row[labels_index[i]] != 0
        #             else 0
        #             for i in range(len(trimmed_feature_row))
        #         ]
        #         + feature_row[-2:]
        #     )
        #
        # return normalized_features
        return features
