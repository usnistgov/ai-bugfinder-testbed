from os import listdir
from os.path import join, splitext

import re
from shutil import move

from bugfinder.dataset.processing import DatasetProcessing, DatasetFileProcessing
from bugfinder.settings import LOGGER


class ReplaceLitterals(DatasetProcessing):
    replacements = {
        r"(.*)L\'([^\']*)\'(.*)": "\\g<1>L('\\g<2>')\\g<3>",
        r'(.*)L"([^"]*)"(.*)': '\\g<1>L("\\g<2>")\\g<3>',
    }

    def execute(self):
        LOGGER.debug("Replacing litterals in code...")
        file_processing_list = [
            join(test_case, filepath)
            for test_case in self.dataset.test_cases
            for filepath in listdir(join(self.dataset.path, test_case))
            if splitext(filepath)[1] in [".c", ".cpp", ".h", ".hpp"]
        ]

        while len(file_processing_list) != 0:
            filepath = file_processing_list.pop(0)
            LOGGER.debug(
                "Replacing litterals in %s (%d items left)..."
                % (filepath, len(file_processing_list))
            )

            repl_count = self.process_file(join(self.dataset.path, filepath))

            # If replacement were made, we keep the file for another round.
            if repl_count != 0:
                file_processing_list.append(filepath)

        LOGGER.info("Litterals successfully replaced.")

    def process_file(self, filepath):
        tmp_filepath = "%s.tmp" % filepath
        out_lines = list()
        repl_count = 0

        # Matching regexp on every line and replace them.
        with open(filepath, "r") as in_file:
            for line in in_file:
                for src, dest in list(self.replacements.items()):
                    if re.match(src, line):
                        repl_count += 1
                        line = re.sub(src, dest, line)

                out_lines.append(line)

        # If replacement were performed, we save them to the new file and
        # replace the old file by the new one.
        if repl_count != 0:
            with open(tmp_filepath, "w") as out_file:
                out_file.writelines(out_lines)

            move(tmp_filepath, filepath)

        return repl_count


class RemoveMainFunction(DatasetFileProcessing):
    main_fn_entry = "#ifdef INCLUDEMAIN\n"
    main_fn_exit = "#endif\n"

    def execute(self):
        LOGGER.debug("Removing main function in dataset at '%s'..." % self.dataset.path)
        super().execute()
        LOGGER.info("Main function successfully removed.")

    def process_file(self, filepath):
        if splitext(filepath)[1] not in [".c", ".cpp", ".h", ".hpp"]:
            LOGGER.debug("File %s is not a code file. Ignoring..." % filepath)
            return

        LOGGER.debug("Removing main function in '%s'." % filepath)
        tmp_filepath = "%s.tmp" % filepath
        is_in_main_fn = False
        out_lines = list()

        # Remove every line between `self.main_fn_entry` and
        # `self.main_fn_exit`.
        with open(filepath, "r") as in_file:
            for line in in_file:
                if not is_in_main_fn:
                    if line != self.main_fn_entry:
                        out_lines.append(line)
                    else:
                        is_in_main_fn = True
                else:  # is_in_main_fn == True
                    if line == self.main_fn_exit:
                        is_in_main_fn = False

        # Save transformations to the new file and replace the old file
        with open(tmp_filepath, "w") as out_file:
            out_file.writelines(out_lines)

        move(tmp_filepath, filepath)
