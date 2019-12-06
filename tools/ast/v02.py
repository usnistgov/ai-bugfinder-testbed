"""
"""
import pickle
import re
from os.path import join

from past.utils import old_div

from tools.neo4j import Neo4J3Processing
from tools.settings import LOGGER


class Neo4JASTMarkup(Neo4J3Processing):

    def configure_container(self):
        super().configure_container()

        self.container_name = "neo3-ast-markup-v02"

    def build_tree(self, node, links):
        if node["id"] not in links:
            return node["type"]

        child_types = list()
        for child in sorted(links[node["id"]], key=self.sort_by_child_num):
            child_types.append(
                self.build_tree(child, links)
            )

        return "%s(%s)" % (node["type"], ','.join(child_types))

    @staticmethod
    def sort_by_child_num(item):
        return int(item["childNum"])

    def get_query(self, neo4j_db, node_list):
        roots_query = """
            UNWIND %s as m_id
            MATCH (m)
            WHERE id(m)=m_id
            RETURN id(m) AS id, m.type as type
        """
        links_query = """
            UNWIND %s as m_id
            MATCH (m)-[:IS_AST_PARENT*]->(n)
            WHERE id(m)=m_id
            WITH collect(n) AS nn
            UNWIND nn AS ni
            MATCH (ni)<-[:IS_AST_PARENT]-(o)
            RETURN ni.type AS type, id(ni) AS id, 
                id(o) AS parent, ni.childNum AS childNum
        """

        LOGGER.info("Querying nodes...")
        roots_query_results = neo4j_db.run(roots_query % str(node_list)).data()
        roots = {root["id"]: root["type"] for root in roots_query_results}

        LOGGER.info("Node info retrieved. Querying links...")

        links_query_result = neo4j_db.run(links_query % str(node_list)).data()
        links = {res["parent"]: list() for res in links_query_result}

        for res in links_query_result:
            links[res["parent"]].append(res)

        LOGGER.info("Links info retrieved. Building tree...")

        for root in list(roots.keys()):
            if root not in list(links.keys()):
                continue

            root_children = list()
            for child in sorted(links[root], key=self.sort_by_child_num):
                root_children.append(
                    self.build_tree(child, links)
                )

            roots[root] += "(%s)" % ','.join(root_children)

        LOGGER.info("Tree built. Uploading ASTs...")
        return roots

    def send_commands(self):
        super().send_commands()

        find_ids = """
            MATCH (m)-[:FLOWS_TO]->(n) 
            WITH collect(m)+collect(n) AS mn
            UNWIND mn AS nodes
            WITH DISTINCT nodes
            WHERE not exists(nodes.ast)
            RETURN DISTINCT id(nodes) as id
        """
        set_ast_cmd = """
           UNWIND %s as data
           MATCH (n)
           WHERE id(n) = data.id
           SET n.ast = data.ast
        """

        LOGGER.info("Connected to Neo4j. Retrieving nodes...")

        nodes_id = [n["id"] for n in self.neo4j_db.run(find_ids).data()]
        total_nodes = len(nodes_id)

        LOGGER.info("%d nodes found. Processing..." % total_nodes)

        ast_update_dict_raw = self.get_query(self.neo4j_db, nodes_id)
        ast_update_dict_raw = [
            {"id": root_id, "ast": ast_repr}
            for root_id, ast_repr in list(ast_update_dict_raw.items())
        ]

        with open(join(self.dataset.path, "ast.bin"), "wb") as ast_file:
            pickle.dump(
                [ast_item["ast"] for ast_item in ast_update_dict_raw],
                ast_file
            )

        LOGGER.info(
            "Update dict generated (%d entries). Uploading..." %
            len(ast_update_dict_raw)
        )

        # Slicing the list into several command
        cmd_list = []
        limit = 2000

        for i in range(old_div(len(ast_update_dict_raw), limit) + 1):
            lower = i * limit
            upper = (i + 1) * limit

            if upper >= len(ast_update_dict_raw):
                upper = len(ast_update_dict_raw)

            cmd_list.append(ast_update_dict_raw[lower:upper])

        LOGGER.info("%d commands prepared" % len(cmd_list))

        for cmd in cmd_list:
            LOGGER.info("Prepping command...")

            # Clenup dict to be parsed by Neo4J
            ast_update_dict = str(cmd)
            ast_update_dict = re.sub(r'u\'([^\']*)\'', "'\\g<1>'", ast_update_dict)
            ast_update_dict = re.sub(r'\'([^\']*)\':', "\\g<1>:", ast_update_dict)

            LOGGER.info("Updating AST...")
            try:
                self.neo4j_db.run(set_ast_cmd % ast_update_dict)
            except Exception as e:
                LOGGER.info(str(e))

        LOGGER.info("Processing completed.")
