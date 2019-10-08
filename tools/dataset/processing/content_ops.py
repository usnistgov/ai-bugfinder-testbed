import re
from os import listdir
from os.path import join
from shutil import move

from tools.dataset.processing import DatasetProcessing, DatasetFileProcessing
from tools.settings import LOGGER


class ReplaceLitterals(DatasetProcessing):
    replacements = {
        r'(.*)L\'([^\']*)\'(.*)': "\\g<1>L('\\g<2>')\\g<3>",
        r'(.*)L"([^"]*)"(.*)': "\\g<1>L(\"\\g<2>\")\\g<3>",
    }

    def execute(self):
        LOGGER.debug("Starting replacing litterals...")
        file_processing_list = [
            join(test_case, filepath) for test_case in self.dataset.test_cases
            for filepath in listdir(join(self.dataset.path, test_case))
        ]

        while len(file_processing_list) != 0:
            LOGGER.debug(
                "Replacing litterals in file list (%d items)..." %
                len(file_processing_list)
            )
            filepath = file_processing_list.pop(0)

            repl_count = self.process_file(
                join(self.dataset.path, filepath)
            )

            # If replacement were made, we keep the file for another round.
            if repl_count != 0:
                LOGGER.debug("Adding %s back to the queue..." % filepath)
                file_processing_list.append(filepath)

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

    def process_file(self, filepath):
        LOGGER.debug("Removing main function in %s" % filepath)
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
