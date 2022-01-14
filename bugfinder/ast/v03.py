"""
"""
from bugfinder.ast import AbstractASTMarkup


class Neo4JASTMarkup(AbstractASTMarkup):
    def configure_container(self):
        super().configure_container()
        self.container_name = "ast-markup-v03"

    def get_ast_information(self):
        return self.neo4j_db.run(
            """
            MATCH (root:DownstreamNode)
            WHERE NOT EXISTS(root.ast)
            OPTIONAL MATCH (root)-[:IS_AST_PARENT]->(sub)
            RETURN id(root) AS id, CASE
                WHEN sub IS NULL THEN root.type
                WHEN sub.type="CallExpression" THEN sub.type + "(" + SPLIT(sub.code, " ( ")[0] + ")"
                WHEN root.type="ExpressionStatement" THEN sub.type
                ELSE root.type
                END AS ast
            """
        ).data()

    def build_ast_markup(self, ast_item):
        return {"id": ast_item["id"], "ast": ast_item["ast"]}
