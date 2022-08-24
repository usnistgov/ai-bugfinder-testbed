import re
from os import listdir
from os.path import join, splitext
from shutil import move

from bugfinder.processing.tokenizers import main_func, keywords, AbstractTokenizer
from bugfinder.settings import LOGGER


class ReplaceFunctions(AbstractTokenizer):
    """Processing to replace user-created functions from a dataset."""

    def execute(self):
        """Run the processing"""
        LOGGER.debug("Replacing functions from file...")

        file_processing_list = [
            join(test_case, filepath)
            for test_case in self.dataset.test_cases
            for filepath in listdir(join(self.dataset.path, test_case))
            if splitext(filepath)[1] in [".c", ".h"]
        ]

        while len(file_processing_list) != 0:
            filepath = file_processing_list.pop(0)
            LOGGER.debug(
                "Replacing functions in %s (%d items left)...",
                filepath,
                len(file_processing_list),
            )

            self.process_file(join(self.dataset.path, filepath))

    @staticmethod
    def process_file(filepath):
        """Process a single file looking for user-created functions and replace them
        with a token FUN to reduce uniqueness in the corpus.

        Args:
            filepath (str): Path of the file to be processed

        Returns:
            int: number of functions replaced
        """
        tmp_filepath = "%s.tmp" % filepath

        function_symbols = dict()
        function_count = 0

        replaced_code = []

        with open(filepath, "r") as in_file:
            code = in_file.readlines()

            for line in code:
                # TODO: Remove these replacements and put it in a separate function
                str_lit_line = re.sub(r'".*?"', "", line)
                hex_line = re.sub(r"0[xX][0-9a-fA-F]+", "HEX", str_lit_line)
                ascii_line = re.sub(r"[^\x00-\x7f]", r"", hex_line)

                line_functions = re.findall(r"\b([_A-Za-z]\w*)\b(?=\s*\()", ascii_line)

                for function_name in line_functions:
                    if (len({function_name}.difference(main_func)) != 0) and (
                        len({function_name}.difference(keywords)) != 0
                    ):
                        if function_name not in function_symbols.keys():
                            function_count += 1

                            function_symbols[function_name] = "FUN" + str(
                                function_count
                            )

                        ascii_line = re.sub(
                            r"\b(" + function_name + r")\b(?=\s*\()",
                            function_symbols[function_name],
                            ascii_line,
                        )

                replaced_code.append(ascii_line)

        LOGGER.debug("%d functions replaced in %s", function_count, filepath)

        with open(tmp_filepath, "w") as out_file:
            out_file.writelines(replaced_code)

        move(tmp_filepath, filepath)

        return function_count
