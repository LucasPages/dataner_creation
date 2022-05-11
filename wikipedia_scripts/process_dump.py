import argparse
import pymongo
import multiprocessing
from tqdm import tqdm
import re
from blingfire import text_to_words
import spacy
from urllib.parse import unquote

"""This script takes the Wikipedia dump collection previously uploaded into MongoDB by the 'add_metadata_to_dump.py 
script', processes its text and makes it into 3 MongoDB collections : 
    * dump_articles : metadata about a given article (title, ner class, ...)
    * dump_tokens   : contains all the sentences of the Wikipedia dump
    * dump_mentions : contains all the mentions of named entities of the dump
"""


parser = argparse.ArgumentParser()

parser.add_argument("workers", type=int, help="Number of workers to use for processing articles.")

args = parser.parse_args()


class Entity:

    def __init__(self, info, sent_index, article_info, collection_dump):
        self.article_id = article_info["id"]
        self.article_title = article_info["title"]
        self.sent_index = sent_index

        self.begin_index = info[0]
        self.end_index = info[1]
        self.sent_index = sent_index
        self.mention_title = unquote(info[2][0].upper() + info[2][1:])
        self.ne_class = self.get_class(collection_dump)

    def make_mention(self):
        if self.ne_class is None:
            return -1
        return {"article_title": self.article_title, "article_id": self.article_id, "sent_index": self.sent_index,
                "begin": self.begin_index, "end": self.end_index, "mention_title": self.mention_title,
                "ne_class": self.ne_class, "technique": "anchor"}

    def get_class(self, collection_dump):
        article_info = collection_dump.find_one({"title": self.mention_title})
        if article_info is not None:
            return article_info["ne_class"]
        return None


class Article:

    def __init__(self, article_info):
        self.article = article_info
        self.article["id"] = int(self.article["id"])
        self.text = self.process_links()
        self.sentences = self.segment_text()
        self.tokens, self.entities = self.process_text()

    def process_links(self):
        tmp_string = self.article['text'].replace("&lt;", "<").replace("&gt;", ">").replace(u"\u00ab", "<") \
            .replace(u"\u00bb", ">").replace("[", "").replace("]", "")
        tmp_string = re.sub("([^\[](\[)[^\[]|[^\]](\])[^\]])", "", tmp_string)
        processed_string = re.sub("<a href=\"(.*?)\">((.|\n)*?)<\/a>", r"[\2][\1]", tmp_string)

        return re.sub("\[\[((.|\n)+?)\]\]", r"[\1][\1]", processed_string)

    def segment_text(self):
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(self.text, disable=["tagger", "attribute_ruler", "lemmatizer", "ner"])
        return [sent.text.strip() for sent in doc.sents if sent.text.strip() != ""]

    def process_text(self):
        tokens = []
        entities = []

        for index_sentence, sentence in enumerate(self.sentences):
            tokenized_sentence = text_to_words(sentence).split(" ")
            tokens_sentence = []
            entities_sentence = []

            begin_index = end_index = 0
            in_info = False
            mention_title = ""

            index_new_sentence = 0
            for index_token, token in enumerate(tokenized_sentence):
                if token == "[":
                    if not in_info:
                        begin_index = index_new_sentence
                    continue
                elif token == "]" and not in_info:
                    end_index = index_new_sentence
                    in_info = True
                    continue
                elif token == "]" and in_info:
                    in_info = False
                    entities_sentence.append((begin_index, end_index, mention_title))
                    mention_title = ""
                    continue
                if token != "[" and in_info:
                    mention_title += token
                    continue
                tokens_sentence.append(token)
                index_new_sentence += 1
            tokens.append((tokens_sentence, index_sentence))
            entities.append((entities_sentence, index_sentence))

        return tokens, entities

    def get_mentions(self, collection_dump):
        mentions = []
        for entity_sent in self.entities:
            sent_index = entity_sent[1]
            entities_list = entity_sent[0]

            for entity in entities_list:
                entity_obj = Entity(entity, sent_index, self.article, collection_dump)
                res = entity_obj.make_mention()
                if res != -1:
                    mentions.append(res)

        return mentions

    def get_article_dict(self):
        article_dict = self.article.copy()

        article_dict["article_title"] = self.article["title"]
        article_dict.pop("title")

        article_dict["article_id"] = self.article["id"]
        article_dict.pop("id")

        article_dict.pop("text")

        return article_dict

    def get_tokens_dict(self):
        tokens_dicts = []

        for token_list in self.tokens:
            sent_index = token_list[1]
            tokens = token_list[0]

            tokens_dict = {"article_title": self.article["title"], "article_id": self.article["id"],
                           "sent_index": sent_index, "tokens": tokens}
            tokens_dicts.append(tokens_dict)

        return tokens_dicts


