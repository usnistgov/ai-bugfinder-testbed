""" Module for annotating neo4J graphs
"""
from docker.errors import APIError

from bugfinder.processing.neo4j import Neo4J3Processing
from bugfinder.settings import LOGGER
from bugfinder.utils.statistics import get_time, display_time


class Neo4JAnnotations(Neo4J3Processing):
    """Neo4J annotation class"""

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
        # Create testcase nodes
        """
            MATCH (file:GenericNode {type:'File'})
            WITH split(file.code,'/')[2..4] as tc, COLLECT(distinct file) AS files
            MERGE (testcase:GenericNode { type:'Testcase', label:tc[0], name:tc[1]})
            WITH testcase, files
            UNWIND files as file
            WITH testcase, file
            MERGE (testcase)<-[r:IS_FILE_OF]-(file)
        """,
        # Delete data flow for the NULL keyword, which is misinterpreted by Joern
        """
            MATCH (n1:DownstreamNode)-[r:REACHES {var:"NULL"}]->(n2:DownstreamNode)
            DELETE r
        """,
        """
            MATCH (:GenericNode {type:"Symbol", code:"NULL"})<-[d:DEF]-()
            DELETE d
        """,
        # Add canonical name to File nodes
        """
            MATCH (f:GenericNode {type:"File"})
            SET f.basename=split(f.code,'/')[-1]
        """,
        # Add canonical line number to all expressions
        """
            MATCH (n1:GenericNode)
            WHERE exists(n1.location)
            SET n1.lineno=toInteger(split(n1.location,":")[0])
        """,
        # Remove extraneous data flow to exit nodes
        """
            MATCH (:GenericNode {type:"CFGExitNode"})<-[r:REACHES]-()
            DELETE r
        """,
        # Add size to dataflow relationships for arrays, including
        # all downstream nodes carrying the same variable name.
        """
            MATCH (n:GenericNode {type:"IdentifierDeclStatement"})
            WHERE n.code =~ '.* \\\\[ [0-9]* \\\\].*'
            WITH
                n,
                split(split(n.code,' [')[0],' ')[-1] as var,
                toInteger(split(split(n.code,'[ ')[1],' ]')[0]) as sz
            MATCH p=(n)-[:REACHES* {var:var}]->()
            UNWIND relationships(p) as r
            SET r.size=sz
        """,
        # Add size to dataflow for some the allocation functions, including
        # all downstream nodes carrying the same variable names.
        # FIXME Untested on "realloc". Only works when the allocation size is constant.
        #  Allocation of variable size is not handled.
        """
            MATCH (xpr:DownstreamNode)-[:IS_AST_PARENT*]->(cal:GenericNode {type:"CallExpression"})-[:IS_AST_PARENT]->(alc:GenericNode {type:"Callee"})
            WHERE xpr.type in ["IdentifierDeclStatement","ExpressionStatement"]
              AND alc.code in ["malloc","ALLOCA","realloc","calloc"]
            WITH xpr, cal, case alc.code when "realloc" then "1" else "0" end as argnum
            MATCH (cal)-[:IS_AST_PARENT]->(:GenericNode {type:"ArgumentList"})-[:IS_AST_PARENT]->(arg:GenericNode {type:"Argument",childNum:argnum})
            WITH xpr, arg
            MATCH (arg)-[:IS_AST_PARENT*]->(operand:GenericNode)
            WHERE substring(operand.type,0,6)<>"Sizeof" and not (operand)-[:IS_AST_PARENT]->()
            WITH xpr, collect(operand) as oplist
            WHERE size(oplist)=1 and oplist[0].type="PrimaryExpression"
            MATCH (xpr)-[:DEF]->(sym:GenericNode {type:"Symbol"})
            MATCH dfp=(xpr)-[:REACHES* {var:sym.code}]->()
            UNWIND relationships(dfp) as dfr
            SET dfr.size=tointeger(oplist[0].code)
        """,
        # Forward size to new variable data flow on assignments,
        # including all downstream nodes carrying the same variable name.
        # FIXME Perhaps handle *var as well.
        """
            MATCH (axpr:GenericNode {type:"AssignmentExpression"})<-[:IS_AST_PARENT*]-(expr:DownstreamNode)
            WHERE expr.type in ["ExpressionStatement","IdentifierDeclStatement","ForInit"]
            MATCH (axpr)-[:USE]->(ssym:GenericNode {type:"Symbol"})
            MATCH (expr)<-[src:REACHES {var:ssym.code}]-() where exists(src.size)
            MATCH (axpr)-[:DEF]->(dsym:GenericNode {type:"Symbol"})
            MATCH p=(expr)-[:REACHES* {var:dsym.code}]->()
            UNWIND relationships(p) as dst
            SET dst.size=src.size
            SET dst.src=src.var
        """,
        # Remove incorrect DEF relationships in arr[x] = data where x was considered
        # DEF'ed by the expression.
        """
            MATCH (expr:DownstreamNode)-[:IS_AST_PARENT*]->(asgn:GenericNode {type:"AssignmentExpression"})-[:IS_AST_PARENT]->(aidx:GenericNode {type:"ArrayIndexing",childNum:"0"})-[:IS_AST_PARENT]->(idfr:GenericNode {type:"Identifier",childNum:"1"})
            MATCH (expr)-[rd1:DEF]->(sym:GenericNode {type:"Symbol",code:"* "+idfr.code})<-[rd2:DEF]-(asgn)
            DELETE rd1, rd2
        """,
        # Delete incorrect DEF relationships created by Joern
        """
            MATCH (decl:GenericNode {type:"IdentifierDeclStatement"})-[rdef:DEF]->(sym:GenericNode {type:"Symbol"})
            WHERE left(sym.code,2)<>"& "
              AND not (decl)-[:IS_AST_PARENT]->(:GenericNode {type:"IdentifierDecl"})-[:DEF]->(sym)
            DELETE rdef
        """,
    ]

    def configure_container(self):
        """Setup container variables."""
        self.fix_data_folder_rights()

        super().configure_container()
        self.container_name = "neo3-annot"

    def send_commands(self):
        """Send commands to the container"""
        super().send_commands()

        LOGGER.debug("Running annotation commands...")
        for cmd in self.COMMANDS:
            try:
                start = get_time()
                self.neo4j_db.run(cmd)

                LOGGER.info(
                    "Annotation command %d/%d run in %s",
                    self.COMMANDS.index(cmd) + 1,
                    len(self.COMMANDS),
                    display_time(get_time() - start),
                )
            except APIError as error:
                LOGGER.info("An error occured while executing command: %s", str(error))
                break

        LOGGER.info("Database annotated.")
