"""
"""
from docker.errors import APIError

from tools.neo4j import Neo4J3Processing
from tools.settings import LOGGER
from tools.utils.statistics import get_time


class Neo4JAnnotations(Neo4J3Processing):
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
        """
            MATCH (n {type:"Function"}) 
            WHERE EXISTS(n.name)
            SET n.code=n.name;
        """,
        """
            MATCH (n {type:"File"}) 
            WHERE EXISTS(n.filepath)
            SET n.code=n.filepath;
        """,
        """
            MATCH (node)
            WHERE EXISTS(node.functionId)
            SET node.functionId=toString(node.functionId);
        """
    ]

    def configure_container(self):
        super().configure_container()

        self.container_name = "neo3-annot"

    def send_commands(self):
        super().send_commands()

        LOGGER.info("Running commands...")
        for cmd in self.COMMANDS:
            try:
                start = get_time()
                self.neo4j_db.run(cmd)

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


