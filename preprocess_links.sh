#!/bin/bash

if [ "$#" != 1 ]
then
	echo "Usage : ./html_to_annot.sh wikipedia_dump"
	exit 1
fi

dump="$1"

perl -i -pe 's|<a href=\\"\\">.*?</a>||g' "$dump"/*
perl -i -pe 's|<a href=\\"[^"]+?\\"></a>||g' "$dump"/*
perl -i -pe 's|<a href=\\"(.*?)\\">(.*?)<\/a>|[\2][\1]|g' "$dump"/*