def process_article(processing_q, writing_q):
    client_p = pymongo.MongoClient("localhost", 27017)
    wikipedia_db_p = client_p.wikipedia
    dump_coll_p = wikipedia_db_p.dump_with_metadata

    while True:
        article_info = processing_q.get()

        if article_info == "kill":
            break

        article_obj = Article(article_info)

        article_dict = article_obj.get_article_dict()
        token_dicts = article_obj.get_tokens_dict()
        mention_dicts = article_obj.get_mentions(dump_coll_p)

        writing_q.put((article_dict, token_dicts, mention_dicts))


def write_processed_article(process_q, writing_q, number_documents, num_processes):
    client_wikipedia = pymongo.MongoClient("localhost", 27017)
    db_wikipedia = client_wikipedia.wikipedia

    collection_articles = db_wikipedia[f"dump_articles"]
    collection_tokens = db_wikipedia[f"dump_tokens"]
    collection_mentions = db_wikipedia[f"dump_mentions"]

    collection_articles.drop()
    collection_tokens.drop()
    collection_mentions.drop()

    print("Writing progress bar :")
    progress_bar_write = tqdm(total=number_documents, unit="articles", leave=None, mininterval=0, miniters=0)

    document_count = 0
    while True:
        article_dict, token_dicts, mention_dicts = writing_q.get()

        collection_articles.insert_one(article_dict)
        for token_dict in token_dicts:
            collection_tokens.insert_one(token_dict)
        for mention_dict in mention_dicts:
            collection_mentions.insert_one(mention_dict)

        progress_bar_write.update(1)
        document_count += 1

        if document_count == number_documents:
            break
    progress_bar_write.close()

    print("Collections created.")
    print("Creating indexes...")

    collection_articles.create_index([("article_title", 1)])
    collection_articles.create_index([("article_id", 1)])

    collection_tokens.create_index([("article_id", 1), ("sent_index", 1)])
    collection_tokens.create_index([("article_id", 1)])

    collection_mentions.create_index([("article_id", 1), ("sent_index", 1)])
    collection_mentions.create_index([("article_id", 1)])

    print("All indices have been created.")
    print("Terminating all processes.")

    for process_number in range(num_processes):
        process_q.put("kill")


if __name__ == "__main__":
    num_workers = args.workers
    print(f"Processing collection with {num_workers} processes.")

    client = pymongo.MongoClient("localhost", 27017)

    wikipedia_db = client.wikipedia

    dump_with_metadata_coll = wikipedia_db.dump_with_metadata
    doc_count = dump_with_metadata_coll.count_documents({})

    manager = multiprocessing.Manager()

    # Setting a maxsize for the queues is important to control memory consumption
    processing_queue = manager.Queue(2000)
    writing_queue = manager.Queue(2000)

    # creating Pool for processing units
    pool = multiprocessing.Pool(processes=num_workers - 1, initializer=process_article, initargs=(processing_queue,
                                                                                                  writing_queue))
    # creating the writing process
    writing_process = multiprocessing.Process(target=write_processed_article, args=(processing_queue, writing_queue,
                                                                                    doc_count, num_workers))
    writing_process.start()

    for article in dump_with_metadata_coll.find({}):
        processing_queue.put(article)

    writing_process.join()
    writing_process.close()

    pool.close()
    pool.join()

    print("Program completed.")
