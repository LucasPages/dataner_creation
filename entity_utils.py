import random
from nltk.corpus import stopwords


class EntityPair:

    def __init__(self, entity1, entity2, config):
        self.entity1 = entity1
        self.entity2 = entity2
        self.config = config
        
    def choose_entity(self):
        if self.same_object():
            return self.entity1
        elif self.config["anchor_priority"] and self.one_is_anchor():
            return self.get_anchor()
        elif self.same_span():
            return self.choose_from_same_span()
        elif self.one_includes_other():
            return self.choose_from_inclusion()
        elif self.overlap():
            return self.choose_from_overlap()
        return -1

    def same_span(self):
        if self.entity1["begin"] == self.entity2["begin"] and self.entity1["end"] == self.entity2["end"]:
            return True
        return False

    def one_is_anchor(self):
        return self.entity1["technique"] == "anchor" or self.entity2["technique"] == "anchor"

    def get_anchor(self):
        if self.entity1["technique"] == "anchor":
            return self.entity1
        elif self.entity2["technique"] == "anchor":
            return self.entity2

    def choose_from_same_span(self):
        # technique_ranking = {"anchor": 0, "title-expansion": 1, "outlinks-sentence": 2, "outlinks-article": 3,
        #                      "alias-sentence": 4, "alias-article": 5, "fusion": 6}
        # technique_ranking = ["anchor", "title-expansion", "alias-title", "outlinks-sentence", "alias-sentence",
        #                      "outlinks-article", "alias-article", "consecutive-fusion", "overlap-fusion"]

        technique_ranking = ["anchor", "title-expansion", "alias-title", "outlinks", "alias",
                             "consecutive-fusion", "overlap-fusion"]

        if not self.same_technique():
            if technique_ranking.index(self.entity1["technique"]) < technique_ranking.index(self.entity2["technique"]):
                return self.entity1
            return self.entity2
        return self.entity1

    def one_includes_two(self):
        return self.entity1["begin"] <= self.entity2["begin"] < self.entity2["end"] <= self.entity1["end"]

    def two_includes_one(self):
        return self.entity2["begin"] <= self.entity1["begin"] < self.entity1["end"] <= self.entity2["end"]

    def one_includes_other(self):
        return self.one_includes_two() or self.two_includes_one()
    
    def choose_from_inclusion(self):
        if self.config["inclusion"] == "bigger":
            return self.get_longer_span()
        elif self.config["inclusion"] == "shorter":
            return self.get_shorter_span()
        elif self.config["inclusion"] == "random":
            return random.choice([self.entity1, self.entity2])

    def overlap(self):
        return (self.entity1["begin"] <= self.entity2["begin"] < self.entity1["end"] <= self.entity2["end"]) or \
               (self.entity2["begin"] <= self.entity1["begin"] < self.entity2["end"] <= self.entity1["end"])

    def choose_from_overlap(self):
        if self.config["overlap"] == "bigger":
            return self.get_longer_span()
        elif self.config["overlap"] == "shorter":
            return self.get_shorter_span()
        elif self.config["overlap"] == "random":
            return random.choice([self.entity1, self.entity2])

    def get_longer_span(self):
        length_entity1 = len(range(self.entity1["begin"], self.entity1["end"]))
        length_entity2 = len(range(self.entity2["begin"], self.entity2["end"]))

        if length_entity1 >= length_entity2:
            return self.entity1
        return self.entity2

    def get_shorter_span(self):
        length_entity1 = len(range(self.entity1["begin"], self.entity1["end"]))
        length_entity2 = len(range(self.entity2["begin"], self.entity2["end"]))

        if length_entity1 <= length_entity2:
            return self.entity1
        return self.entity2

    def same_class_and_link(self):
        return self.same_link() and self.same_class()

    def same_link(self):
        return self.entity1["link"] == self.entity2["link"]

    def same_class(self):
        return self.entity1["ne_class"] == self.entity2["ne_class"]

    def same_technique(self):
        if self.entity1["technique"] != self.entity2["technique"]:
            return False
        return True

    def fuse(self, technique):
        fused_entity = self.entity1.copy()

        if self.entity1["begin"] < self.entity2["begin"]:
            fused_entity["begin"] = self.entity1["begin"]
            fused_entity["end"] = self.entity2["end"]
        else:
            fused_entity["begin"] = self.entity2["begin"]
            fused_entity["end"] = self.entity1["end"]

        fused_entity["technique"] = technique
        fused_entity["origin"] = [entity["_id"] for entity in [self.entity1, self.entity2]]

        return fused_entity

    def one_follows_two(self):
        return self.entity1["begin"] == self.entity2["end"]

    def two_follows_one(self):
        return self.entity2["begin"] == self.entity1["end"]

    def are_consecutive(self):
        return self.one_follows_two() or self.two_follows_one()

    def share_one_word(self):
        return self.entity1["end"] - 1 == self.entity2["begin"] or self.entity2["end"] - 1 == self.entity1["begin"]

    def are_fusable_consecutive(self):
        return self.are_consecutive() and self.same_class()

    def are_fusable_overlap(self):
        return self.share_one_word() and self.same_class()

    def same_object(self):
        return self.entity1 == self.entity2

    def same_origin(self):
        if "origin" not in self.entity1 or "origin" not in self.entity2:
            return False
        return self.entity1["origin"] == self.entity2["origin"]

    def same_mention(self):
        return self.same_span() and self.same_class_and_link() and self.same_technique() and self.same_origin()

    def get_entities(self):
        return self.entity1, self.entity2

    def get_entity1(self):
        return self.entity1

    def get_entity2(self):
        return self.entity2


