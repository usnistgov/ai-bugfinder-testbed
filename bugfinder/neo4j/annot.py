"""
"""
from docker.errors import APIError

from bugfinder.neo4j import Neo4J3Processing
from bugfinder.settings import LOGGER
from bugfinder.utils.statistics import get_time, display_time


class Neo4JAnnotations(Neo4J3Processing):
    COMMANDS = [
        "MATCH (n) SET n:GenericNode;",
        "CREATE INDEX ON :GenericNode(type);",
        "CREATE INDEX ON :GenericNode(code);",
        "CREATE INDEX ON :GenericNode(filepath);",
        """
            MATCH (root1:GenericNode)-[:FLOWS_TO|REACHES|CONTROLS]->()
            WHERE root1.type IN [ 
                'Condition', 'ForInit', 'IncDecOp', 'PostIncDecOperationExpression',
                'ExpressionStatement', 'IdentifierDeclStatement', 'CFGEntryNode',
                'BreakStatement', 'Parameter', 'ReturnStatement', 'Label',
                'GotoStatement', 'Statement', 'UnaryExpression' 
            ]
            SET root1:UpstreamNode;  
        """,
        """
            MATCH ()-[:FLOWS_TO|REACHES|CONTROLS]->(root2:GenericNode)
            WHERE root2.type IN [
                'CFGExitNode', 'IncDecOp', 'Condition', 'PostIncDecOperationExpression',
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
        """,
        """
            match (file:GenericNode {type:'File'})
            with split(file.code,'/')[2..4] as tc, collect(distinct file) as files
            merge (testcase:GenericNode { type:'Testcase', label:tc[0], name:tc[1]})
            with testcase, files
            unwind files as file
            with testcase, file
            merge (testcase)<-[r:IS_FILE_OF]-(file)
        """,
        """
            // Delete dataflow for the NULL keyword, which is misinterpreted by Joern
            match (n1:DownstreamNode)-[r:REACHES {var:"NULL"}]->(n2:DownstreamNode)
            delete r
        """, """
            match (:GenericNode {type:"Symbol",code:"NULL"})<-[d:DEF]-()
            delete d
        """,
        """
            // Add canonical name to File nodes
            match (f:GenericNode {type:"File"})
            set f.basename=split(f.code,'/')[-1]
        """, """
            // Add canonical line number to all expressions
            match (n1:GenericNode)
            where exists(n1.location)
            set n1.lineno=toInteger(split(n1.location,":")[0])
        """,
    ]

    def configure_container(self):
        self.fix_data_folder_rights()

        super().configure_container()
        self.container_name = "neo3-annot"

    def send_commands(self):
        super().send_commands()

        LOGGER.debug("Running annotation commands...")
        for cmd in self.COMMANDS:
            try:
                start = get_time()
                self.neo4j_db.run(cmd)

                LOGGER.info(
                    "Annotation command %d/%d run in %s"
                    % (
                        self.COMMANDS.index(cmd) + 1,
                        len(self.COMMANDS),
                        display_time(get_time() - start),
                    )
                )
            except APIError as error:
                LOGGER.info("An error occured while executing command: %s" % str(error))
                break

        LOGGER.info("Database annotated.")
