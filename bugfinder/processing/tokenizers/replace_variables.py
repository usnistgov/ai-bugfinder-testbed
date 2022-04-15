from os import listdir
from os.path import join, splitext

import re
from shutil import move

from bugfinder.base.processing import AbstractProcessing
from bugfinder.processing.tokenizers import main_vars, keywords
from bugfinder.settings import LOGGER


class ReplaceVariables(AbstractProcessing):
    """Processing to replace user-created functions from a dataset."""

    def execute(self):
        """Run the processing."""
        LOGGER.debug("Replacing variables from file...")

        file_processing_list = [
            join(test_case, filepath)
            for test_case in self.dataset.test_cases
            for filepath in listdir(join(self.dataset.path, test_case))
            if splitext(filepath)[1] in [".c", ".h"]
        ]

        while len(file_processing_list) != 0:
            filepath = file_processing_list.pop(0)
            LOGGER.debug(
                "Replacing variables in %s (%d items left)...",
                filepath,
                len(file_processing_list),
            )

            self.process_file(join(self.dataset.path, filepath))

    @staticmethod
    def process_file(filepath):
        """Process a single file looking for user-created variables and replace them with a token VAR to reduce uniqueness in the corpus.

        Args:
            filepath (str): Path of the file to be processed

        Returns:
            int: number of variables replaced
        """
        tmp_filepath = "%s.tmp" % filepath

        var_symbols = dict()
        var_count = 0

        replaced_code = []

        with open(filepath, "r") as in_file:
            code = in_file.readlines()

            for line in code:
                # TODO: Remove these replacements and put it in a separate function
                str_lit_line = re.sub(r'".*?"', "", line)
                hex_line = re.sub(r"0[xX][0-9a-fA-F]+", "HEX", str_lit_line)
                ascii_line = re.sub(r"[^\x00-\x7f]", r"", hex_line)

                line_vars = re.findall(
                    r"\b([_A-Za-z]\w*)\b((?!\s*\**\w+))(?!\s*\()", ascii_line
                )

                for var_name in line_vars:
                    if (len({var_name[0]}.difference(keywords)) != 0) and (
                        len({var_name[0]}.difference(main_vars)) != 0
                    ):
                        if var_name[0] not in var_symbols.keys():
                            var_count += 1
                            var_symbols[var_name[0]] = "VAR" + str(var_count)

                        ascii_line = re.sub(
                            r"\b("
                            + var_name[0]
                            + r")\b(?:(?=\s*\w+\()|(?!\s*\w+))(?!\s*\()",
                            var_symbols[var_name[0]],
                            ascii_line,
                        )

                replaced_code.append(ascii_line)

        LOGGER.debug("%d variables replaced in %s", var_count, filepath)

        with open(tmp_filepath, "w") as out_file:
            out_file.writelines(replaced_code)

        move(tmp_filepath, filepath)

        return var_count
