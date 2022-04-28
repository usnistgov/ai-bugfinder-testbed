""" Module containing the first version of the AST markup algorithm.
"""
from bugfinder.processing.ast import AbstractASTMarkup


class Neo4JASTMarkup(AbstractASTMarkup):
    """Class for version 1 of the AST markup."""

    def configure_container(self):
        """Setup container variables"""
        super().configure_container()
        self.container_name = "ast-markup-v01"

    def get_ast_information(self):
        """Retrieve AST information"""
        return self.neo4j_db.run(
            """
            MATCH (root)-[:IS_AST_PARENT*]->(sub)
            WHERE NOT EXISTS(root.ast)
            WITH DISTINCT(root), sub ORDER BY id(sub)
            RETURN id(root) AS id, COLLECT(sub.type) AS ast
        """
        ).data()

    def build_ast_markup(self, ast_item):
        """Build the AST markup."""
        return {"id": ast_item["id"], "ast": ":".join(ast_item["ast"])}
