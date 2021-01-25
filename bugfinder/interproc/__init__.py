"""
"""
from concurrent.futures import ThreadPoolExecutor

from bugfinder.neo4j import Neo4J3Processing
from bugfinder.settings import ROOT_DIR, LOGGER, POOL_SIZE


# TODO
# Check if Joern includes global variables in data flow
# Handle nested function calls in the control+data flow graph
# Add REACHES to sink functions like memcpy
# Flag vulnerability sinks


class InterprocMerger(Neo4J3Processing):
    
    def configure_container(self):
        super().configure_container()
        self.container_name = "interproc"

    def get_testcase_ids(self):
        list_testcases_cmd = """
            match (tc:GenericNode {type:"Testcase"}) return id(tc) as id
        """
        return self.neo4j_db.run(list_testcases_cmd).data()

    def interproc_worker(self, tcid):
        for cmd in self.interproc_cmds_tc:
            self.neo4j_db.run(cmd % tcid["id"])

    def send_commands(self):
        self.fix_data_folder_rights()

        super().send_commands()

        LOGGER.info("Retrieving testcases...")
        tcid_list = self.get_testcase_ids()

        LOGGER.debug("%d testcases retrieved. Connecting interprocedural flows using %d workers..." % (len(tcid_list), POOL_SIZE))
        with ThreadPoolExecutor(max_workers=POOL_SIZE+8) as executor:
            res = executor.map(self.interproc_worker, tcid_list)

        LOGGER.debug("Interprocedural flows connected, marking data sinks...")
        for cmd in self.interproc_cmds_post:
            self.neo4j_db.run(cmd)

        LOGGER.info("All done.")

    interproc_cmds_tc = [
        """
            // Connect control flow from caller to callee
            match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(func:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(callee:UpstreamNode {type:"CFGEntryNode"}) // Get all function declarations in the testcase
            where id(tc)=%d
            with tc,func,callee
            match (tc)<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(entry:UpstreamNode {type:"CFGEntryNode"})
            with func,callee,entry
            match shortestPath((entry)-[:CONTROLS*]->(caller:DownstreamNode))
            where caller.type in ["ExpressionStatement","Condition"]
            with func,callee,caller
            match shortestPath((caller)-[:IS_AST_PARENT*]->(cexpr:GenericNode {type:"CallExpression"}))
            where not (cexpr)<-[:IS_AST_PARENT*]-(:GenericNode {type:"CallExpression"}) // Dodge nested function calls
            with func,callee,caller,cexpr
            match (cexpr)-[r:IS_AST_PARENT]->(:GenericNode {type:"Callee",code:func.code}) // Get all function calls within the testcase
            with callee,caller
            merge (caller)-[intercall:FLOWS_TO]->(callee) // Connect the callee's entry point (head) to where it is called
            with callee,caller,intercall
            match shortestPath((callee)-[:CONTROLS*]->(last:DownstreamNode))
            with callee,caller,intercall,last
            match (last)-[:FLOWS_TO|DOM]->(exit:DownstreamNode {type:"CFGExitNode"}) // Find the callee's exit point
            with caller,intercall,exit
            match (caller)-[nextrel:FLOWS_TO]->(next:DownstreamNode) // Find the caller's next node in its control flow graph
            where next.type<>"CFGEntryNode"
            with DISTINCT caller,intercall,exit,nextrel,next
            merge (exit)-[interreturn:FLOWS_TO {callerid:id(intercall)}]->(next) // Connect the callee's tail to the caller's next node
            merge (caller)-[:SHORTCUT]->(next)
            delete nextrel // Delete the edge between the function call and its next step, so that the control flow graph now goes through the callee and returns to the callers next step
        """, """
            // Handle use of *var
            match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(entry:UpstreamNode {type:"CFGEntryNode"})
            where id(tc)=%d
            with distinct entry
            match shortestPath((entry)-[:CONTROLS*]->(n:DownstreamNode))
            with distinct n
            match shortestPath((n)-[:DEF|USE]->(sym0:GenericNode {type:"Symbol"}))
            with distinct sym0
            match (sym0)<-[r0:DEF]-(expr:DownstreamNode)-[r1:USE]->(sym1:GenericNode {type:"Symbol"})
            where expr.type in ["ExpressionStatement","Condition"] and sym0.code="* "+sym1.code
            merge (expr)-[r2:DEF]->(sym1)
        """, """
            // Handle use of &var
            match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(entry:UpstreamNode {type:"CFGEntryNode"})
            where id(tc)=%d
            with distinct entry
            match shortestPath((entry)-[:CONTROLS*]->(n:DownstreamNode))
            with distinct n
            match shortestPath((n)-[:IS_AST_PARENT*]->(uop:GenericNode {type:"UnaryOperator",code:"&"}))
            with distinct uop
            match (uop)<-[:IS_AST_PARENT]-(uexpr:GenericNode {type:"UnaryOperationExpression"})-[:IS_AST_PARENT]->(idf:GenericNode {type:"Identifier"})
            with uexpr,idf
            match shortestPath((uexpr)<-[:IS_AST_PARENT*]-(expr:DownstreamNode {type:"ExpressionStatement"}))
            with expr,idf
            match (expr)-[:USE]->(adr_sym:GenericNode {type:"Symbol",code:"& "+idf.code})
            with expr,adr_sym,idf
            match shortestPath((expr)<-[:FLOWS_TO*]-(def:DownstreamNode))
            where expr<>def and def.type in ["IdentifierDeclStatement","Parameter"]
            match (def)-[:DEF]->(def_sym:GenericNode {type:"Symbol",code:idf.code})
            merge (def)-[rdef:DEF {var:idf.code}]->(adr_sym)
            merge (def)-[dflr:REACHES {var:adr_sym.code}]->(expr)
            with distinct expr
            match (ptr_sym:GenericNode {type:"Symbol"})<-[:DEF]-(expr)
            match shortestPath((expr)-[:FLOWS_TO*]-(usr:DownstreamNode {type:"ExpressionStatement"}))
            where expr<>usr
            match (usr)-[:USE]->(star_sym:GenericNode {type:"Symbol",code:"* "+ptr_sym.code})
            merge (expr)-[sdef:DEF {var:ptr_sym.code}]->(star_sym)
        """, """
            // Add missing dataflow
            match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(entry:UpstreamNode {type:"CFGEntryNode"})
            where id(tc)=%d
            with distinct entry
            match shortestPath((entry)-[:CONTROLS*]->(n:DownstreamNode))
            with distinct n
            match (n)-[:DEF|USE]->(sym:GenericNode {type:"Symbol"})
            with distinct sym
            match (sym)<-[use:USE]-(clr:GenericNode)
            match (sym)<-[def:DEF]-(src:DownstreamNode)
            match shortestPath((clr)<-[cf:FLOWS_TO*]-(src))
            where clr<>src
            merge (src)-[ndf:REACHES {var:sym.code}]->(clr)
        """, """
            // Connect arguments to dataflow on the caller side
            match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(entry:UpstreamNode {type:"CFGEntryNode"})
            where id(tc)=%d
            with distinct entry
            match shortestPath((entry)-[:CONTROLS*]->(caller:DownstreamNode))
            where caller.type in ["ExpressionStatement","Condition"]
            with distinct caller
            match shortestPath((caller)-[:IS_AST_PARENT*]->(cexpr:GenericNode {type:"CallExpression"}))
            where not (cexpr)<-[:IS_AST_PARENT*]-(:GenericNode {type:"CallExpression"})
            with caller,cexpr
            match (caller)-[calrel:FLOWS_TO]->(callee:UpstreamNode {type:"CFGEntryNode"})
            with caller,cexpr,calrel,callee
            match (cexpr)-[:IS_AST_PARENT]->(arglst:GenericNode {type:"ArgumentList"})-[:IS_AST_PARENT]->(arg:GenericNode {type:"Argument"})-[:USE]->(sym:GenericNode {type:"Symbol"})<-[:USE]-(caller)<-[df0:REACHES]-(src:DownstreamNode)-[:DEF]->(sym)
            merge (src)-[df1:REACHES {var:sym.code}]->(arg)
            delete df0
            with caller,calrel,callee,arg
            match (callee)-[:FLOWS_TO|CONTROLS]->(param:DownstreamNode {type:"Parameter",childNum:arg.childNum})-[:DEF]->(sym:GenericNode {type:"Symbol"})
            with caller,calrel,callee,arg,param,sym
            merge (arg)-[df2:REACHES {var:sym.code}]->(param)
            with caller,calrel,callee
            match shortestPath((callee)-[:CONTROLS*]->(ret:DownstreamNode {type:"ReturnStatement"}))
            where callee<>ret
            merge (ret)-[df3:REACHES {callerid:id(calrel)}]->(caller)
        """,
    ]
    interproc_cmds_post = [
        """
            // Label data sinks
            MATCH (s:GenericNode)-[:REACHES]->(d:GenericNode)
            WHERE s<>d AND NOT (d)-[:REACHES]->(:GenericNode)
            SET d:DataSinkNode
        """,
    ]

