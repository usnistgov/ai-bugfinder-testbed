import re
from shutil import move

from bugfinder.processing import AbstractCppFileProcessing
from bugfinder.settings import LOGGER


class RemoveComments(AbstractCppFileProcessing):
    """Processing to remove comments from a certain dataset based on RegEx."""

    def execute(self):
        """Run the processing"""
        LOGGER.debug("Removing comments in dataset at '%s'...", self.dataset.path)
        super().execute()
        LOGGER.info("Comments successfully removed.")

    def process_file(self, filepath):
        tmp_filepath = "%s.tmp" % filepath

        rx_comments = re.compile(
            r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)", re.MULTILINE | re.DOTALL
        )

        def _replacer(match):
            if match.group(2) is not None:
                return ""

            return match.group(1)

        with open(filepath, "r") as in_file:
            code = in_file.read()

            stripped_code = rx_comments.sub(_replacer, code)

            code_as_list = [line.strip() for line in stripped_code.splitlines()]
            code_as_list = list(filter(None, code_as_list))

        with open(tmp_filepath, "w") as out_file:
            for line in code_as_list:
                out_file.write(f"{line}\n")

        move(tmp_filepath, filepath)
