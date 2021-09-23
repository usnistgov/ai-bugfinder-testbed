"""
"""
from multiprocessing import Pool

import os
from http.client import RemoteDisconnected
from py2neo import Graph
from time import sleep
from urllib3.exceptions import ProtocolError

from bugfinder.neo4j import Neo4J3Processing
from bugfinder.settings import LOGGER, POOL_SIZE
from bugfinder.utils.progressbar import MultiBar


def sinktagging_worker(bar, tc_name, tc_info, port):

    db = Graph(
        scheme="http",
        host="0.0.0.0",
        port=port,
    )

    tcid = tc_info["tcid"]
    if not tc_info["sinks"]:
        LOGGER.warning("No sinks for test case: %s / %d" % (tc_name, tcid))

    sinks_left = len(tc_info["sinks"])
    if sinks_left > 1:
        LOGGER.debug("> Sinks for %s: %d" % (tc_name, sinks_left))
    bar.subscribe(max=sinks_left)
    for sink in tc_info["sinks"]:
        for tries in range(4):
            try:
                sleep(tries ** 2)
                # FIXME Note that the line number for mixed test case can
                # be wrong because the good code was removed from bad test
                # cases. In Juliet, the bad code comes first, so the line
                # number is usually correct, even after removing the good
                # code.
                query = """
                    MATCH (tc:GenericNode {type:"Testcase",label:"bad",name:"%s"})
                    WHERE ID(tc)=%d
                    MATCH (tc)<-[:IS_FILE_OF]-(:GenericNode {type:"File",basename:"%s"})-[:IS_FILE_OF]->(:GenericNode {type:"Function"})-[:IS_FUNCTION_OF_CFG]->(e:UpstreamNode {type:"CFGEntryNode"})
                    WITH DISTINCT e
                    MATCH (e)-[:CONTROLS*]->(n1:GenericNode)
                    WHERE EXISTS(n1.lineno) AND n1.lineno=%d
                    SET n1:BugSinkNode
                    """ % (
                    tc_name,
                    tcid,
                    sink["basename"],
                    sink["lineno"],
                )
                # LOGGER.info(query)
                db.run(query)
                sinks_left -= 1
                break
            except (RemoteDisconnected, ProtocolError):
                continue
            except (KeyboardInterrupt, Exception) as e:
                LOGGER.debug("Testcase %d sink tagging failed: %s" % (tcid, str(e)))
                bar.next(n=sinks_left)
                bar.unsubscribe()
                return tcid, tc_name, str(e)
        else:
            LOGGER.debug("Testcase %d sink tagging failed: timeout" % tcid)
            bar.next(n=sinks_left)
            bar.unsubscribe()
            return tcid, tc_name, "All tries exhausted."
        bar.next()
    bar.unsubscribe()
    return None


class SinkTaggingProcessing(Neo4J3Processing):
    log_input = None
    log_output = None
    sinksfile = None

    def assign_ports(self):
        assigned_ports = None
        if self.container_ports is not None:
            self.machine_ports = self.container_ports
            assigned_ports = dict(zip(self.container_ports, self.machine_ports))
        return assigned_ports

    def configure_command(self, command):
        self.log_input = command["log_input"]
        self.log_output = command["log_output"]
        self.sinksfile = command["sinks"]

    def configure_container_with_dict(self, container_config):
        self.configure_container()
        self.environment["NEO4J_dbms_transaction_timeout"] = container_config["timeout"]

    def configure_container(self):
        super().configure_container()
        self.container_name = "sinktagging"

    def send_commands(self):
        self.fix_data_folder_rights()
        super().send_commands()

        if self.log_input:
            # Read failed queries from a log file if specified
            LOGGER.info("Loading failed testcases...")
            with open(self.log_input, "r") as inlog:
                failed = list(inlog)
            tc_list = {
                ln.split(",")[1]: {
                    "tcid": int(ln.split(",")[0]),
                    "sinks": [],
                }
                for ln in failed
            }
        else:
            # Read test cases from the database otherwise
            LOGGER.info("Retrieving testcases...")
            tc_list = {
                tc["name"]: {
                    "tcid": tc["id"],
                    "sinks": [],
                }
                for tc in self.neo4j_db.run(
                    """
                        MATCH (tc:GenericNode {type:"Testcase",label:"bad"})
                        RETURN DISTINCT ID(tc) AS id, tc.name AS name
                    """
                ).data()
            }
        LOGGER.debug("%d testcases retrieved." % len(tc_list))

        LOGGER.info("Loading sinks...")
        with open(self.sinksfile, "r") as sf:
            sinklist = list(sf)
        for s in sinklist:
            try:
                fields = s.split(",")
                assert len(fields) == 3
                sardid = int(fields[0])
                sardtc = "%06d" % sardid
                basnam = os.path.basename(fields[1])
                lineno = int(fields[2])
                jtcnam = basnam.rsplit(".", 1)[0]
                jtcnam = (
                    jtcnam[:-1]
                    if jtcnam[-1] in ["a", "b", "c", "d", "e", "f"]
                    else jtcnam
                )
                entry = {"basename": basnam, "lineno": lineno, "sardid": sardid}
                if sardtc in tc_list:
                    # This block is for general SARD test cases
                    if entry not in tc_list[sardtc]["sinks"]:
                        tc_list[sardtc]["sinks"].append(entry)
                elif jtcnam in tc_list:
                    # This block is Juliet-specific
                    entry["lineno"] -= 1  # Because we remove line #ifndef OMITBAD
                    if (
                        not tc_list[jtcnam]["sinks"]
                        or tc_list[jtcnam]["sinks"][0]["sardid"] < sardid
                    ):
                        # This is a more recent version of Juliet, use it
                        tc_list[jtcnam]["sinks"] = [entry]
                    elif (
                        tc_list[jtcnam]["sinks"][0]["sardid"] == sardid
                        and entry not in tc_list[jtcnam]["sinks"]
                    ):
                        tc_list[jtcnam]["sinks"].append(entry)
            except Exception as e:
                LOGGER.warning("Problem parsing line '%s': %s" % (s[:-1], str(e)))
                continue
        LOGGER.info("%d sinks loaded." % len(sinklist))

        port = self.machine_ports[self.container_ports.index("7474")]

        LOGGER.debug("Processing...")
        bar = MultiBar("Processing", max=1)
        pool = Pool(POOL_SIZE)
        status = pool.starmap_async(
            sinktagging_worker,
            [[bar, tc_name, tc_info, port] for tc_name, tc_info in tc_list.items()],
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
                        "%d,%s,%s\n" % (query[0], query[1], query[2].replace("\n", " "))
                    )

        LOGGER.info("All done.")
