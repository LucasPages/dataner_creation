#!/bin/bash

# This script selects the subset of WikiData pages (items) that are linked to English Wikipedia. In this repository, we
# we are only interested in this subset because we seek structured information about English Wikipedia articles.

if [ "$#" != 2 ]
then
	echo "Usage : ./select_en.sh wikidata_dump output_dump"
	exit 1
fi

dump="$1"
output_file="$2"

bzcat "$dump" | sed -E "s/(^\[|\]$|,$)//g" | sed -E "/^\s*$/d" | jq -c "select(.sitelinks.enwiki != null)" > "$output_file"