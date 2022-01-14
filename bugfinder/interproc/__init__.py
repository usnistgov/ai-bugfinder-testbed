"""
"""
from multiprocessing import Pool

from http.client import RemoteDisconnected
from py2neo import Graph
from time import sleep
from urllib3.exceptions import ProtocolError

from bugfinder.neo4j import Neo4J3Processing
from bugfinder.settings import LOGGER, POOL_SIZE
from bugfinder.utils.progressbar import SlowBar, MultiBar


# TODO
# Check if Joern includes global variables in data flow
# Handle nested function calls in the control+data flow graph


def interproc_worker(progress_bar, cmds, tcid, q, port):
    db = Graph(
        scheme="http",
        host="0.0.0.0",
        port=port,
    )
    progress_bar.subscribe(len(cmds))
    for idx in range(q, len(cmds)):
        cmd = cmds[idx]
        for tries in range(4):
            try:
                sleep(tries ** 2)
                db.run(cmd % tcid)
                LOGGER.debug("Testcase %d Query %d succeeded.", tcid, idx)
                break
            except (RemoteDisconnected, ProtocolError):
                continue
            except (KeyboardInterrupt, Exception) as exc:
                LOGGER.debug("Testcase %d Query %d failed: %s", tcid, idx, str(exc))
                progress_bar.next(n=len(cmds) - idx)
                progress_bar.unsubscribe()
                return tcid, idx, str(exc)
        else:
            LOGGER.debug("Testcase %d Query %d failed.", tcid, idx)
            progress_bar.next(n=len(cmds) - idx)
            progress_bar.unsubscribe()
            return tcid, idx, "All tries exhausted."
        progress_bar.next()
    progress_bar.unsubscribe()
    return None


class InterprocProcessing(Neo4J3Processing):
    log_input = None
    log_output = None
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

    def configure_container_with_dict(self, container_config):
        self.configure_container()
        self.environment["NEO4J_dbms_transaction_timeout"] = container_config["timeout"]

    def configure_container(self):
        super().configure_container()
        self.container_name = "interproc"

    def send_commands(self):
        self.fix_data_folder_rights()
        super().send_commands()

        if self.interproc_cmds_pre:
            LOGGER.debug("Preprocessing...")
            progress_bar = SlowBar("Preprocessing", max=len(self.interproc_cmds_pre))
            for cmd in self.interproc_cmds_pre:
                self.neo4j_db.run(cmd)
                progress_bar.next()
            progress_bar.finish()

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
                        """
                        MATCH (tc:GenericNode {type:"Testcase"})
                        return distinct id(tc) as id, tc.name as name
                        """
                    ).data()
                ]
            LOGGER.debug("%d testcases retrieved.", len(tc_list))

            port = self.machine_ports[self.container_ports.index("7474")]

            LOGGER.debug("Processing...")
            progress_bar = MultiBar("Processing", max=1)
            pool = Pool(POOL_SIZE)
            status = pool.starmap_async(
                interproc_worker,
                [
                    [progress_bar, self.interproc_cmds_tc, int(tc), int(q), port]
                    for tc, q in tc_list
                ],
                chunksize=1,
            )
            pool.close()

            # Display progress until we are done
            progress_bar.next()
            try:
                progress_bar.refresh()
            except KeyboardInterrupt:
                pass
            progress_bar.finish()
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
            progress_bar = SlowBar("Postprocessing", max=len(self.interproc_cmds_post))
            for cmd in self.interproc_cmds_post:
                self.neo4j_db.run(cmd)
                progress_bar.next()
            progress_bar.finish()

        LOGGER.info("All done.")


