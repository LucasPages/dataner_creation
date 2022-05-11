#! /bin/bash

# This file encompasses all the actions to be done with the Wikipedia dump up to before the augmentation process
# and extraction of a corpus.

if [ $# != 1 ]
then
  echo "Usage : ./process_wikipedia_dump.sh wikipedia_dump_path"
  exit 1
fi

wikipedia_dump="$1"

echo "Extracting all Wikipedia articles from the dump (excluding redirect pages)."
./wikipedia_scripts/extract_wikipedia_articles.sh "$wikipedia_dump" "dumps/wikipedia_en.json.bz2"

echo "Adding metadata to the dump and uploading it into a MongoDB collection."
python wikipedia_scripts/add_metadata_articles.py "dumps/wikipedia_en.json.bz2"

echo "Processing the text from the Wikipedia articles and dividing the dump into 3 more manageable MongoDB collections."
python wikipedia_scripts/process_dump.py 8