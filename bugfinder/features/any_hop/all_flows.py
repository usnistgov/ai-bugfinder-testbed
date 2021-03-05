"""
"""
from bugfinder.dataset.processing import DatasetProcessingDeprecation
from bugfinder.features import FlowGraphFeatureExtractor


class FeatureExtractor(FlowGraphFeatureExtractor):
    def __init__(self, dataset):
        notice = """
            The Any Hop All Flows (AHAF) extractor is being deprecated and will be
            removed in a future version. This extractor does not adapt well for large
            test cases and, hence, is being deprecated.
        """

        super().__init__(
            dataset, deprecation_warning=DatasetProcessingDeprecation(notice)
        )

    def configure_container(self):
        super().configure_container()
        self.container_name = "fext-any-hop-all-flows"

    def get_flowgraph_list_for_entrypoint(self, entrypoint):
        flowgraph_command = """
            MATCH 
                (entry)-[:FLOWS_TO|REACHES|CONTROLS*0..5]->(root1:UpstreamNode)
            WHERE entry.functionId="%s"
            WITH distinct root1
            MATCH 
                p=(root1)-[
                    :FLOWS_TO|REACHES|CONTROLS*1..3
                ]->(root2:DownstreamNode)
            WHERE root1<>root2
            WITH extract(r in relationships(p) | type(r)) as flow, 
                root1.ast as source, root2.ast as sink
            RETURN source, flow, sink
        """

        return self.neo4j_db.run(flowgraph_command % entrypoint["id"]).data()

    def get_flowgraph_count(self, flowgraph):
        return 1

    def get_label_from_flowgraph(self, flowgraph):
        source = flowgraph["source"]
        sink = flowgraph["sink"]
        flow = ":".join(flowgraph["flow"])

        return "%s-%s-%s" % (source, flow, sink)
