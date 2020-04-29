"""
"""
from bugfinder.ast import AbstractASTMarkup


class Neo4JASTMarkup(AbstractASTMarkup):
    def configure_container(self):
        super().configure_container()
        self.container_name = "ast-markup-v02"

    def get_ast_information(self):
        get_main_nodes_info = """
            MATCH (m)-[:FLOWS_TO]->(n) 
            WITH collect(m)+collect(n) AS mn
            UNWIND mn AS node
            WITH DISTINCT node
            WHERE not exists(node.ast)
            RETURN DISTINCT id(node) as id, node.type as type
        """
        get_child_nodes_info = """
            MATCH (m)-[:IS_AST_PARENT*]->(n)
            WHERE id(m)=%s
            WITH collect(n) AS ast_nodes
            UNWIND ast_nodes AS ast_node
            MATCH (ast_node)<-[:IS_AST_PARENT]-(ast_parent)
            RETURN ast_node.type AS type, id(ast_node) AS id, 
                id(ast_parent) AS parent, ast_node.childNum AS child_num
        """

        return [
            {
                "id": node["id"],
                "type": node["type"],
                "ast": [
                    {
                        "id": ast_node["id"],
                        "parent": ast_node["parent"],
                        "type": ast_node["type"],
                        "child_num": ast_node["child_num"],
                    }
                    for ast_node in self.neo4j_db.run(get_child_nodes_info % node["id"])
                ],
            }
            for node in self.neo4j_db.run(get_main_nodes_info).data()
        ]

    def build_ast_markup(self, ast_item):
        def sort_by_child_num(item):
            return int(item["child_num"])

        def build_tree(node, ast_list):
            node_children = [  # Retieve children of current node
                ast_node for ast_node in ast_list if ast_node["parent"] == node["id"]
            ]

            # If there are no children, return node type
            if len(node_children) == 0:
                return node["type"]

            return "%s(%s)" % (
                node["type"],
                ",".join(
                    [
                        build_tree(child, ast_list)
                        for child in sorted(node_children, key=sort_by_child_num)
                    ]
                ),
            )

        return {"id": ast_item["id"], "ast": build_tree(ast_item, ast_item["ast"])}
