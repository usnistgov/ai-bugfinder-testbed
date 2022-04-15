"""
"""

from shutil import move

from bugfinder.processing import AbstractCppFileProcessing
from bugfinder.settings import LOGGER


class RemoveMainFunction(AbstractCppFileProcessing):
    """Processing to remove the main function from a dataset."""

    main_fn_entry = "#ifdef INCLUDEMAIN\n"
    main_fn_exit = "#endif\n"

    def execute(self):
        """Run the processing"""
        LOGGER.debug("Removing main function in dataset at '%s'...", self.dataset.path)
        super().execute()
        LOGGER.info("Main function successfully removed.")

    def process_file(self, filepath):
        """Process a single file"""
        LOGGER.debug("Removing main function in '%s'.", filepath)
        tmp_filepath = f"{filepath}.tmp"
        is_in_main_fn = False
        out_lines = []

        # Remove every line between `self.main_fn_entry` and
        # `self.main_fn_exit`.
        with open(filepath, "r", encoding="utf-8") as in_file:
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
        with open(tmp_filepath, "w", encoding="utf-8") as out_file:
            out_file.writelines(out_lines)

        move(tmp_filepath, filepath)
