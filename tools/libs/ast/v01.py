import re

from py2neo import Graph

from libs.neo4j.ai import start_container as run_neo4j_v3
from settings import LOGGER
from utils.containers import stop_container_by_name


def main(db_path):
    get_ast_cmd = """
        MATCH (root)-[:IS_AST_PARENT*]->(sub)
        WHERE (root:UpstreamNode OR root:DownstreamNode)
        AND NOT EXISTS(root.ast)
        WITH DISTINCT(root), sub ORDER BY id(sub)
        RETURN id(root) AS id, COLLECT(sub.type) AS ast
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

    LOGGER.info("Retrieving AST...")

    ast_list = neo4j_db.run(get_ast_cmd).data()

    LOGGER.info("%d item found. Slicing AST..." % len(ast_list))

    # Slicing the list into several command
    cmd_list = []
    limit = 2000

    for i in xrange(len(ast_list) / limit + 1):
        lower = i*limit
        upper = (i+1)*limit

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
        neo4j_db.run(set_ast_cmd % ast_update_dict)

    LOGGER.info("AST updated")

    stop_container_by_name(neo4j_container_name)
