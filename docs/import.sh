#!/usr/bin/env bash
DIR_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
REPO_PATH="${DIR_PATH}/.."
API_PATH="${DIR_PATH}/api"
API_INDEX_TEMPLATE="${DIR_PATH}/_templates/api/index.rst"
API_MODULE_TEMPLATE="${DIR_PATH}/_templates/api/module.rst"

# Import readme file
repo_readme="${REPO_PATH}/README.rst"
docs_readme="${DIR_PATH}/readme.rst"

echo "Introduction" > ${docs_readme}
echo "============" >> ${docs_readme}
tail -n+3  ${repo_readme} | head -n-3 >> ${docs_readme}
sed -i -r 's;docs/(_static);\1;g' ${docs_readme}

# Generate RST files based on Python files
echo "Generating new documentation files..."
for pyf in $(find ${REPO_PATH}/ -type f -name "*.py" | grep -vE "${REPO_PATH}/(docs|dist)")
do
  RST_FILE="$(echo "${pyf}" | sed -r "s;${REPO_PATH}/(.*\.)py$;\1rst;")"
  RST_PATH="${API_PATH}/${RST_FILE}"
  TPL_FILE="${API_MODULE_TEMPLATE}"

  if [[ $(basename "${pyf}") == "__init__.py" ]]
  then
    RST_PATH="${API_PATH}/$(dirname $RST_FILE)/index.rst"
    TPL_FILE="${API_INDEX_TEMPLATE}"
  fi


  if [[ ! -f "${RST_PATH}" ]]
  then
    echo "Creating ${API_PATH}/${RST_FILE}..."
    mkdir -p "${API_PATH}/$(dirname $RST_FILE)"
    cp "${TPL_FILE}" "${RST_PATH}"
  fi
done

for apif in $(find ${API_PATH}/ -type f -name "*.rst")
do
  if [[ $(grep -c "#name#" "${apif}") -eq 0 ]]
  then
    continue
  fi

  echo "Replacing placeholders in ${apif}..."

  MODULE_NAME=$(echo "${apif}" | sed -r "s;${API_PATH}/(.*)\.rst;\1;")
  MODULE_NAME=$(echo "${MODULE_NAME}" | tr '/' '.' |  sed -r "s;\.index$;;")

  tail -n+2 ${apif} | sed -r "s;#name#;${MODULE_NAME};" > ${apif}.body

  echo ${MODULE_NAME} > ${apif}.head
  echo ${MODULE_NAME} | sed -r 's;.;=;g' >> ${apif}.head

  cat ${apif}.head ${apif}.body > ${apif}
  rm ${apif}.*

  if [[ $(basename ${apif}) != "index.rst" ]]
  then
    continue
  fi

  echo "Adding toctree..."

  api_dir=$(dirname "${apif}")
  echo "" >> ${apif}

  for othf in $(find "${api_dir}" -mindepth 1 -maxdepth 1 -type f | grep -v index)
  do
    echo "${othf}" | sed -r "s;${api_dir}/(.+)\.rst;    \1;" >> ${apif}
  done
  for dir in $(find "${api_dir}" -mindepth 1 -maxdepth 1 -type d)
  do
    echo "${dir}/index" | sed -r "s;${api_dir}/;    ;" >> ${apif}
  done
done

echo "Job done!"
