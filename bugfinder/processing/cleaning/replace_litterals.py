"""
"""

import re
from shutil import move

from bugfinder.processing import AbstractCppFileProcessing
from bugfinder.settings import LOGGER


class ReplaceLitterals(AbstractCppFileProcessing):
    """Replace unrecognized litterals in the test cases"""

    replacements = {
        r"(.*)L\'([^\']*)\'(.*)": "\\g<1>L('\\g<2>')\\g<3>",
        r'(.*)L"([^"]*)"(.*)': '\\g<1>L("\\g<2>")\\g<3>',
    }

    def execute(self):
        """Execute the processing"""
        LOGGER.debug("Replacing litterals in dataset...")
        repl_count = -1

        while repl_count != 0:
            retcode = super().execute()
            repl_count = sum(retcode)

        LOGGER.info("Litterals successfully replaced.")

    def process_file(self, filepath):
        """Replace litteral in a single file"""
        tmp_filepath = f"{filepath}.tmp"
        out_lines = []
        repl_count = 0

        # Matching regexp on every line and replace them.
        with open(filepath, "r", encoding="utf-8") as in_file:
            for line in in_file:
                for src, dest in list(self.replacements.items()):
                    if re.match(src, line):
                        repl_count += 1
                        line = re.sub(src, dest, line)

                out_lines.append(line)

        # If replacement were performed, we save them to the new file and
        # replace the old file by the new one.
        if repl_count != 0:
            with open(tmp_filepath, "w", encoding="utf-8") as out_file:
                out_file.writelines(out_lines)

            move(tmp_filepath, filepath)

        return repl_count
