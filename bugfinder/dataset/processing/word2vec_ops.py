import re
from os import listdir
from os.path import join, splitext
from shutil import move

from bugfinder.dataset.processing import DatasetProcessing
from bugfinder.settings import LOGGER


keywords = frozenset(
    {
        "__asm",
        "__builtin",
        "__cdecl",
        "__declspec",
        "__except",
        "__export",
        "__far16",
        "__far32",
        "__fastcall",
        "__finally",
        "__import",
        "__inline",
        "__int16",
        "__int32",
        "__int64",
        "__int8",
        "__leave",
        "__optlink",
        "__packed",
        "__pascal",
        "__stdcall",
        "__system",
        "__thread",
        "__try",
        "__unaligned",
        "_asm",
        "_Builtin",
        "_Cdecl",
        "_declspec",
        "_except",
        "_Export",
        "_Far16",
        "_Far32",
        "_Fastcall",
        "_finally",
        "_Import",
        "_inline",
        "_int16",
        "_int32",
        "_int64",
        "_int8",
        "_leave",
        "_Optlink",
        "_Packed",
        "_Pascal",
        "_stdcall",
        "_System",
        "_try",
        "alignas",
        "alignof",
        "and",
        "and_eq",
        "asm",
        "auto",
        "bitand",
        "bitor",
        "bool",
        "break",
        "case",
        "catch",
        "char",
        "char16_t",
        "char32_t",
        "class",
        "compl",
        "const",
        "const_cast",
        "constexpr",
        "continue",
        "decltype",
        "default",
        "delete",
        "do",
        "double",
        "dynamic_cast",
        "else",
        "enum",
        "explicit",
        "export",
        "extern",
        "false",
        "final",
        "float",
        "for",
        "friend",
        "goto",
        "if",
        "inline",
        "int",
        "long",
        "mutable",
        "namespace",
        "new",
        "noexcept",
        "not",
        "not_eq",
        "nullptr",
        "operator",
        "or",
        "or_eq",
        "override",
        "private",
        "protected",
        "public",
        "register",
        "reinterpret_cast",
        "return",
        "short",
        "signed",
        "sizeof",
        "static",
        "static_assert",
        "static_cast",
        "struct",
        "switch",
        "template",
        "this",
        "thread_local",
        "throw",
        "true",
        "try",
        "typedef",
        "typeid",
        "typename",
        "union",
        "unsigned",
        "using",
        "virtual",
        "void",
        "volatile",
        "wchar_t",
        "while",
        "xor",
        "xor_eq",
        "NULL",
    }
)

main_set = frozenset({"main"})

main_args = frozenset({"argc", "argv"})

##################################################################################


class RemoveComments(DatasetProcessing):
    def execute(self):
        LOGGER.debug("Starting removing comments from files...")

        file_processing_list = [
            join(test_case, filepath)
            for test_case in self.dataset.test_cases
            for filepath in listdir(join(self.dataset.path, test_case))
            if splitext(filepath)[1] in [".c", ".h"]
        ]

        while len(file_processing_list) != 0:
            filepath = file_processing_list.pop(0)
            LOGGER.debug(
                "Removing comments in %s (%d items left)..."
                % (filepath, len(file_processing_list))
            )

            self.process_file(join(self.dataset.path, filepath))

    def process_file(self, filepath):
        tmp_filepath = "%s.tmp" % filepath

        rx_comments = re.compile(
            r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)", re.MULTILINE | re.DOTALL
        )

        def _replacer(match):
            if match.group(2) is not None:
                return ""
            else:
                return match.group(1)

        with open(filepath, "r") as in_file:
            code = in_file.read()

            stripped_code = rx_comments.sub(_replacer, code)

            code_as_list = [line.strip() for line in stripped_code.splitlines()]
            code_as_list = list(filter(None, code_as_list))

        with open(tmp_filepath, "w") as out_file:
            for line in code_as_list:
                out_file.write(line)
                out_file.write("\n")
            # out_file.writelines(stripped_list)

        move(tmp_filepath, filepath)


##################################################################################


class ReplaceFunctions(DatasetProcessing):
    def execute(self):
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
                "Replacing functions in %s (%d items left)..."
                % (filepath, len(file_processing_list))
            )

            self.process_file(join(self.dataset.path, filepath))

    def process_file(self, filepath):
        tmp_filepath = "%s.tmp" % filepath

        function_symbols = dict()
        function_count = 1

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
                    if (len({function_name}.difference(main_set)) != 0) and (
                        len({function_name}.difference(keywords)) != 0
                    ):
                        if function_name not in function_symbols.keys():
                            function_symbols[function_name] = "FUN" + str(
                                function_count
                            )
                            function_count += 1

                        ascii_line = re.sub(
                            r"\b(" + function_name + r")\b(?=\s*\()",
                            function_symbols[function_name],
                            ascii_line,
                        )

                replaced_code.append(ascii_line)

        LOGGER.debug("%d functions replaced in %s" % (function_count, filepath))

        with open(tmp_filepath, "w") as out_file:
            out_file.writelines(replaced_code)

        move(tmp_filepath, filepath)


##################################################################################
class ReplaceVariables(DatasetProcessing):
    def execute(self):
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
                "Replacing variables in %s (%d items left)..."
                % (filepath, len(file_processing_list))
            )

            self.process_file(join(self.dataset.path, filepath))

    def process_file(self, filepath):
        tmp_filepath = "%s.tmp" % filepath

        var_symbols = dict()
        var_count = 1

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
                        len({var_name[0]}.difference(main_args)) != 0
                    ):
                        if var_name[0] not in var_symbols.keys():
                            var_symbols[var_name[0]] = "VAR" + str(var_count)
                            var_count += 1

                        ascii_line = re.sub(
                            r"\b("
                            + var_name[0]
                            + r")\b(?:(?=\s*\w+\()|(?!\s*\w+))(?!\s*\()",
                            var_symbols[var_name[0]],
                            ascii_line,
                        )

                replaced_code.append(ascii_line)

        LOGGER.debug("%d variables replaced in %s" % (var_count, filepath))

        with open(tmp_filepath, "w") as out_file:
            out_file.writelines(replaced_code)

        move(tmp_filepath, filepath)
