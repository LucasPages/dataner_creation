#! /bin/bash

# This file encompasses all the actions to be done with the WikiData dump in the creation of DataNER.

if [ $# != 1 ]
then
  echo "Usage : ./process_wikidata_dump.sh wikidata_dump_path"
  exit 1
fi

wikidata_dump="$1"
output_path="dumps/wikidata_dump_en.json"

echo "Selecting WikiData items connected to english Wikipedia"
./wikidata_scripts/select_en.sh "$wikidata_dump" "$output_path"

echo "Classifying WikiData pages into [LOC, PER, ORG] with the NECKAr tool."
./NECKAr/start_NECKAr.sh

echo "Creating a mapping from WikiData ID to Wikipedia title."
python wikidata_scripts/create_id_to_title_mapping.py

echo "Compressing back the WikiData dump file."
bzip2 -z "$wikidata_dump"