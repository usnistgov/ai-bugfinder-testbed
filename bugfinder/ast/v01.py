"""
"""
from bugfinder.ast import AbstractASTMarkup


class Neo4JASTMarkup(AbstractASTMarkup):
    def configure_container(self):
        super().configure_container()
        self.container_name = "ast-markup-v01"

    def get_ast_information(self):
        return self.neo4j_db.run(
            """
            MATCH (root)-[:IS_AST_PARENT*]->(sub)
            WHERE NOT EXISTS(root.ast)
            WITH DISTINCT(root), sub ORDER BY id(sub)
            RETURN id(root) AS id, COLLECT(sub.type) AS ast
        """
        ).data()

    def build_ast_markup(self, ast_item):
        return {"id": ast_item["id"], "ast": ":".join(ast_item["ast"])}
