import re
from os import listdir
from os.path import join, splitext
from shutil import move

from bugfinder.dataset.processing import DatasetProcessing
from bugfinder.settings import LOGGER

single_char_ops = {
    "(",
    ")",
    "[",
    "]",
    ".",
    "+",
    "-",
    "*",
    "&",
    "/",
    "%",
    "<",
    ">",
    "^",
    "|",
    "=",
    ",",
    "?",
    ":",
    ";",
    "{",
    "}",
}

double_char_ops = {
    "->",
    "++",
    "--",
    "**",
    "!~",
    "<<",
    ">>",
    "<=",
    ">=",
    "==",
    "!=",
    "&&",
    "||",
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    "&=",
    "^=",
    "|=",
}

triple_char_ops = {"<<=", ">>="}


class TokenizeText(DatasetProcessing):
    def to_regex(self, ops):
        return r"|".join([f"({re.escape(op)})" for op in ops])

    def execute(self):
        LOGGER.debug("Starting tokenizing text from files...")

        file_processing_list = [
            join(test_case, filepath)
            for test_case in self.dataset.test_cases
            for filepath in listdir(join(self.dataset.path, test_case))
            if splitext(filepath)[1] in [".c", ".h"]
        ]

        while len(file_processing_list) != 0:
            filepath = file_processing_list.pop(0)

            LOGGER.debug(
                "Tokenizing content on file %s (%d items left)..."
                % (filepath, len(file_processing_list))
            )

            self.process_file(join(self.dataset.path, filepath))

    def process_file(self, filepath):
        tmp_filepath = "%s.tmp" % filepath
        tokens = []

        regex_split_operators = (
            self.to_regex(triple_char_ops)
            + self.to_regex(double_char_ops)
            + self.to_regex(single_char_ops)
        )

        with open(filepath, "r") as in_file:
            code = in_file.readlines()

            for line in code:
                if line == "":
                    continue

                line = re.sub("(\n)|(\\\\n)|(\\\\)|(\\t)|(\\r)", "", line)
                splitter = r" +|" + regex_split_operators + r"|(\/)|(\;)|(\-)|(\*)"

                line = re.split(splitter, line)

                line = list(filter(None, line))
                line = list(filter(str.strip, line))

                tokens.extend(line)

        with open(tmp_filepath, "w") as out_file:
            out_file.writelines(token + "\n" for token in tokens)

        move(tmp_filepath, filepath)