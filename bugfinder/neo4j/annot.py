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
        # Create testcase nodes
        """
            match (file:GenericNode {type:'File'})
            with split(file.code,'/')[2..4] as tc, collect(distinct file) as files
            merge (testcase:GenericNode { type:'Testcase', label:tc[0], name:tc[1]})
            with testcase, files
            unwind files as file
            with testcase, file
            merge (testcase)<-[r:IS_FILE_OF]-(file)
        """,
        # Delete dataflow for the NULL keyword, which is misinterpreted by Joern
        """
            match (n1:DownstreamNode)-[r:REACHES {var:"NULL"}]->(n2:DownstreamNode)
            delete r
        """,
        """
            match (:GenericNode {type:"Symbol",code:"NULL"})<-[d:DEF]-()
            delete d
        """,
        # Add canonical name to File nodes
        """
            match (f:GenericNode {type:"File"})
            set f.basename=split(f.code,'/')[-1]
        """,
        # Add canonical line number to all expressions
        """
            match (n1:GenericNode)
            where exists(n1.location)
            set n1.lineno=toInteger(split(n1.location,":")[0])
        """,
        # Remove extraneous dataflow to exit nodes
        """
            match (:GenericNode {type:"CFGExitNode"})<-[r:REACHES]-()
            delete r
        """,
        # Add size to dataflow relationships for arrays, including
        # all downstream nodes carrying the same variable name.
        """
            match (n:GenericNode {type:"IdentifierDeclStatement"})
            where n.code =~ '.* \\\\[ [0-9]* \\\\].*'
            //where n.code =~ '.* \\[ [0-9]* \\].*'
            with n, split(split(n.code,' [')[0],' ')[-1] as var, toInteger(split(split(n.code,'[ ')[1],' ]')[0]) as sz
            match p=(n)-[:REACHES* {var:var}]->()
            unwind relationships(p) as r
            set r.size=sz
        """,
        # Add size to dataflow for some the allocation functions, including
        # all downstream nodes carrying the same variable names.
        # FIXME This is untested on "realloc"
        # FIXME This only works when the allocation size is constant. Allocation of variable size is not handled.
        """
            match (xpr:DownstreamNode)-[:IS_AST_PARENT*]->(cal:GenericNode {type:"CallExpression"})-[:IS_AST_PARENT]->(alc:GenericNode {type:"Callee"})
            where xpr.type in ["IdentifierDeclStatement","ExpressionStatement"]
              and alc.code in ["malloc","ALLOCA","realloc","calloc"]
            with xpr, cal, case alc.code when "realloc" then "1" else "0" end as argnum
            match (cal)-[:IS_AST_PARENT]->(:GenericNode {type:"ArgumentList"})-[:IS_AST_PARENT]->(arg:GenericNode {type:"Argument",childNum:argnum})
            with xpr, arg
            match (arg)-[:IS_AST_PARENT*]->(operand:GenericNode)
            where substring(operand.type,0,6)<>"Sizeof" and not (operand)-[:IS_AST_PARENT]->()
            with xpr, collect(operand) as oplist
            where size(oplist)=1 and oplist[0].type="PrimaryExpression"
            match (xpr)-[:DEF]->(sym:GenericNode {type:"Symbol"})
            match dfp=(xpr)-[:REACHES* {var:sym.code}]->()
            unwind relationships(dfp) as dfr
            set dfr.size=tointeger(oplist[0].code)
        """,
        # Forward size to new variable data flow on assignments,
        # including all downstream nodes carrying the same variable name.
        # FIXME Perhaps handle *var as well.
        """
            match (axpr:GenericNode {type:"AssignmentExpression"})<-[:IS_AST_PARENT*]-(expr:DownstreamNode)
            where expr.type in ["ExpressionStatement","IdentifierDeclStatement","ForInit"]
            match (axpr)-[:USE]->(ssym:GenericNode {type:"Symbol"})
            match (expr)<-[src:REACHES {var:ssym.code}]-() where exists(src.size)
            match (axpr)-[:DEF]->(dsym:GenericNode {type:"Symbol"})
            match p=(expr)-[:REACHES* {var:dsym.code}]->()
            unwind relationships(p) as dst
            set dst.size=src.size
            set dst.src=src.var
        """,
        # Remove incorrect DEF relationships in arr[x] = data where x was considered DEF'ed by the expression
        """
            match (expr:DownstreamNode)-[:IS_AST_PARENT*]->(asgn:GenericNode {type:"AssignmentExpression"})-[:IS_AST_PARENT]->(aidx:GenericNode {type:"ArrayIndexing",childNum:"0"})-[:IS_AST_PARENT]->(idfr:GenericNode {type:"Identifier",childNum:"1"})
            match (expr)-[rd1:DEF]->(sym:GenericNode {type:"Symbol",code:"* "+idfr.code})<-[rd2:DEF]-(asgn)
            delete rd1, rd2
        """,
        # Delete incorrect DEF relationships created by Joern
        """
            match (decl:GenericNode {type:"IdentifierDeclStatement"})-[rdef:DEF]->(sym:GenericNode {type:"Symbol"})
            where left(sym.code,2)<>"& "
              and not (decl)-[:IS_AST_PARENT]->(:GenericNode {type:"IdentifierDecl"})-[:DEF]->(sym)
              delete rdef
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
