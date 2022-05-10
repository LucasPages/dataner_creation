#!/usr/bin/env bash
cd src/
echo NECKAR loading dump to MongoDB
python3 WD2DB.py
echo -----------------------------
echo NECKAR extracting NEs from dump
python3 NECKAr_main.py
echo -----------------------------
echo NECKAR extracting links to LOD
python3 create_LOD_lists.py
echo NECKAR: DONE