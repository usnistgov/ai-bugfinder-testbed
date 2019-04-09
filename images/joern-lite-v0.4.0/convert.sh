#!/bin/sh
CHOWN_IDS=$(stat -c "%u:%g" /code)
TMP_DB_FOLDER="/tmp/joern.db"
FINAL_DB_FOLDER="/code/joern.db"

if [[ -d ${TMP_DB_FOLDER} ]]
then
  echo "Temp DB directory already exists. Cleaning before execution..."
  rm -rf ${TMP_DB_FOLDER}
  echo "Temp DB directory removed."
fi

if [[ -d ${FINAL_DB_FOLDER} ]]
then
  echo "Directory joerndb already exists in /code. Remove or rename it before execution."
  exit 1
fi

java -Xmx4G -cp "/usr/local/lib/*" tools.parser.ParserMain -outformat csv -outdir ${TMP_DB_FOLDER} /code
mv ${TMP_DB_FOLDER} ${FINAL_DB_FOLDER}
chown -R ${CHOWN_IDS} /code
