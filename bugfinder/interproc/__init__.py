"""
"""
from multiprocessing import Pool
from py2neo import Graph
from http.client import RemoteDisconnected
from urllib3.exceptions import ProtocolError
from time import sleep
from sys import stderr

from bugfinder.neo4j import Neo4J3Processing
from bugfinder.utils.progressbar import SlowBar, MultiBar
from bugfinder.settings import ROOT_DIR, LOGGER, POOL_SIZE

# TODO
# Check if Joern includes global variables in data flow
# Handle nested function calls in the control+data flow graph


def interproc_worker(bar, cmds, tcid, q, port):
    db = Graph(
        scheme="http",
        host="0.0.0.0",
        port=port,
    )
    bar.subscribe(max=len(cmds))
    for idx in range(q, len(cmds)):
        cmd = cmds[idx]
        for tries in range(4):
            try:
                sleep(tries ** 2)
                db.run(cmd % tcid)
                LOGGER.debug("Testcase %d Query %d succeeded." % (tcid, idx))
                break
            except (RemoteDisconnected, ProtocolError):
                continue
            except (KeyboardInterrupt, Exception) as e:
                LOGGER.debug("Testcase %d Query %d failed: %s" % (tcid, idx, str(e)))
                bar.next(n=len(cmds) - idx)
                bar.unsubscribe()
                return (tcid, idx, str(e))
        else:
            LOGGER.debug("Testcase %d Query %d failed." % (tcid, idx))
            bar.next(n=len(cmds) - idx)
            bar.unsubscribe()
            return (tcid, idx, "All tries exhausted.")
        bar.next()
    bar.unsubscribe()
    return None


class InterprocProcessing(Neo4J3Processing):

    interproc_cmds_pre = []
    interproc_cmds_tc = []
    interproc_cmds_post = []

    def assign_ports(self):
        assigned_ports = None
        if self.container_ports is not None:
            self.machine_ports = self.container_ports
            assigned_ports = dict(zip(self.container_ports, self.machine_ports))
        return assigned_ports

    def configure_command(self, command):
        self.log_input = command["log_input"]
        self.log_output = command["log_output"]
        self.timeout = command["timeout"]

    def configure_container(self):
        super().configure_container()
        self.container_name = "interproc"
        self.environment["NEO4J_dbms_transaction_timeout"] = self.timeout

    def send_commands(self):
        self.fix_data_folder_rights()
        super().send_commands()

        if self.interproc_cmds_pre:
            LOGGER.debug("Preprocessing...")
            bar = SlowBar("Preprocessing")
            for cmd in self.interproc_cmds_pre:
                self.neo4j_db.run(cmd)
                bar.next()
            bar.finish()

        if self.interproc_cmds_tc:
            if self.log_input:
                # Read failed queries from a log file if specified
                LOGGER.info("Loading failed testcases...")
                with open(self.log_input, "r") as inlog:
                    failed = list(inlog)
                tc_list = [l.split(",")[:2] for l in failed]
            else:
                # Read test cases from the database otherwise
                LOGGER.info("Retrieving testcases...")
                tc_list = [
                    [tc["id"], 0]
                    for tc in self.neo4j_db.run(
                        """match (tc:GenericNode {type:"Testcase"}) return distinct id(tc) as id, tc.name as name"""
                    ).data()
                ]
            LOGGER.debug("%d testcases retrieved." % len(tc_list))

            port = self.machine_ports[self.container_ports.index("7474")]

            LOGGER.debug("Processing...")
            bar = MultiBar("Processing", max=1)
            pool = Pool(POOL_SIZE)
            status = pool.starmap_async(
                interproc_worker,
                [
                    [bar, self.interproc_cmds_tc, int(tc), int(q), port]
                    for tc, q in tc_list
                ],
                chunksize=1,
            )
            pool.close()

            # Display progress until we are done
            bar.next()
            try:
                bar.refresh()
            except KeyboardInterrupt:
                pass
            bar.finish()
            pool.join()

            # Write failed queries to a log file if specified
            if self.log_output:
                failed = filter(None, status.get())
                with open(self.log_output, "a") as outlog:
                    for query in failed:
                        outlog.write(
                            "%d,%d,%s\n"
                            % (query[0], query[1], query[2].replace("\n", " "))
                        )

        if self.interproc_cmds_post:
            LOGGER.debug("Postprocessing...")
            bar = SlowBar("Postprocessing")
            for cmd in self.interproc_cmds_post:
                self.neo4j_db.run(cmd)
                bar.next()
            bar.finish()

        LOGGER.info("All done.")


