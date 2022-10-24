#!/usr/bin/env bash

RED=$'\e[0;31m'
NC=$'\e[0m'

if [[ $# -eq 0 ]] ; then
    printf "\n${RED}Path to file or directory is required.${NC}\n"
    exit 1
fi

grep -rnw "from \." $1
if [ $? -eq 0 ]
then
    printf "\n${RED}These files contain imports that use relative paths. Use only absolute paths for imports.${NC}\n"
    exit 1
fi