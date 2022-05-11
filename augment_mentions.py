import argparse

import pymongo
from blingfire import text_to_words

import multiprocessing
from tqdm import tqdm

import entity_utils

"""This script is used to create new named entity mentions in the mentions collections."""

parser = argparse.ArgumentParser()

parser.add_argument("workers", type=int, help="Number of workers to use for processing.", default=8)

args = parser.parse_args()


class Sentence:

    def __init__(self, sentence):
        self.sentence = sentence
        self.tokens = sentence["tokens"]

    def check_for_subsequence(self, substring):
        subsequence = text_to_words(substring).split(" ")

        return [(index_tokens, index_tokens + len(subsequence)) for index_tokens in range(len(self.tokens)) if
                [token.lower() for token in self.tokens[index_tokens:index_tokens + len(subsequence)]] ==
                [token.lower() for token in subsequence]]


def augment_article(art_id, technique, test_m, coll_mentions, coll_articles):
    article_info = coll_articles.find_one({"article_id": art_id})

    entities_to_augment = []
    if technique == "outlinks":
        entities_to_augment = test_m.find({"article_id": art_id, "technique": "anchor"})
    elif technique == "alias":
        entities_to_augment = test_m.find({"article_id": art_id, "technique": "anchor"})
    elif technique == "alias-title":
        entities_to_augment = [{"_id": article_info["_id"], "mention_title": article_info["article_title"],
                                "ne_class": article_info["ne_class"], "origin": article_info["_id"],
                                "sent_index": -1, "origin_sent": -1, "technique": "alias-title"}]

    new_entities = []
    if technique == "title-expansion":
        new_entities.append({"mention_title": article_info["article_title"], "ne_class": article_info["ne_class"]})

    for entity in entities_to_augment:
        mention = entity_utils.Mention(entity)
        if technique == "outlinks":
            new_entities.extend(mention.get_outlinks(coll_mentions))
        elif technique == "alias" or technique == "alias-title":
            new_entities.extend(mention.get_aliases(coll_articles))

    return new_entities


def write_article(art_id, new_entities, technique, coll_tokens):
    sentences = list(coll_tokens.find({"article_id": art_id}))

    new_mentions = []
    for new_entity in new_entities:
        for sentence in sentences:
            sentence_obj = Sentence(sentence)

            if technique == "alias" or technique == "alias-title":
                sublist_res = sentence_obj.check_for_subsequence(new_entity["alias"])
            else:
                sublist_res = sentence_obj.check_for_subsequence(new_entity["mention_title"])

            if sublist_res:
                for sublist in sublist_res:
                    new_mention = {"article_title": sentence["article_title"], "article_id": art_id,
                                   "sent_index": sentence["sent_index"], "begin": sublist[0], "end": sublist[1],
                                   "mention_title": new_entity["mention_title"], "ne_class": new_entity["ne_class"],
                                   "technique": technique}

                    if technique in ["outlinks", "alias"]:
                        new_mention["origin"] = new_entity["origin"]
                        new_mention["origin_sent"] = new_entity["origin_sent"]

                    if technique == "alias":
                        new_mention["origin_technique"] = new_entity["origin_technique"]

                    if new_mention not in new_mentions:
                        new_mentions.append(new_mention)
    return new_mentions


def process_article(processing_q, writing_q):
    client_p = pymongo.MongoClient("localhost", 27017)
    db_p = client_p.wikipedia

    dump_collection_p = db_p["dump_mentions"]
    
    collection_tokens_p = db_p["dump_tokens"]
    collection_mentions_p = db_p["dump_mentions"]
    collection_articles_p = db_p["dump_articles"]
    
    methods = ["title-expansion", "alias-title", "outlinks", "alias"]
    dump_collection_p.delete_many({"technique": {"$in": methods}})

    while True:
        article_id_p = processing_q.get()

        if article_id_p == "exit":
            break

        new_mentions = []

        for method in methods:
            new_ents = augment_article(article_id_p, method, dump_collection_p, collection_mentions_p,
                                       collection_articles_p)
            created_mentions = write_article(article_id_p, new_ents, method, collection_tokens_p)
            new_mentions.extend(created_mentions)

        writing_q.put(new_mentions)


def write_mentions(writing_q, process_q, num_processes, number_documents):
    client_w = pymongo.MongoClient("localhost", 27017)
    db_w = client_w.wikipedia
    
    collection_write = db_w["dump_mentions"]
    progress_bar_write = tqdm(total=number_documents, unit="articles", leave=None, mininterval=0, miniters=0)
    
    count_articles = 0
    while True:
        new_mentions = writing_q.get()

        try:
            collection_write.insert_many(new_mentions)
        except TypeError:
            pass

        count_articles += 1
        progress_bar_write.update(1)
        if count_articles == number_documents:
            break
    
    for index in range(num_processes):
        process_q.put("exit")

    collection_write.drop_index("article_id_1_sent_index_1")
    collection_write.create_index([("article_id", 1), ("sent_index", 1)])


if __name__ == "__main__":
    client = pymongo.MongoClient("localhost", 27017)
    db = client.wikipedia
    dump_collection = db["dump_mentions"]

    article_ids = list(dump_collection.distinct("article_id"))
    doc_count = len(article_ids)

    num_workers = args.workers
    print(f"Processing collection with {num_workers} processes.")

    manager = multiprocessing.Manager()
    processing_queue = manager.Queue(5000)
    writing_queue = manager.Queue(5000)

    pool = multiprocessing.Pool(processes=num_workers - 1, initializer=process_article, initargs=(processing_queue,
                                                                                                  writing_queue))

    writing_process = multiprocessing.Process(target=write_mentions,
                                              args=(writing_queue, processing_queue, num_workers,
                                                    doc_count))
    writing_process.start()

    for article_id in article_ids:
        processing_queue.put(article_id)

    writing_process.join()
    writing_process.close()

    pool.close()
    pool.join()

    print("Program completed.")
