#!/usr/bin/env bash
DIR_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
REPO_PATH="${DIR_PATH}/.."

# Import readme file
repo_readme="${REPO_PATH}/README.rst"
docs_readme="${DIR_PATH}/readme.rst"

echo "Introduction" > ${docs_readme}
echo "============" >> ${docs_readme}
tail -n+3  ${repo_readme} >> ${docs_readme}
sed -i -r 's;docs/(_static);\1;g' ${docs_readme}

# TODO Generate RST files based on Python files
