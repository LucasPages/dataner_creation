import pymongo
import argparse
import bz2


def upload_mapping(wikidata_item, collection):
    wikidata_id = wikidata_item["id"]
    try:
        enwiki_title = wikidata_item["sitelinks"]["enwiki"]["title"]
    except KeyError:
        return

    collection.insert_one({"title": enwiki_title, "wikidata_id": wikidata_id})


if __name__ == "__main__":
    client = pymongo.MongoClient("localhost", 27017)

    wikidata_db = client.wikidata
    wikidata_items_coll = wikidata_db.wikidata_items

    mappings_db = client.mappings
    title_to_id_mapping_coll = mappings_db.title_to_id

    title_to_id_mapping_coll.drop()

    for item in wikidata_items_coll.find({}):
        upload_mapping(item, title_to_id_mapping_coll)

    title_to_id_mapping_coll.create_index("title")
    title_to_id_mapping_coll.create_index("wikidata_id")
