#! /bin/bash

if [ $# != 2 ]
then
  echo "Usage : ./extract_ids.sh wiki_dump_path output_file_path"
  exit 1
fi

dump=$1
output_file=$2

python3 /u/pagesluc/Documents/Memoire/wikiextractor/wikiextractor/WikiExtractor.py "$dump" --json -l --processes 20 -o - | bzip2 -c > "$output_file"
