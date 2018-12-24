from os.path import join

from py2neo import Graph

from libs.neo4j.ai import start_container as neo4j_v3_run
from settings import LOGGER, ROOT_DIR
from utils.containers import stop_container_by_name

find_ids = """
MATCH (m)-[:FLOWS_TO]->(n) 
WITH collect(m)+collect(n) AS mn
UNWIND mn AS nodes
WITH DISTINCT nodes
WHERE not exists(nodes.ast)
RETURN nodes
"""

ast_match_query = """
MATCH (m)-[r:IS_AST_PARENT]->(n) 
WHERE id(m) = %d 
RETURN n
ORDER BY n.childNum ASC
"""

ast_set = """
MATCH (m)
WHERE id(m) = %d
SET m.ast = '%s'
"""


def retrieve_children(_node):
    nodes = neo4j_db.run(ast_match_query % _node.identity).data()

    if len(nodes) == 0:
        return None

    children = []

    for n in nodes:
        current_node = n['n']

        # if current_node.get('type') in children.keys():
        #     LOGGER.warning("Overwriting tree...")

        # children[current_node.get('type')] = retrieve_children(current_node)
        children.append(
            (current_node.get('type'), retrieve_children(current_node))
        )

    return children


def flatten_dict(ast):
    if ast[1] is None:
        return ast[0]

    return "%s(%s)" % (ast[0], ",".join([flatten_dict(i) for i in ast[1]]))
    # if ast is None:
    #     return ""
    #
    # s = ""
    # for k, v in ast.items():
    #     ast_v = flatten_dict(v)
    #
    #     if len(ast_v) == 0:
    #         s += "%s" % k
    #     else:
    #         s += "%s%s" % (k, ast_v)
    #
    #     s += ","
    #
    # return "(%s)" % s[:-1]


def get_tree(_node):
    # graph_tree = OrderedDict()
    # graph_tree[_node.get('type')] = retrieve_children(_node)
    graph_tree = (_node.get('type'), retrieve_children(_node))

    return flatten_dict(graph_tree)


if __name__ == "__main__":
    arg_db_path = "./data/cwe121_0500a/neo4j_v3.db"

    db_path = join(ROOT_DIR, arg_db_path)

    neo4j_container = neo4j_v3_run(db_path, stop_after_execution=False)

    neo4j_db = Graph(
        scheme="http",
        host="0.0.0.0",
        port="7474"
    )

    LOGGER.info("Connected to Neo4j. Retrieving nodes...")

    nodes_id = neo4j_db.run(find_ids).data()
    total_nodes = len(nodes_id)

    LOGGER.info("%d nodes found. Processing..." % total_nodes)

    for node_id in nodes_id:
        ast_prop = get_tree(node_id['nodes'])

        neo4j_db.run(ast_set % (node_id['nodes'].identity, ast_prop))
        total_nodes -= 1
        LOGGER.info("Node %d processed. %d nodes left." %
                    (node_id['nodes'].identity, total_nodes))

    stop_container_by_name(neo4j_container)