class EntitySet:

    def __init__(self, entities, config):
        self.list = list({dict_entry['_id']: dict_entry for dict_entry in entities}.values())
        self.config = config

    def filter_same_span_entities(self):
        sentence_spans = []
        new_entities = []

        for index, mention_iter in enumerate(self.list):
            if (mention_iter["begin"], mention_iter["end"]) not in sentence_spans:
                sentence_spans.append((mention_iter["begin"], mention_iter["end"]))
                new_entities.append(mention_iter)

        return new_entities

    def filter_multiclass(self, neckar_coll):
        new_entities = []
        counter = 0

        for index, mention_iter in enumerate(self.list):
            neckar_info = set([info["neClass"] for info in neckar_coll.find({"en_sitelink": mention_iter["link"]})])
            if len(neckar_info) <= 1:
                new_entities.append(mention_iter)
            else:
                counter += 1

        return new_entities, counter

    def find_overlapping_entities(self):
        overlapping_pairs = []
        overlapping_unrolled = [False] * len(self.list)

        for index, mention_iter in enumerate(self.list):
            if index == len(self.list) - 1:
                break
            for index_sublist in range(index + 1, len(self.list)):
                overlapping = range(max(mention_iter["begin"], self.list[index_sublist]["begin"]),
                                    min(mention_iter["end"], self.list[index_sublist]["end"]))
                if overlapping:
                    overlapping_pairs.append(((index, mention_iter), (index_sublist, self.list[index_sublist])))
                    overlapping_unrolled[index] = True
                    overlapping_unrolled[index_sublist] = True

        non_overlapping = []
        for index, mention_iter in enumerate(self.list):
            if not overlapping_unrolled[index]:
                non_overlapping.append(mention_iter)

        return overlapping_pairs, overlapping_unrolled, non_overlapping

    def find_consecutive_fusable_entities(self):
        fusable_pairs = []

        for index, mention_iter in enumerate(self.list):
            if index == len(self.list) - 1:
                break
            for index_sublist in range(index + 1, len(self.list)):
                entity_pair = EntityPair(mention_iter, self.list[index_sublist], self.config)
                if entity_pair.are_fusable_consecutive():
                    fusable_pairs.append(entity_pair)

        fused_pairs = []
        for entity_pair in fusable_pairs:
            if entity_pair.fuse("consecutive-fusion") not in self.list:
                fused_pairs.append(entity_pair.fuse("consecutive-fusion"))

        return fused_pairs
    
    def find_overlap_fusable_entities(self):
        fusable_pairs = []

        for index, mention_iter in enumerate(self.list):
            if index == len(self.list) - 1:
                break
            for index_sublist in range(index + 1, len(self.list)):
                entity_pair = EntityPair(mention_iter, self.list[index_sublist], self.config)
                if entity_pair.are_fusable_overlap():
                    fusable_pairs.append(entity_pair)

        fused_pairs = []
        for entity_pair in fusable_pairs:
            fused_entity = entity_pair.fuse("overlap-fusion")
            fused_pairs.append(fused_entity)

            if entity_pair.entity1 in self.list:
                self.list.remove(entity_pair.entity1)
            if entity_pair.entity2 in self.list:
                self.list.remove(entity_pair.entity2)

        return fused_pairs

    def only_keep_entities_in_config(self, collection):
        techniques_to_keep = ["anchor"]

        if self.config["alias-title"]:
            techniques_to_keep.append("alias-title")
        if self.config["title-expansion"]:
            techniques_to_keep.append("title-expansion")
        if self.config["outlinks"]:
            techniques_to_keep.append(self.config["outlinks"])
        if self.config["alias"]:
            techniques_to_keep.append(self.config["alias"])

        chosen_entities = []

        for entity in self.list:
            if entity["technique"] in techniques_to_keep:
                chosen_entities.append(entity)
            elif entity["technique"] == "outlinks" and self.config["outlinks"]:
                if self.config["outlinks"] == "outlinks-article":
                    chosen_entities.append(entity)
                elif self.config["outlinks"] == "outlinks-sentence" and (entity["sent_index"] == entity["origin_sent"]):
                    chosen_entities.append(entity)
            elif entity["technique"] == "alias" and self.config["alias"]:
                if self.config["alias"] == "alias-article":
                    chosen_entities.append(entity)
                elif self.config["alias"] == "alias-sentence" and (entity["sent_index"] == entity["origin_sent"]):
                    chosen_entities.append(entity)

        return chosen_entities

    def filter_augm_misc(self):
        new_entities = []

        for entity in self.list:
            if entity["ne_class"] == "MISC" and entity["technique"] != "anchor":
                continue
            else:
                new_entities.append(entity)

        return new_entities

    def filter(self, tokens_sentence):
        self.filter_numbers(tokens_sentence)
        self.filter_stopwords(tokens_sentence)

        return self.list

    def filter_numbers(self, tokens_sentence):
        filtered_list = []
        for entity in self.list:
            mention_obj = Mention(entity)
            if not mention_obj.is_number(tokens_sentence):
                filtered_list.append(entity)
        self.list = filtered_list

    def filter_stopwords(self, tokens_sentence):
        filtered_list = []

        for entity in self.list:
            mention_obj = Mention(entity)
            if not mention_obj.is_stopword(tokens_sentence):
                filtered_list.append(entity)
        self.list = filtered_list

    def filter_not_winer(self, articles_winer, collection_articles, collection_mentions):
        filtered_list = []

        for entity in self.list:
            if entity["technique"] == "anchor":
                link_to_recover = entity["link"]
            elif entity["technique"] in ["outlinks", "alias"]:
                link_to_recover = collection_mentions.find_one({"_id": entity["origin"]})["link"]
            else:
                filtered_list.append(entity)
                continue
            article_id_link = collection_articles.find_one({"title": link_to_recover})["article_id"]
            if article_id_link in articles_winer:
                filtered_list.append(entity)

        return filtered_list


