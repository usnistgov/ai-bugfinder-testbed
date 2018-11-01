#!/bin/bash
DIR_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
DATA_PATH="${DIR_PATH}/data"
DATASET="C/testcases/CWE121_Stack_Based_Buffer_Overflow"

NPROC=$(( $(nproc) / 2 ))
mkdir -p ${DATA_PATH}

# Download and extract Juliet
wget https://samate.nist.gov/SARD/testsuites/juliet/Juliet_Test_Suite_v1.3_for_C_Cpp.zip -P ${DATA_PATH}
#unzip Juliet_Test_Suite_v1.3_for_C_Cpp.zip C/testcases/CWE121_Stack_Based_Buffer_Overflow/* C/testcasesupport/*
unzip ${DATA_PATH}/Juliet_Test_Suite_v1.3_for_C_Cpp.zip ${DATASET}/* -d ${DATA_PATH}

mv ${DATA_PATH}/C/* ${DATA_PATH}
rm -rf ${DATA_PATH}/C
mkdir -p ${DATA_PATH}/annot

# Read Juliet test cases line by line and separate good, bad and common code into directories “good” and “bad”
cd ${DATA_PATH} && \
  find testcases -type f -name "*.c" -o -name "*.cpp" -o -name "*.h" -o -name "*.hpp" | xargs -I {} -P $((2*${NPROC})) bash -c ' 
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
		GDIR="./annot/good/${DN}/${ITC}"
		BDIR="./annot/bad/${DN}/${ITC}"
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

