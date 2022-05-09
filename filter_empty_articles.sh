#!/bin/bash

if [ "$#" != 2 ]; then
    echo "Usage : ./filter_empty_articles.sh dump output"
    exit 1
fi

wikipedia_dump="$1"
output_file="$2"

bzcat "$wikipedia_dump" | jq -c 'select(.text != "")' | bzip2 -c > "$output_file"