class Mention:

    def __init__(self, entity):
        self.entity = entity
        self.link = entity["link"]

    def get_outlinks(self, coll_mentions):
        new_mentions = []
        for entity in coll_mentions.find({"article_title": self.link, "technique": "anchor"}):
            entity["origin"] = self.entity["_id"]
            entity["origin_sent"] = self.entity["sent_index"]
            new_mentions.append(entity)
        return new_mentions

    def get_aliases(self, coll_articles):
        return [{"alias": alias, "link": self.link, "ne_class": self.entity["ne_class"],
                 "origin": self.entity["_id"], "origin_sent": self.entity["sent_index"],
                 "origin_technique": self.entity["technique"]}
                for alias in coll_articles.find_one({"title": self.link})["aliases"]]

    def get_technique(self):
        return self.entity["technique"]

    def get_origin(self, coll_mentions):
        if self.entity["technique"] != "anchor":
            return coll_mentions.find_one({"_id": self.entity["origin"]})
        return "anchor"

    def is_number(self, tokens_sentence):
        mention_string = "".join(tokens_sentence[self.entity["begin"]: self.entity["end"]])

        return mention_string.replace(",", "").replace(".", "").isdigit()

    def is_stopword(self, tokens_sentence):
        stopwords_list = set(stopwords.words("english"))

        mention_sublist = tokens_sentence[self.entity["begin"]: self.entity["end"]]
        if len(mention_sublist) > 1:
            return False
        try:
            if mention_sublist[0].lower() in stopwords_list:
                return True
        except IndexError:
            pass
        return False
