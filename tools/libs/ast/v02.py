import re

from py2neo import Graph

from libs.neo4j.ai import start_container as run_neo4j_v3
from settings import LOGGER
from utils.containers import stop_container_by_name


def sort_by_child_num(item):
    return int(item["childNum"])


def build_tree(node, links):
    if node["id"] not in links:
        return node["type"]

    child_types = list()
    for child in sorted(links[node["id"]], key=sort_by_child_num):
        child_types.append(
            build_tree(child, links)
        )

    return "%s(%s)" % (node["type"], ','.join(child_types))


def get_query(neo4j_db, node_list):
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

    for root in roots.keys():
        if root not in links.keys():
            continue

        root_children = list()
        for child in sorted(links[root], key=sort_by_child_num):
            root_children.append(
                build_tree(child, links)
            )

        roots[root] += "(%s)" % ','.join(root_children)

    LOGGER.info("Tree built. Uploading ASTs...")
    return roots


def main(db_path):
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

    neo4j_container_obj, neo4j_container_name = run_neo4j_v3(db_path, stop_after_execution=False)

    neo4j_db = Graph(
        scheme="http",
        host="0.0.0.0",
        port="7474"
    )

    LOGGER.info("Connected to Neo4j. Retrieving nodes...")

    nodes_id = [n["id"] for n in neo4j_db.run(find_ids).data()]
    total_nodes = len(nodes_id)

    LOGGER.info("%d nodes found. Processing..." % total_nodes)

    ast_update_dict_raw = get_query(neo4j_db, nodes_id)
    ast_update_dict_raw = [
        {"id": root_id, "ast": ast_repr}
        for root_id, ast_repr in ast_update_dict_raw.items()
    ]

    LOGGER.info(
        "Update dict generated (%d entries). Uploading..." %
        len(ast_update_dict_raw)
    )

    # Slicing the list into several command
    cmd_list = []
    limit = 2000

    for i in xrange(len(ast_update_dict_raw) / limit + 1):
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
            LOGGER.info(e.message)

    LOGGER.info("Processing completed...")
    stop_container_by_name(neo4j_container_name)
