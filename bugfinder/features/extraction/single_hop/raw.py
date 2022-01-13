"""
"""
from bugfinder.features.extraction import FlowGraphFeatureExtractor


class FeatureExtractor(FlowGraphFeatureExtractor):
    def configure_container(self):
        super().configure_container()
        self.container_name = "fext-single-hop-raw"

    def get_flowgraph_list_for_entrypoint(self, entrypoint):
        flowgraph_command = """
            MATCH p = (root1:UpstreamNode)-[
                rel:FLOWS_TO|:REACHES|:CONTROLS
            ]->(root2:DownstreamNode)
            WHERE root1.functionId="%s"
            RETURN distinct root1.ast AS source, root2.ast AS sink, 
                type(rel) AS flow, count(p) AS count
        """

        return self.neo4j_db.run(flowgraph_command % entrypoint["function_id"]).data()

    def get_flowgraph_count(self, flowgraph):
        return flowgraph["count"]

    def get_label_from_flowgraph(self, flowgraph):
        source = flowgraph["source"]
        sink = flowgraph["sink"]
        flow = flowgraph["flow"]

        return "%s-%s-%s" % (source, flow, sink)
