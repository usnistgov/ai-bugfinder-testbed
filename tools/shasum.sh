#!/bin/bash
# Test sha1sum of a particular directory

if [[ $# -ne 1 ]]
then
    echo "Please specify one and only one argument"
    exit 1
fi

if [[ ! -f "$1" && ! -d "$1" ]]
then
    echo "File or folder does not exist"
    exit 1
fi

find $1 -type f -print0 | sort -z | xargs -0 sha1sum | sha1sum
