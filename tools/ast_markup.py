
from os.path import join

import sys

from tools.libs.ast.v01 import main as ast_v01
from tools.libs.ast.v02 import main as ast_v02
from tools.settings import ROOT_DIR, LOGGER

USAGE = "python ./tools/ast_markup.py ${DB_DIR} ${AST_VERSION}"

COMMANDS = {
    "v01": ast_v01,
    "v02": ast_v02
}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        LOGGER.error("Illegal number of arguments. Usage: %s." % USAGE)
        exit(1)

    db_path = join(ROOT_DIR, sys.argv[1])
    COMMANDS[sys.argv[2]](db_path)

    LOGGER.info("AST property added to the nodes")
