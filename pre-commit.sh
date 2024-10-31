#!/bin/bash -e
if [ -z "${VIRTUAL_ENV}" ] ; then
  echo "Please activate your virtual environment before commit!"
  exit 1
fi
# format with black and add any changes to the commit
root=$(git rev-parse --show-toplevel)
black ${root} | while read line ; do
  if [[ ${line} == "reformatted*" ]] ; then
    len=$(($(wc -c <<< ${line})-12))
    file=${line:12:len}
    git add ${file}
  fi
done
# lint with ruff
ruff check ${root}
# test
pytest -x --no-header
