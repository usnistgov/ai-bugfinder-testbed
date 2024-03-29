""" Any hop single flow feature extractor module
"""
from bugfinder.features.extraction import FlowGraphFeatureExtractor


class FeatureExtractor(FlowGraphFeatureExtractor):
    """Any hop single flow feature extractor"""

    FLOWS = ["CONTROLS", "FLOWS_TO", "REACHES"]

    def configure_container(self):
        """Configure container variable"""
        super().configure_container()
        self.container_name = "fext-any-hop-single-flow"

    def get_flowgraph_list_for_entrypoint(self, entrypoint):
        """Create list of flow graphs for a given entrypoint"""
        flowgraph_command = """
               MATCH p = (root1:UpstreamNode)-[:%s*]->(root2:DownstreamNode)
               WHERE root1.functionId="%s"
               RETURN distinct root1.ast AS source, root2.ast AS sink,
                   count(p) as count
           """
        flowgraph_list = []

        for flow in self.FLOWS:
            flow_information = {"flow": flow}
            flowgraph_data_list = self.neo4j_db.run(
                flowgraph_command % (flow, entrypoint["function_id"])
            ).data()

            for flowgraph_data in flowgraph_data_list:
                flowgraph_data.update(flow_information)

            flowgraph_list += flowgraph_data_list

        return flowgraph_list

    def get_flowgraph_count(self, flowgraph):
        """Count the number of flowgraphs"""
        return flowgraph["count"]

    def get_label_from_flowgraph(self, flowgraph):
        """Create the label for a given flow graph"""
        source = flowgraph["source"]
        sink = flowgraph["sink"]
        flow = flowgraph["flow"]

        return "%s-%s-%s" % (source, flow, sink)

    @staticmethod
    def finalize_features(features, labels):
        """Finalize feature before exporting to CSV file"""
        normalized_features = []

        flows = ["CONTROLS", "REACHES", "FLOWS_TO"]

        # Find all labels related to each type of flow
        labels_in_flow = [
            [labels.index(label) for label in labels if flow in label] for flow in flows
        ]

        # Determine index of each labels
        labels_index = [0] * len(labels)
        for flow_index in range(len(labels_in_flow) - 1):
            for label_index in labels_in_flow[flow_index + 1]:
                labels_index[label_index] = flow_index + 1

        for feature_row in features:
            trimmed_feature_row = feature_row[:-2]

            summed_row = [
                sum(
                    [
                        trimmed_feature_row[label_index]
                        for label_index in labels_in_flow[flow_index]
                    ]
                )
                for flow_index in range(len(flows))
            ]

            normalized_features.append(
                [
                    trimmed_feature_row[i] / summed_row[labels_index[i]]
                    if summed_row[labels_index[i]] != 0
                    else 0
                    for i in range(len(trimmed_feature_row))
                ]
                + feature_row[-2:]
            )

        return normalized_features
