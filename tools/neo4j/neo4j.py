from os.path import realpath
import re

from docker.errors import APIError
from past.utils import old_div
from py2neo import Graph

from tools.dataset.processing import DatasetProcessingWithContainer
from tools.settings import NEO4J_V3_MEMORY, LOGGER
from tools.utils.containers import wait_log_display
from tools.utils.rand import get_rand_string
from tools.utils.statistics import get_time


class Neo4JImporter(DatasetProcessingWithContainer):
    db_path = "neo4j_v3.db"
    START_STRING = "Remote interface available"

    def configure_container(self):
        self.image_name = "neo4j-ai:latest"
        self.container_name = "neo3-importer"
        self.environment = {
            "NEO4J_dbms_memory_pagecache_size": NEO4J_V3_MEMORY,
            "NEO4J_dbms_memory_heap_max__size": NEO4J_V3_MEMORY,
            "NEO4J_dbms_allow__upgrade": "true",
            "NEO4J_dbms_shell_enabled": "true",
            "NEO4J_AUTH": "none"
        }
        self.ports = {
            "7474": "7474",
            "7687": "7687",
        }
        self.volumes = {
            realpath("%s/%s" % (self.dataset.path, self.db_path)):
                "/data/databases/%s" % self.db_path,
            realpath("%s/joern.db/import" % self.dataset.path):
                "/var/lib/neo4j/import"
        }

    def send_commands(self):
        wait_log_display(self.container, self.START_STRING)

        self.container.exec_run(
            """
            ./bin/neo4j-admin import --database=%s --delimiter='TAB'
                --nodes=/var/lib/neo4j/import/nodes.csv
                --relationships=/var/lib/neo4j/import/edges.csv
            """ % self.db_path
        )

        LOGGER.info("CSV file imported.")


class Neo4JAnnotations(DatasetProcessingWithContainer):
    START_STRING = "Remote interface available"
    COMMANDS = [
        "MATCH (n) SET n:GenericNode;",
        "CREATE INDEX ON :GenericNode(type);",
        "CREATE INDEX ON :GenericNode(filepath);",
        """
        MATCH (root1:GenericNode)-[:FLOWS_TO|REACHES|CONTROLS]->()
        WHERE root1.type IN [ 
            'Condition', 'ForInit', 'IncDecOp',
            'ExpressionStatement', 'IdentifierDeclStatement', 'CFGEntryNode',
            'BreakStatement', 'Parameter', 'ReturnStatement', 'Label',
            'GotoStatement', 'Statement', 'UnaryExpression' 
        ]
        SET root1:UpstreamNode;  
        """,
        """
        MATCH ()-[:FLOWS_TO|REACHES|CONTROLS]->(root2:GenericNode)
        WHERE root2.type IN [
            'CFGExitNode', 'IncDecOp', 'Condition',
            'ExpressionStatement', 'ForInit', 'IdentifierDeclStatement',
            'BreakStatement', 'Parameter', 'ReturnStatement', 'Label',
            'GotoStatement', 'Statement', 'UnaryExpression' 
        ]
        SET root2:DownstreamNode;
        """,
    ]

    def configure_container(self):
        self.image_name = "neo4j-ai:latest"
        self.container_name = "neo3-annot"
        self.environment = {
            "NEO4J_dbms_memory_pagecache_size": NEO4J_V3_MEMORY,
            "NEO4J_dbms_memory_heap_max__size": NEO4J_V3_MEMORY,
            "NEO4J_dbms_allow__upgrade": "true",
            "NEO4J_dbms_shell_enabled": "true",
            "NEO4J_AUTH": "none"
        }
        self.ports = {
            "7474": "7474",
            "7687": "7687",
        }
        self.volumes = {
            realpath("%s/neo4j_v3.db" % self.dataset.path):
                "/data/databases/graph.db",
        }

    def send_commands(self):
        wait_log_display(self.container, self.START_STRING)

        LOGGER.info("Running commands...")

        neo4j_db = Graph(
            scheme="http",
            host="0.0.0.0",
            port="7474"
        )

        for cmd in self.COMMANDS:
            try:
                start = get_time()
                neo4j_db.run(cmd)

                LOGGER.info(
                    "Command %d out of %d run in %dms" %
                    (
                        self.COMMANDS.index(cmd) + 1,
                        len(self.COMMANDS),
                        get_time() - start
                    )
                )
            except APIError as error:
                LOGGER.info(
                    "An error occured while executing command: %s" %
                    str(error)
                )
                break

        LOGGER.info("Database annotated.")


class Neo4JASTMarkup(DatasetProcessingWithContainer):
    START_STRING = "Remote interface available"

    def configure_container(self):
        self.image_name = "neo4j-ai:latest"
        self.container_name = "neo3-ast-markup"
        self.environment = {
            "NEO4J_dbms_memory_pagecache_size": NEO4J_V3_MEMORY,
            "NEO4J_dbms_memory_heap_max__size": NEO4J_V3_MEMORY,
            "NEO4J_dbms_allow__upgrade": "true",
            "NEO4J_dbms_shell_enabled": "true",
            "NEO4J_AUTH": "none"
        }
        self.ports = {
            "7474": "7474",
            "7687": "7687",
        }
        self.volumes = {
            realpath("%s/neo4j_v3.db" % self.dataset.path):
                "/data/databases/graph.db",
        }

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
        wait_log_display(self.container, self.START_STRING)

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

        neo4j_db = Graph(
            scheme="http",
            host="0.0.0.0",
            port="7474"
        )

        LOGGER.info("Connected to Neo4j. Retrieving nodes...")

        nodes_id = [n["id"] for n in neo4j_db.run(find_ids).data()]
        total_nodes = len(nodes_id)

        LOGGER.info("%d nodes found. Processing..." % total_nodes)

        ast_update_dict_raw = self.get_query(neo4j_db, nodes_id)
        ast_update_dict_raw = [
            {"id": root_id, "ast": ast_repr}
            for root_id, ast_repr in list(ast_update_dict_raw.items())
        ]

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
                neo4j_db.run(set_ast_cmd % ast_update_dict)
            except Exception as e:
                LOGGER.info(str(e))

        LOGGER.info("Processing completed.")
