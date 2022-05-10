import argparse
import yaml
import pymongo
import entity_utils

import multiprocessing
from tqdm import tqdm

parser = argparse.ArgumentParser()

parser.add_argument("config", help="Path to the YAML extraction configuration file.")
parser.add_argument("workers", type=int, help="Number of workers to use for processing.", default=8)
parser.add_argument("output_file", help="Path to which the corpus will be extracted.")

args = parser.parse_args()


def extract_sentence(tokens_list, mentions_list):
    begin_indices = dict()
    for mention_iter in mentions_list:
        begin_indices[str(mention_iter["begin"])] = mention_iter

    new_sentence = []
    end_index = -1
    for index, token in enumerate(tokens_list):
        if index == end_index:
            new_sentence.append("]")

        if str(index) in begin_indices:
            ne_class = begin_indices[str(index)]["ne_class"]
            end_index = begin_indices[str(index)]["end"]
            new_sentence.extend(["[", ne_class])

        new_sentence.append(token)

    if end_index == len(tokens_list):
        new_sentence.append("]")

    return " ".join(new_sentence)


def process_article(process_q, writing_q, config_p):
    client_w = pymongo.MongoClient("localhost", 27017)
    db_w = client_w.wikipedia

    collection_tokens = db_w["dump_tokens"]
    coll_w = db_w[args.collection]

    while True:
        article_id_p = process_q.get()

        count_anchor = 0
        count_random = 0
        
        if article_id_p == "exit":
            break

        sentences = list(collection_tokens.find({"article_id": article_id_p}).sort([("sent_index", 1)]))

        sentences_article = []
        for sentence_tokens in sentences:
            mentions_sentence = list(coll_w.find({"article_id": article_id_p,
                                                  "sent_index": sentence_tokens["sent_index"]})
                                     .sort([("begin", 1)]))

            if not mentions_sentence:
                extracted_sentence = extract_sentence(sentence_tokens["tokens"], [])
                sentences_article.append(extracted_sentence)
                continue

            mentions_set = entity_utils.EntitySet(mentions_sentence, config_p)
            mentions_set = entity_utils.EntitySet(mentions_set.only_keep_entities_in_config(coll_w), config_p)
            mentions_set = entity_utils.EntitySet(mentions_set.filter_same_span_entities(), config_p)

            overlapping_pairs, overlapping_entities, non_overlapping_entities = mentions_set.find_overlapping_entities()

            correct_mentions = []
            correct_mentions.extend(non_overlapping_entities)

            while overlapping_pairs:
                chosen_entities = []

                for index, ent in enumerate(overlapping_pairs):
                    entity_pair = entity_utils.EntityPair(ent[0][1], ent[1][1], config_p)

                    if config_p["anchor_priority"] and entity_pair.one_is_anchor() and not entity_pair.same_object():
                        count_anchor += 1
                    elif entity_pair.same_span() or entity_pair.one_includes_other() or entity_pair.overlap():
                        count_random += 1

                    chosen_entity = entity_pair.choose_entity()
                    chosen_entities.append(chosen_entity)

                mentions_set = entity_utils.EntitySet(chosen_entities, config_p)
                overlapping_pairs, overlapping_entities, non_overlapping_entities = mentions_set\
                    .find_overlapping_entities()

                correct_mentions.extend(non_overlapping_entities)

            extracted_sentence = []
            if args.to == "brackets":
                extracted_sentence = extract_sentence(sentence_tokens["tokens"], correct_mentions)
            elif args.to == "latex":
                extracted_sentence = extract_sentence_to_latex(sentence_tokens["tokens"], correct_mentions)
            sentences_article.append(extracted_sentence)
        writing_q.put((article_id_p, sentences_article, count_anchor, count_random))


def write_article(process_q, writing_q, number_processes, number_documents):
    count_articles = 0
    count_anchor = 0
    count_random = 0

    progress_bar_write = tqdm(total=number_documents, unit="articles", leave=None, mininterval=0, miniters=0)

    output_file = open(args.output_file, "w+")

    while True:
        article_id_w, sentences_w, number_anchor, number_random = writing_q.get()

        count_anchor += number_anchor
        count_random += number_random

        output_file.write(f"ARTICLE {article_id_w}\n")
        for sentence in sentences_w:
            output_file.write(sentence + "\n")
        output_file.write("\n")

        count_articles += 1
        progress_bar_write.update(1)
        if count_articles == number_documents:
            break
    output_file.close()
    
    for index in range(number_processes):
        process_q.put("exit")


if __name__ == "__main__":
    client = pymongo.MongoClient("localhost", 27017)
    wikipedia_db = client.wikipedia

    collection_articles = wikipedia_db.dump_articles
    article_ids = [article["article_id"] for article in collection_articles.find({})]
    doc_count = len(article_ids)

    num_workers = args.workers

    with open(f"{args.config}", "r") as config_file:
        try:
            config = yaml.safe_load(config_file)
        except yaml.YAMLError:
            print(f"Issue with config file {args.config}")

    manager = multiprocessing.Manager()
    processing_queue = manager.Queue(5000)
    writing_queue = manager.Queue(5000)

    pool = multiprocessing.Pool(processes=num_workers - 1, initializer=process_article, initargs=(processing_queue,
                                                                                                  writing_queue,
                                                                                                  config))

    writing_process = multiprocessing.Process(target=write_article,
                                              args=(processing_queue, writing_queue, num_workers,
                                                    doc_count))
    writing_process.start()

    for article_id in article_ids:
        processing_queue.put(article_id)

    writing_process.join()
    writing_process.close()

    pool.close()
    pool.join()

    print("Program completed.")

