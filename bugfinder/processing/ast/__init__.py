""" Module containing abstract AST processing classes.
"""

import re
from abc import abstractmethod

from bugfinder.processing.neo4j import Neo4J3Processing
from bugfinder.settings import LOGGER


class AbstractASTMarkup(Neo4J3Processing):
    """Abstract class to markup the AST"""

    SET_AST_MARKUP_CMD = """
       UNWIND %s as data
       MATCH (n)
       WHERE id(n) = data.id
       SET n.ast = data.ast
    """

    @abstractmethod
    def get_ast_information(self):
        """Retrieve AST information. Must be defined in the subclasses."""
        raise NotImplementedError("get_ast_information")

    @abstractmethod
    def build_ast_markup(self, ast_item):
        """Build the AST markup. Must be defined in the subclasses."""
        raise NotImplementedError("build_ast_markup")

    def send_commands(self):
        """Sends the command to the container."""
        self.fix_data_folder_rights()

        super().send_commands()

        LOGGER.info("Retrieving AST...")
        ast_list = self.get_ast_information()

        LOGGER.debug("AST retrieved. Creating command bundles...")

        # Slicing the list into several command
        cmd_list = []
        limit = 2000

        for i in range(int(len(ast_list) / limit) + 1):
            lower = i * limit
            upper = (i + 1) * limit

            if upper >= len(ast_list):
                upper = len(ast_list)

            cmd_list.append(ast_list[lower:upper])

        LOGGER.info(
            "Found %d AST. Prepared %d command bundles.", len(ast_list), len(cmd_list)
        )
        # LOGGER.info(cmd_list)
        for cmd_index, operation_list in enumerate(cmd_list):
            LOGGER.debug("Preparing operations...")

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
            except Exception as exc:
                LOGGER.info("Command %e failed: %s", cmd_index, str(exc))
                import traceback

                traceback.print_exc()
            else:
                LOGGER.info(
                    "AST command %d/%d successfully run.", cmd_index + 1, len(cmd_list)
                )

        LOGGER.info("AST updated.")
