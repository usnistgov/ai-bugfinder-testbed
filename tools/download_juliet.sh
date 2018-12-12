#!/bin/bash
# Script downloading CWE121 test cases from Juliet 1.3
#
# ==============================================================================
# Script parameters
SARD_WEBSITE="https://samate.nist.gov/SARD"
JULIET_FILE="Juliet_Test_Suite_v1.3_for_C_Cpp.zip"
JULIET_PATH="${SARD_WEBSITE}/testsuites/juliet/${JULIET_FILE}"
JULIET_EXTRACT_PATH="C/testcases/CWE121_Stack_Based_Buffer_Overflow"

CURRENT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
DATA_PATH="${CURRENT_PATH}/../data"
DATASET_PATH="${DATA_PATH}/cwe121_orig"

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
    echo "Removing cwe121_orig..."
    rm -rf "${DATASET_PATH}"
fi

if [[ -d "${DATA_PATH}/cwe121_annot" ]]
then
    echo "Removing cwe121_annot..."
    rm -rf "${DATA_PATH}/cwe121_annot"
fi

mv ${DATA_PATH}/$(dirname ${JULIET_EXTRACT_PATH})/* ${DATASET_PATH}
rm -rf ${DATA_PATH}/C

echo "Juliet extracted. Flattening test suite..."

for d in $(ls ${DATASET_PATH})
do
    mv ${DATASET_PATH}/${d}/* -t ${DATASET_PATH}
    rm -rf ${DATASET_PATH}/${d}
done

echo "Juliet flattened. Processing test cases..."

# Read Juliet test cases line by line and separate good, bad and common code
# into directories “good” and “bad”
cd ${DATASET_PATH} && find . -type f -name "*.c" -o -name "*.cpp" \
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
            GDIR="../cwe121_annot/good/${DN}/${ITC}"
            BDIR="../cwe121_annot/bad/${DN}/${ITC}"
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
