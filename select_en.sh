#!/bin/bash

if [ "$#" != 2 ]
then
	echo "Usage : ./select_en.sh wikidata_dump output_dump"
	exit 1
fi

dump="$1"
output_file="$2"

bzcat "$dump" | sed -E "s/(^\[|\]$|,$)//g" | sed -E "/^\s*$/d" | jq -c "select(.sitelinks.enwiki != null)" | bzip2 -c > "$output_file"