class InterprocMerger(InterprocProcessing):

    interproc_cmds_pre = [
        """
            match (cexpr:GenericNode {type:"CallExpression"})-[:IS_AST_PARENT]->(func:GenericNode {type:"Callee"})
            where func.code in ["memcpy","memmove","gets","fgets","fgetws","sprintf","swprintf","strcat","wcscat","strncat","wcsncat","strcpy","wcscpy","strncpy","wcsncpy","wcstombs"]
            with distinct cexpr
            match (cexpr)-[:IS_AST_PARENT]->(:GenericNode {type:"ArgumentList"})-[:IS_AST_PARENT]->(arg:GenericNode {type:"Argument",childNum:"0"})
            match (arg)-[:USE]->(sym:GenericNode {type:"Symbol"})<-[:USE]-(expr:DownstreamNode)
            where expr.type in ["ExpressionStatement","IdentifierDeclStatement","ForInit","Condition"]
              and (expr)-[:IS_AST_PARENT*]->(cexpr)
            merge (expr)-[r:DEF]->(sym)
        """,
        """
            match (cexpr:GenericNode {type:"CallExpression"})-[:IS_AST_PARENT]->(func:GenericNode {type:"Callee"})
            where func.code in ["scanf","wscanf","fscanf","fwscanf","sscanf","swscanf"]
            with distinct cexpr, case when func.code in ["scanf","wscanf"] then 1 else 2 end as offset
            match (cexpr)-[:IS_AST_PARENT]->(:GenericNode {type:"ArgumentList"})-[:IS_AST_PARENT]->(arg:GenericNode {type:"Argument"})
            where arg.childNum > offset
            match (arg)-[:USE]->(sym:GenericNode {type:"Symbol"})<-[:USE]-(expr:DownstreamNode)
            where expr.type in ["ExpressionStatement","IdentifierDeclStatement","ForInit","Condition"]
              and (expr)-[:IS_AST_PARENT*]->(cexpr)
            merge (expr)-[r:DEF]->(sym)
        """,
    ]

    interproc_cmds_tc = [
        """
            // Connect control flow from caller to callee
            match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(func:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(callee:UpstreamNode {type:"CFGEntryNode"}) // Get all function declarations in the testcase
            where id(tc)=%d
            with tc,func,callee
            match (tc)<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(entry:UpstreamNode {type:"CFGEntryNode"})
            with func,callee,entry
            match (entry)-[:CONTROLS*]->(caller:DownstreamNode)
            where caller.type in ["ExpressionStatement","Condition"]
            with func,callee,caller
            match (caller)-[:IS_AST_PARENT*]->(cexpr:GenericNode {type:"CallExpression"})
            where not (cexpr)<-[:IS_AST_PARENT*]-(:GenericNode {type:"CallExpression"}) // Dodge nested function calls
            with func,callee,caller,cexpr
            match (cexpr)-[r:IS_AST_PARENT]->(:GenericNode {type:"Callee",code:func.code}) // Get all function calls within the testcase
            with callee,caller
            merge (caller)-[intercall:FLOWS_TO]->(callee) // Connect the callee's entry point (head) to where it is called
            with callee,caller,intercall
            match (callee)-[:CONTROLS*]->(last:DownstreamNode)
            with callee,caller,intercall,last
            match (last)-[:FLOWS_TO|DOM]->(exit:DownstreamNode {type:"CFGExitNode"}) // Find the callee's exit point
            with caller,intercall,exit
            match (caller)-[nextrel:FLOWS_TO]->(next:DownstreamNode) // Find the caller's next node in its control flow graph
            where next.type<>"CFGEntryNode"
            with DISTINCT caller,intercall,exit,nextrel,next
            merge (exit)-[interreturn:FLOWS_TO {callerid:id(intercall)}]->(next) // Connect the callee's tail to the caller's next node
            merge (caller)-[:SHORTCUT]->(next)
            delete nextrel // Delete the edge between the function call and its next step, so that the control flow graph now goes through the callee and returns to the callers next step
        """,
        """
            // Handle global variables by first finding their initialization, then creating dataflow to nodes that use them.
            match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function",code:"main"})-[:IS_FUNCTION_OF_CFG]->(main:UpstreamNode {type:"CFGEntryNode"})
            where id(tc)=%d
            with distinct main
            match (main)-[:FLOWS_TO*]->(n1:GenericNode)-[:DEF]->(sym1:GenericNode {type:"Symbol"}) // Find the initialization of the global variable
            where not left(sym1.code,2)="* "
              and not sym1.code contains " . "
              and not sym1.code=toupper(sym1.code)
              and not sym1.code in ["NULL","L","stdin","& wsaData"]
              and not (sym1)<-[:DEF]-(:GenericNode {type:"IdentifierDeclStatement"})
              and not (sym1)<-[:DEF]-(:GenericNode {type:"Parameter"})
              and not (sym1)<-[:USE]-(:GenericNode)-[:IS_AST_PARENT*]->(:GenericNode {type:"Callee",code:sym1.code})
            with n1, sym1
            match p=(n1)-[:FLOWS_TO*]->(n2:GenericNode)-[:USE]->(sym2:GenericNode {type:"Symbol",code:sym1.code}) // Find the next node n2 that uses the global variable
            where n1<>n2 and none(n in nodes(p)[1..-1] where (n)-[:DEF]->(:GenericNode {type:"Symbol",code:sym1.code})) // Ensure the value has not been modified since n1
            merge (n1)-[:REACHES {var:sym1.code}]->(n2)
        """,
        """
            // Handle use of *var
            match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(entry:UpstreamNode {type:"CFGEntryNode"})
            where id(tc)=%d
            with distinct entry
            match (entry)-[:CONTROLS*]->(n:DownstreamNode)
            with distinct n
            match (n)-[:DEF|USE]->(sym0:GenericNode {type:"Symbol"})
            with distinct sym0
            match (sym0)<-[r0:DEF]-(expr:DownstreamNode)-[r1:USE]->(sym1:GenericNode {type:"Symbol"})
            where expr.type in ["ExpressionStatement","Condition"] and sym0.code="* "+sym1.code
            merge (expr)-[r2:DEF]->(sym1)
        """,
        """
            // Handle use of &var
            match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(entry:UpstreamNode {type:"CFGEntryNode"})
            where id(tc)=%d
            with distinct entry
            match (entry)-[:CONTROLS*]->(n:DownstreamNode)
            with distinct n
            match (n)-[:IS_AST_PARENT*]->(uop:GenericNode {type:"UnaryOperator",code:"&"})
            with distinct uop
            match (uop)<-[:IS_AST_PARENT]-(uexpr:GenericNode {type:"UnaryOperationExpression"})-[:IS_AST_PARENT]->(idf:GenericNode {type:"Identifier"})
            with uexpr,idf
            match (uexpr)<-[:IS_AST_PARENT*]-(expr:DownstreamNode)
            where expr.type in ["ExpressionStatement","IdentifierDeclStatement","ForInit","Condition"]
            with expr,idf
            match (expr)-[:USE]->(adr_sym:GenericNode {type:"Symbol",code:"& "+idf.code})
            with expr,adr_sym,idf
            match (expr)<-[:FLOWS_TO*]-(def:DownstreamNode)
            where expr<>def and def.type in ["IdentifierDeclStatement","Parameter"]
            match (def)-[:DEF]->(def_sym:GenericNode {type:"Symbol",code:idf.code})
            merge (def)-[rdef:DEF {var:idf.code}]->(adr_sym)
            merge (def)-[dflr:REACHES {var:adr_sym.code}]->(expr)
            with distinct expr
            match (ptr_sym:GenericNode {type:"Symbol"})<-[:DEF]-(expr)
            match (expr)-[:FLOWS_TO*]-(usr:DownstreamNode {type:"ExpressionStatement"})
            where expr<>usr
            match (usr)-[:USE]->(star_sym:GenericNode {type:"Symbol",code:"* "+ptr_sym.code})
            merge (expr)-[sdef:DEF {var:ptr_sym.code}]->(star_sym)
        """,
        """
            // Add missing dataflow
            match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(entry:UpstreamNode {type:"CFGEntryNode"})
            where id(tc)=%d
            with distinct entry
            match (entry)-[:CONTROLS*]->(n:DownstreamNode)
            with distinct n
            match (n)-[:DEF|USE]->(sym:GenericNode {type:"Symbol"})
            with distinct sym
            match (sym)<-[use:USE]-(clr:GenericNode)
            match (sym)<-[def:DEF]-(src:DownstreamNode)
            match (clr)<-[cf:FLOWS_TO*]-(src)
            where clr<>src
            merge (src)-[ndf:REACHES {var:sym.code}]->(clr)
        """,
        """
            // Connect arguments to dataflow on the caller side
            match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(entry:UpstreamNode {type:"CFGEntryNode"})
            where id(tc)=%d
            with distinct entry
            match (entry)-[:CONTROLS*]->(caller:DownstreamNode)
            where caller.type in ["ExpressionStatement","Condition"]
            with distinct caller
            match (caller)-[:IS_AST_PARENT*]->(cexpr:GenericNode {type:"CallExpression"})
            where not (cexpr)<-[:IS_AST_PARENT*]-(:GenericNode {type:"CallExpression"})
            with caller,cexpr
            match (caller)-[calrel:FLOWS_TO]->(callee:UpstreamNode {type:"CFGEntryNode"})
            with caller,cexpr,calrel,callee
            match (cexpr)-[:IS_AST_PARENT]->(arglst:GenericNode {type:"ArgumentList"})-[:IS_AST_PARENT]->(arg:GenericNode {type:"Argument"})-[:USE]->(sym:GenericNode {type:"Symbol"})<-[:USE]-(caller)<-[df0:REACHES]-(src:DownstreamNode)-[:DEF]->(sym)
            delete df0
            with caller,calrel,callee,arg,src
            match (callee)-[:FLOWS_TO|CONTROLS]->(param:DownstreamNode {type:"Parameter",childNum:arg.childNum})-[:DEF]->(sym:GenericNode {type:"Symbol"})
            with caller,calrel,callee,src,param,sym
            merge (src)-[:REACHES {var:sym.code}]->(param)
            with caller,calrel,callee,param,sym
            match (param)-[rpr:REACHES]->()
            set rpr.src=sym.code
            with caller,calrel,callee
            match (callee)-[:CONTROLS*]->(ret:DownstreamNode {type:"ReturnStatement"})
            where callee<>ret
            merge (ret)-[:REACHES {callerid:id(calrel)}]->(caller)
        """,
        """
            // Remove redundant dataflow/shortcuts
            match (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(:GenericNode {type:"Function",code:"main"})-[:IS_FUNCTION_OF_CFG]->(main:UpstreamNode {type:"CFGEntryNode"})
            where id(tc)=%d
            with distinct main
            match (main)-[:FLOWS_TO*]->(src:GenericNode) // Find sources (start of data flow on the control flow path)
            where (src)-[:REACHES]->() and not (src)<-[:REACHES]-()
            with distinct src
            match pm1=(src)-[r1:REACHES*]->(dst:GenericNode) // Find destinations (end of dataflow)
            where not (dst)-[:REACHES]->()
              and all(idx in range(1,size(r1)-1) where r1[idx-1].var in [r1[idx].var, r1[idx].src]) // Ensure we follow the same variable
            with distinct src, dst, r1[-1].var as var, pm1 order by length(pm1) // Order paths my length
            with distinct src, dst, var, collect(pm1) as paths // Group path by source, destination and variable
            unwind range(0, size(paths)-2) as idx
            with src, dst, paths[idx] as shorter, paths[idx+1] as longer
            where all(n in nodes(shorter) where n in nodes(longer)) // Check if the shorter path is a subset of the longer path
            with src, dst, filter(r in relationships(shorter) where not r in relationships(longer)) as xr // Retrieve extraneous relationship / shortcuts in the shorter path 
            foreach(r in xr | delete r) // Delete the shortcuts
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
