import pymongo
import argparse
import bz2
import json
import random


parser = argparse.ArgumentParser()

parser.add_argument("wikipedia_dump", help="Path to the Wikipedia dump to add the metadata to.")
parser.add_argument("output_file", help="Path to the output file containing the updated dump.")

args = parser.parse_args()


if __name__ == "__main__":
    client = pymongo.MongoClient()

    mappings_db = client.mappings
    title_to_id_coll = mappings_db.title_to_id

    wikidata_db = client.wikidata
    wikidata_items_coll = wikidata_db.wikidata_items

    neckar_db = client.neckar_results
    neckar_results_coll = neckar_db.entities

    wikipedia_dump = args.wikipedia_dump

    print("Counting articles...")

    articles_counter = 0
    with bz2.open(wikipedia_dump, "r") as dump_file:
        for article in dump_file:
            articles_counter += 1

    print("Processing...")
    progress_bar = tqdm(total=doc_count, unit="items", leave=None, mininterval=0, miniters=0)

    with bz2.open(args.output, "w") as output_file:
        with bz2.open(wikipedia_dump, "r") as dump_file:
            for article in dump_file:
                article_info = json.loads(article.decode("utf-8"))

                wikidata_id = title_to_id_coll.find_one({title: article_info["title"]})
                if wikidata_id is None:
                    continue
                try:
                    aliases = [alias["value"] for alias in wikidata_items_coll.find_one(
                        {"id": wikidata_id})["aliases"]["en"]]
                except KeyError:
                    aliases = []
                ner_class = random.choice([result["neClass"] for result in neckar_results_coll.find({"id": wikidata_id})])
                if not ner_class:
                    ner_class = "MISC"

                article_info["wikidata_id"] = wikidata_id
                article_info["aliases"] = aliases
                article_info["ne_class"] = ner_class

                output_file.write(json.dumps(article_info).strip() + "\n")
                progress_bar.update(1)

    print("Program completed.")