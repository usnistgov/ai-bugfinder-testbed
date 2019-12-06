"""
"""
import re

from past.utils import old_div

from tools.neo4j import Neo4J3Processing
from tools.settings import LOGGER


class Neo4JASTMarkup(Neo4J3Processing):

    def configure_container(self):
        super().configure_container()

        self.container_name = "neo3-ast-markup-v01"

    def send_commands(self):
        super().send_commands()

        # get_ast_cmd = """
        #     MATCH (root)-[:IS_AST_PARENT*]->(sub)
        #     WHERE (root:UpstreamNode OR root:DownstreamNode)
        #     AND NOT EXISTS(root.ast)
        #     WITH DISTINCT(root), sub ORDER BY id(sub)
        #     RETURN id(root) AS id, COLLECT(sub.type) AS ast
        # """
        get_ast_cmd = """
            MATCH (root)-[:IS_AST_PARENT*]->(sub)
            WHERE NOT EXISTS(root.ast)
            WITH DISTINCT(root), sub ORDER BY id(sub)
            RETURN id(root) AS id, COLLECT(sub.type) AS ast
        """
        set_ast_cmd = """
           UNWIND %s as data
           MATCH (n)
           WHERE id(n) = data.id
           SET n.ast = data.ast
        """

        LOGGER.info("Retrieving AST...")

        ast_list = self.neo4j_db.run(get_ast_cmd).data()

        LOGGER.info("%d item found. Slicing AST..." % len(ast_list))

        # Slicing the list into several command
        cmd_list = []
        limit = 2000

        for i in range(old_div(len(ast_list), limit) + 1):
            lower = i * limit
            upper = (i + 1) * limit

            if upper >= len(ast_list):
                upper = len(ast_list)

            cmd_list.append(ast_list[lower:upper])

        LOGGER.info("%d commands prepared" % len(cmd_list))

        for cmd in cmd_list:
            LOGGER.info("Prepping command...")

            # For each item retrieve the correct notation
            for ast_item in cmd:
                ast_repr = ':'.join(ast_item["ast"])
                ast_item["ast"] = ast_repr

            # Clenup dict to be parsed by Neo4J
            ast_update_dict = str(cmd)
            ast_update_dict = re.sub(r'u\'([^\']*)\'', "'\\g<1>'", ast_update_dict)
            ast_update_dict = re.sub(r'\'([^\']*)\':', "\\g<1>:", ast_update_dict)

            LOGGER.info("Updating AST...")
            self.neo4j_db.run(set_ast_cmd % ast_update_dict)

        LOGGER.info("AST updated")
