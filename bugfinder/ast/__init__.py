"""
"""
import re
from abc import abstractmethod
from os.path import exists, join
from pickle import dump, load

from bugfinder.neo4j import Neo4J3Processing
from bugfinder.settings import ROOT_DIR, LOGGER


class AbstractASTMarkup(Neo4J3Processing):
    SET_AST_MARKUP_CMD = """
       UNWIND %s as data
       MATCH (n)
       WHERE id(n) = data.id
       SET n.ast = data.ast
    """

    @abstractmethod
    def get_ast_information(self):
        raise NotImplementedError("get_ast_information")

    @abstractmethod
    def build_ast_markup(self, ast_item):
        raise NotImplementedError("build_ast_markup")

    def send_commands(self):
        self.fix_data_folder_rights()

        super().send_commands()

        LOGGER.info("Retrieving AST...")
        ast_list = self.get_ast_information()

        LOGGER.info("%d item found. Creating command bundles..." % len(ast_list))

        # Slicing the list into several command
        cmd_list = []
        limit = 2000

        for i in range(int(len(ast_list) / limit) + 1):
            lower = i * limit
            upper = (i + 1) * limit

            if upper >= len(ast_list):
                upper = len(ast_list)

            cmd_list.append(ast_list[lower:upper])

        LOGGER.info("%d bundles prepared." % len(cmd_list))

        for operation_list in cmd_list:
            LOGGER.debug("Prepping operations...")

            # For each item, create the correct notation
            operation_list = [
                self.build_ast_markup(ast_item) for ast_item in operation_list
            ]

            # Cleanup dict to be parsed by Neo4J
            ast_update_dict = str(operation_list)
            ast_update_dict = re.sub(r"u\'([^\']*)\'", "'\\g<1>'", ast_update_dict)
            ast_update_dict = re.sub(r"\'([^\']*)\':", "\\g<1>:", ast_update_dict)

            LOGGER.debug("Updating AST...")
            try:
                self.neo4j_db.run(self.SET_AST_MARKUP_CMD % ast_update_dict)
            except Exception as e:
                LOGGER.info(str(e))

            LOGGER.info("AST command successfully run.")

        LOGGER.info("AST updated")


class ASTSetExporter(Neo4J3Processing):
    """ Generate the set of AST retrieved from a Neo4J database
    """

    ast_list_command = """
        MATCH (n:GenericNode) 
        WHERE EXISTS(n.ast)
        RETURN n.ast as ast
    """
    ast_file = None

    def execute(self, command_args=None, ast_file="nodes_ast.bin"):
        self.ast_file = ast_file
        super().execute(command_args)

    def configure_container(self):
        super().configure_container()
        self.container_name = "ast-set-generator"

    def send_commands(self):
        super().send_commands()
        ast_node_filepath = join(ROOT_DIR, self.ast_file)

        if exists(ast_node_filepath):
            with open(ast_node_filepath, "rb") as ast_node_file:
                ast_list = list(load(ast_node_file))
        else:
            ast_list = list()

        # Concatenate list of AST if it already exists
        ast_list += [
            item["ast"] for item in self.neo4j_db.run(self.ast_list_command).data()
        ]

        # Write data to disk in CSV format
        with open(ast_node_filepath, "wb") as ast_node_file:
            dump(set(ast_list), ast_node_file)