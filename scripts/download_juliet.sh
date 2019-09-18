#!/bin/bash
# Script downloading CWE121 test cases from Juliet 1.3
#
# ==============================================================================
# Script parameters
SARD_WEBSITE="https://samate.nist.gov/SARD"
JULIET_FILE="Juliet_Test_Suite_v1.3_for_C_Cpp.zip"
JULIET_PATH="${SARD_WEBSITE}/testsuites/juliet/${JULIET_FILE}"
JULIET_EXTRACT_PATH="C/testcases"

CURRENT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
DATA_PATH="${CURRENT_PATH}/../data"
DATASET_PATH="${DATA_PATH}/juliet_orig"
ANNOT_SET_PATH="${DATA_PATH}/juliet_annot"

NPROC=$(nproc)
#
# ==============================================================================
# Download, extract Juliet and move to a separate folder
echo "Extracting Juliet...."

mkdir -p ${DATASET_PATH}

if [[ ! -f "${DATA_PATH}/${JULIET_FILE}" ]]
then
    wget ${JULIET_PATH} -P ${DATA_PATH}
fi

unzip -qq ${DATA_PATH}/${JULIET_FILE} ${JULIET_EXTRACT_PATH}/* -d ${DATA_PATH}

if [[ -d "${DATA_PATH}/$(basename ${JULIET_EXTRACT_PATH})/" ]]
then
    rm -rf "${DATA_PATH}/$(basename ${JULIET_EXTRACT_PATH})/"
fi

if [[ -d "${DATASET_PATH}" ]]
then
    echo "Removing juliet_orig..."
    rm -rf "${DATASET_PATH}"
fi

if [[ -d "${ANNOT_SET_PATH}" ]]
then
    echo "Removing juliet_annot..."
    rm -rf "${ANNOT_SET_PATH}"
fi

mv ${DATA_PATH}/$(dirname ${JULIET_EXTRACT_PATH})/* ${DATASET_PATH}
rm -rf ${DATA_PATH}/C

echo "Juliet extracted. Processings test suites..."

for cwe_folder in $(ls ${DATASET_PATH})
do
    echo "Flattening ${cwe_folder}..."
    CWE_FOLDER_PATH="${DATASET_PATH}/${cwe_folder}"

    for cwe_file in $(find ${CWE_FOLDER_PATH} -mindepth 2 -type f)
    do
        cwe_file_name="$(echo $(basename ${cwe_file}) | grep -v "CWE")"

        if [[ "${cwe_file_name}" != "" ]]
        then
            echo "Removing ${cwe_file}..."
            rm ${cwe_file}
        else
            mv ${cwe_file} ${CWE_FOLDER_PATH}
        fi
    done

    for cwe_subdir in $(find ${CWE_FOLDER_PATH} -mindepth 1 -maxdepth 1 -type d)
    do
        echo "Removing ${cwe_subdir}..."
        rm -r ${cwe_subdir}
    done

    echo "${cwe_folder} flattened. Processing test cases..."

    # Read Juliet test cases line by line and separate good, bad and common code
    # into directories “good” and “bad”
    cd ${CWE_FOLDER_PATH} && find . -type f -name "*.c" -o -name "*.cpp" \
        -o -name "*.h" -o -name "*.hpp" | xargs -I {} -P ${NPROC} bash -c '
            FILTERGOOD=false
            FILTERBAD=false

            echo "Processing: {}... "

            # Extract the test case name
            SFILE=$(basename {})
            ITC=$(echo ${SFILE} | sed "s/\(^CWE.*__.*_[0-9]\+\).*/\1/")
            if $(echo ${ITC} | grep -q "[0-9]$")
            then
                # Test case code, create an independent subdirectory for it
                DN=$(dirname {})
                GDIR="../../juliet_annot/good/${DN}/${ITC}"
                BDIR="../../juliet_annot/bad/${DN}/${ITC}"
                mkdir -p ${GDIR} ${BDIR}
                GFILE="${GDIR}/${SFILE}"
                BFILE="${BDIR}/${SFILE}"
            else
                # General purpose code, skip it
                exit 0
            fi

            # Check if the file has already been processed, in case we are resuming
            if [ -f ${GFILE} ] && [ -f ${BFILE} ]
            then
                echo "Already done"
                exit 0
            fi

            # Read the code line by line and filter out irrelevant code
            cat {} | while IFS="" read -r line || [[ -n "$line" ]]
            do
                # Optimization to skip the greps if possible
                if $(echo -n "$line" | grep -q "OMIT")
                then
                    if $(echo -n "$line" | grep -q "^#ifndef OMITBAD")
                    then FILTERBAD=true
                    elif $(echo -n "$line" | grep -q "^#endif .*OMITBAD")
                    then FILTERBAD=false
                    elif $(echo -n "$line" | grep -q "^#ifndef OMITGOOD")
                    then FILTERGOOD=true
                    elif $(echo -n "$line" | grep -q "^#endif .*OMITGOOD")
                    then FILTERGOOD=false
                    fi
                else
                    # Write the line to the appropriate file(s)
                    if ! $FILTERBAD
                    then echo "$line" >> ${GFILE}
                    fi
                    if ! $FILTERGOOD
                    then echo "$line" >> ${BFILE}
                    fi
                fi
            done'
done