class InterprocMerger(InterprocProcessing):

    interproc_cmds_pre = [
        # Add a DEF relationship so string functions
        # "define" their desination symbol
        """
            MATCH (cexpr:GenericNode {type:"CallExpression"})-[
                :IS_AST_PARENT
            ]->(func:GenericNode {type:"Callee"})
            WHERE func.code IN [
                "memcpy","memmove","gets","fgets","fgetws","sprintf",
                "swprintf","strcat","wcscat","strncat","wcsncat","strcpy",
                "wcscpy","strncpy","wcsncpy","wcstombs"
            ]
            WITH DISTINCT cexpr
            MATCH (cexpr)-[:IS_AST_PARENT]->(
                :GenericNode {type:"ArgumentList"}
            )-[:IS_AST_PARENT]->(
                arg:GenericNode {type:"Argument",childNum:"0"}
            )
            MATCH (arg)-[:USE]->(sym:GenericNode {type:"Symbol"})<-[:USE]-(
                expr:DownstreamNode
            )
            WHERE expr.type IN [
                "ExpressionStatement","IdentifierDeclStatement","ForInit",
                "Condition"
            ]
            AND (expr)-[:IS_AST_PARENT*]->(cexpr)
            MERGE (expr)-[r:DEF]->(sym)
        """,
        # Add a DEF relationship so "scan" functions
        # "define" their desination symbol
        """
            MATCH (cexpr:GenericNode {type:"CallExpression"})-[
                :IS_AST_PARENT
            ]->(func:GenericNode {type:"Callee"})
            WHERE func.code IN [
                "scanf","wscanf","fscanf","fwscanf","sscanf","swscanf"
            ]
            WITH DISTINCT cexpr, case when func.code IN [
                "scanf","wscanf"
            ] then 1 else 2 end AS offset
            MATCH (cexpr)-[:IS_AST_PARENT]->(
                :GenericNode {type:"ArgumentList"}
            )-[:IS_AST_PARENT]->(arg:GenericNode {type:"Argument"})
            WHERE arg.childNum > offset
            MATCH (arg)-[:USE]->(sym:GenericNode {type:"Symbol"})<-[
                :USE
            ]-(expr:DownstreamNode)
            WHERE expr.type IN [
                "ExpressionStatement","IdentifierDeclStatement","ForInit",
                "Condition"
            ]
            AND (expr)-[:IS_AST_PARENT*]->(cexpr)
            MERGE (expr)-[r:DEF]->(sym)
        """,
    ]

    interproc_cmds_tc = [
        # Connect control flow from caller to callee
        """
            MATCH (tc:GenericNode {type:"Testcase"})<-[
                :IS_FILE_OF
            ]-(:GenericNode {type:"File"})-[:IS_FILE_OF]->(
                func:GenericNode {type:"Function"}
            )-[:IS_FUNCTION_OF_CFG]->(
                callee:UpstreamNode {type:"CFGEntryNode"}
            ) // Get all function declarations IN the testcase
            WHERE ID(tc)=%d
            WITH tc,func,callee
            MATCH (tc)<-[:IS_FILE_OF]-(:GenericNode {type:"File"})-[
                :IS_FILE_OF
            ]->(:GenericNode {type:"Function"})-[
                :IS_FUNCTION_OF_CFG
            ]->(entry:UpstreamNode {type:"CFGEntryNode"})
            WITH func,callee,entry
            MATCH (entry)-[:CONTROLS*]->(caller:DownstreamNode)
            WHERE caller.type IN ["ExpressionStatement","Condition"]
            WITH func,callee,caller
            MATCH (caller)-[:IS_AST_PARENT*]->(cexpr:GenericNode {type:"CallExpression"})
            WHERE NOT (cexpr)<-[:IS_AST_PARENT*]-(
                :GenericNode {type:"CallExpression"}
            ) // Dodge nested function calls
            WITH func,callee,caller,cexpr
            MATCH (cexpr)-[r:IS_AST_PARENT]->(
                :GenericNode {type:"Callee",code:func.code}
            ) // Get all function calls within the testcase
            WITH callee,caller
            MERGE (caller)-[
                intercall:FLOWS_TO
            ]->(callee) // Connect the callee's entry point (head) to WHERE it is called
            WITH callee,caller,intercall
            MATCH (callee)-[:CONTROLS*]->(last:DownstreamNode)
            WITH callee,caller,intercall,last
            MATCH (last)-[
                :FLOWS_TO|DOM
            ]->(exit:DownstreamNode {type:"CFGExitNode"}) // Find the callee's exit point
            WITH caller,intercall,exit
            MATCH (caller)-[
                nextrel:FLOWS_TO
            ]->(
                next:DownstreamNode
            ) // Find the caller's next node IN its control flow graph
            WHERE next.type<>"CFGEntryNode"
            WITH DISTINCT caller,intercall,exit,nextrel,next
            MERGE (exit)-[
                interreturn:FLOWS_TO {callerid:ID(intercall)}
            ]->(next) // Connect the callee's tail to the caller's next node
            MERGE (caller)-[:SHORTCUT]->(next)
            // Delete the edge between the function call AND its next step,
            // so that the control flow graph now goes through the callee AND
            // returns to the callers next step
            DELETE nextrel
        """,
        # Handle global variables by first finding their initialization,
        # then creating dataflow to nodes that use them.
        """
            MATCH (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(
                :GenericNode {type:"File"}
            )-[:IS_FILE_OF]->(
                :GenericNode {type:"Function",code:"main"}
            )-[:IS_FUNCTION_OF_CFG]->(main:UpstreamNode {type:"CFGEntryNode"})
            WHERE ID(tc)=%d
            WITH DISTINCT main
            MATCH (main)-[:FLOWS_TO*]->(
                n1:GenericNode
            )-[:DEF]->(
                sym1:GenericNode {type:"Symbol"}
            ) // Find the initialization of the global variable
            WHERE NOT LEFT(sym1.code,2)="* "
                AND NOT sym1.code contains " . "
                AND NOT sym1.code=TOUPPER(sym1.code)
                AND NOT sym1.code IN ["NULL","L","stdin","& wsaData"]
                AND NOT (sym1)<-[:DEF]-(:GenericNode {type:"IdentifierDeclStatement"})
                AND NOT (sym1)<-[:DEF]-(:GenericNode {type:"Parameter"})
                AND NOT (sym1)<-[:USE]-(:GenericNode)-[
                    :IS_AST_PARENT*
                ]->(:GenericNode {type:"Callee",code:sym1.code})
            WITH n1, sym1
            MATCH p=(n1)-[:FLOWS_TO*]->(n2:GenericNode)-[:USE]->(
                sym2:GenericNode {type:"Symbol",code:sym1.code}
            ) // Find the next node n2 that uses the global variable
            WHERE n1<>n2 AND NONE(n IN NODES(p)[1..-1]
            WHERE (n)-[:DEF]->(
                :GenericNode {type:"Symbol",code:sym1.code})
            ) // Ensure the value has NOT been modified since n1
            MERGE (n1)-[:REACHES {var:sym1.code}]->(n2)
        """,
        # Handle use of *var
        """
            MATCH (tc:GenericNode {type:"Testcase"})<-[:IS_FILE_OF]-(
                :GenericNode {type:"File"}
            )-[:IS_FILE_OF]->(
                :GenericNode {type:"Function"}
            )-[:IS_FUNCTION_OF_CFG]->(entry:UpstreamNode {type:"CFGEntryNode"})
            WHERE ID(tc)=%d
            WITH DISTINCT entry
            MATCH (entry)-[:CONTROLS*]->(n:DownstreamNode)
            WITH DISTINCT n
            MATCH (n)-[:DEF|USE]->(sym0:GenericNode {type:"Symbol"})
            WITH DISTINCT sym0
            MATCH (sym0)<-[r0:DEF]-(expr:DownstreamNode)-[r1:USE]->(
                sym1:GenericNode {type:"Symbol"}
            )
            WHERE expr.type IN ["ExpressionStatement","Condition"]
                AND sym0.code="* "+sym1.code
            MERGE (expr)-[r2:DEF]->(sym1)
        """,
        # Handle use of &var
        """
            MATCH (tc:GenericNode {type:"Testcase"})<-[
                :IS_FILE_OF
            ]-(:GenericNode {type:"File"})-[
                :IS_FILE_OF
            ]->(:GenericNode {type:"Function"})-[
                :IS_FUNCTION_OF_CFG
            ]->(entry:UpstreamNode {type:"CFGEntryNode"})
            WHERE ID(tc)=%d
            WITH DISTINCT entry
            MATCH (entry)-[:CONTROLS*]->(n:DownstreamNode)
            WITH DISTINCT n
            MATCH (n)-[
                :IS_AST_PARENT*
            ]->(uop:GenericNode {type:"UnaryOperator",code:"&"})
            WITH DISTINCT uop
            MATCH (uop)<-[:IS_AST_PARENT]-(
                uexpr:GenericNode {type:"UnaryOperationExpression"}
            )-[:IS_AST_PARENT]->(idf:GenericNode {type:"Identifier"})
            WITH uexpr,idf
            MATCH (uexpr)<-[:IS_AST_PARENT*]-(expr:DownstreamNode)
            WHERE expr.type IN [
                "ExpressionStatement","IdentifierDeclStatement","ForInit",
                "Condition"
            ]
            WITH expr,idf
            MATCH (expr)-[:USE]->(
                adr_sym:GenericNode {type:"Symbol",code:"& "+idf.code}
            )
            WITH expr,adr_sym,idf
            MATCH (expr)<-[:FLOWS_TO*]-(def:DownstreamNode)
            WHERE expr<>def AND def.type IN ["IdentifierDeclStatement","Parameter"]
            MATCH (def)-[:DEF]->(def_sym:GenericNode {type:"Symbol",code:idf.code})
            MERGE (def)-[rdef:DEF {var:idf.code}]->(adr_sym)
            MERGE (def)-[dflr:REACHES {var:adr_sym.code}]->(expr)
            WITH DISTINCT expr
            MATCH (ptr_sym:GenericNode {type:"Symbol"})<-[:DEF]-(expr)
            MATCH (expr)-[:FLOWS_TO*]-(usr:DownstreamNode {type:"ExpressionStatement"})
            WHERE expr<>usr
            MATCH (usr)-[:USE]->(
                star_sym:GenericNode {type:"Symbol",code:"* "+ptr_sym.code}
            )
            MERGE (expr)-[sdef:DEF {var:ptr_sym.code}]->(star_sym)
        """,
        # Add missing dataflow
        """
            MATCH (tc:GenericNode {type:"Testcase"})<-[
                :IS_FILE_OF
            ]-(:GenericNode {type:"File"})-[
                :IS_FILE_OF
            ]->(:GenericNode {type:"Function"})-[
                :IS_FUNCTION_OF_CFG
            ]->(entry:UpstreamNode {type:"CFGEntryNode"})
            WHERE ID(tc)=%d
            WITH DISTINCT entry
            MATCH (entry)-[:CONTROLS*]->(n:DownstreamNode)
            WITH DISTINCT n
            MATCH (n)-[:DEF|USE]->(sym:GenericNode {type:"Symbol"})
            WITH DISTINCT sym
            MATCH (sym)<-[use:USE]-(clr:GenericNode)
            MATCH (sym)<-[def:DEF]-(src:DownstreamNode)
            MATCH (clr)<-[cf:FLOWS_TO*]-(src)
            WHERE clr<>src
            MERGE (src)-[ndf:REACHES {var:sym.code}]->(clr)
        """,
        # Connect arguments to dataflow on the caller side
        """
            MATCH (tc:GenericNode {type:"Testcase"})<-[
                :IS_FILE_OF
            ]-(:GenericNode {type:"File"})-[
                :IS_FILE_OF
            ]->(:GenericNode {type:"Function"})-[
                :IS_FUNCTION_OF_CFG
            ]->(entry:UpstreamNode {type:"CFGEntryNode"})
            WHERE ID(tc)=%d
            WITH DISTINCT entry
            MATCH (entry)-[:CONTROLS*]->(caller:DownstreamNode)
            WHERE caller.type IN ["ExpressionStatement","Condition"]
            WITH DISTINCT caller
            MATCH (caller)-[:IS_AST_PARENT*]->(cexpr:GenericNode {type:"CallExpression"})
            WHERE NOT (cexpr)<-[:IS_AST_PARENT*]-(:GenericNode {type:"CallExpression"})
            WITH caller,cexpr
            MATCH (caller)-[calrel:FLOWS_TO]->(callee:UpstreamNode {type:"CFGEntryNode"})
            WITH caller,cexpr,calrel,callee
            MATCH (cexpr)-[:IS_AST_PARENT]->(
                arglst:GenericNode {type:"ArgumentList"}
            )-[:IS_AST_PARENT]->(
                arg:GenericNode {type:"Argument"}
            )-[:USE]->(sym:GenericNode {type:"Symbol"})<-[:USE]-(
                caller
            )<-[df0:REACHES]-(src:DownstreamNode)-[:DEF]->(sym)
            DELETE df0
            WITH caller,calrel,callee,arg,src
            MATCH (callee)-[:FLOWS_TO|CONTROLS]->(
                param:DownstreamNode {type:"Parameter",childNum:arg.childNum}
            )-[:DEF]->(sym:GenericNode {type:"Symbol"})
            WITH caller,calrel,callee,src,param,sym
            MERGE (src)-[:REACHES {var:sym.code}]->(param)
            WITH caller,calrel,callee,param,sym
            MATCH (param)-[rpr:REACHES]->()
            set rpr.src=sym.code
            WITH caller,calrel,callee
            MATCH (callee)-[:CONTROLS*]->(ret:DownstreamNode {type:"ReturnStatement"})
            WHERE callee<>ret
            MERGE (ret)-[:REACHES {callerid:ID(calrel)}]->(caller)
        """,
        # Remove redundant dataflow/shortcuts
        """
            MATCH (tc:GenericNode {type:"Testcase"})<-[
                :IS_FILE_OF
            ]-(:GenericNode {type:"File"})-[
                :IS_FILE_OF
            ]->(:GenericNode {type:"Function",code:"main"})-[
                :IS_FUNCTION_OF_CFG
            ]->(main:UpstreamNode {type:"CFGEntryNode"})
            WHERE ID(tc)=%d
            WITH DISTINCT main
            // Find sources (start of data flow on the control flow path)
            MATCH (main)-[:FLOWS_TO*]->(src:GenericNode)
            WHERE (src)-[:REACHES]->() AND NOT (src)<-[:REACHES]-()
            WITH DISTINCT src
            // Find destinations (end of dataflow)
            MATCH pm1=(src)-[r1:REACHES*]->(dst:GenericNode)
            WHERE NOT (dst)-[:REACHES]->()
                AND ALL(idx IN RANGE(1,SIZE(r1)-1)
                // Ensure we follow the same variable
                WHERE r1[idx-1].var IN [r1[idx].var, r1[idx].src])
            WITH DISTINCT src, dst, r1[-1].var AS var, pm1
                ORDER BY LENGTH(pm1) // Order paths by length
            // Group path by source, destination AND variable
            WITH DISTINCT src, dst, var, COLLECT(pm1) AS paths
            UNWIND RANGE(0, SIZE(paths)-2) AS idx
            WITH src, dst, paths[idx] AS shorter, paths[idx+1] AS longer
            // Check if the shorter path is a subset of the longer path
            WHERE ALL(n IN NODES(shorter) WHERE n IN NODES(longer))
            // Retrieve extraneous relationship / shortcuts IN the shorter path
            WITH src, dst, FILTER(
                r IN RELATIONSHIPS(shorter) WHERE NOT r IN RELATIONSHIPS(longer)
            ) AS xr
            // Delete the shortcuts
            FOREACH(r IN xr | DELETE r)
        """,
        # Propagate dataflow sizes
        """
            MATCH (tc:GenericNode {type:"Testcase"})<-[
                :IS_FILE_OF
            ]-(:GenericNode {type:"File"})-[
                :IS_FILE_OF
            ]->(:GenericNode {type:"Function",code:"main"})-[
                :IS_FUNCTION_OF_CFG
            ]->(main:UpstreamNode {type:"CFGEntryNode"})
            WHERE ID(tc)=%d
            WITH DISTINCT main
            MATCH (main)-[:FLOWS_TO*]->(:GenericNode)-[r1:REACHES]->(n:GenericNode)-[r2:REACHES]->()
            WHERE EXISTS(r1.size) AND NOT EXISTS(r2.size)
              AND r1.var IN [r2.var, r2.src]
            SET r2.size=r1.size
            WITH DISTINCT n, r1, r2
            MATCH p=(n)-[r2]->(:GenericNode)-[:REACHES*]->(:GenericNode)
            WHERE ALL(idx IN RANGE(1, SIZE(RELATIONSHIPS(p))-1)
              WHERE NOT EXISTS(RELATIONSHIPS(p)[idx].size)
                AND RELATIONSHIPS(p)[idx-1].var IN [RELATIONSHIPS(p)[idx].var, RELATIONSHIPS(p)[idx].src])
            UNWIND RELATIONSHIPS(p) AS r3
            SET r3.size=r1.size
        """,
    ]

    interproc_cmds_post = [
        # Label data sinks
        """
            MATCH (s:GenericNode)-[:REACHES]->(d:GenericNode)
            WHERE s<>d AND NOT (d)-[:REACHES]->(:GenericNode)
            SET d:DataSinkNode
        """,
    ]
