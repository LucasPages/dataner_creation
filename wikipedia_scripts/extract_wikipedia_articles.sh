#! /bin/bash

if [ $# != 2 ]
then
  echo "Usage : ./extract_wikipedia_articles.sh wiki_dump_path output_file_path"
  exit 1
fi

dump=$1
output_file=$2

python3 wikiextractor/wikiextractor/WikiExtractor.py "$dump" --json -l --processes 20 -o - | jq -c 'select(.text != "")' | bzip2 -c > "$output_file"
