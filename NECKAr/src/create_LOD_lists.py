#! /usr/bin/env python3
# This Python file uses the following encoding: utf-8

__author__ = 'jgeiss'


#############################################################################
# authors: Johanna Geiß, Heidelberg University, Germany                     #
# email: geiss@informatik.uni-heidelberg.de                                 #
# Copyright (c) 2017 Database Research Group,                               #
#               Institute of Computer Science,                              #
#               University of Heidelberg                                    #
#   Licensed under the Apache License, Version 2.0 (the "License");         #
#   you may not use this file except in compliance with the License.        #
#   You may obtain a copy of the License at                                 #
#                                                                           #
#   http://www.apache.org/licenses/LICENSE-2.0                              #
#                                                                           #
#   Unless required by applicable law or agreed to in writing, software     #
#   distributed under the License is distributed on an "AS IS" BASIS,       #
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.#
#   See the License for the specific language governing permissions and     #
#   limitations under the License.                                          #
#############################################################################
# last updated 21.3.2017 by Johanna Geiß

from pymongo import *
from pymongo import errors
import configparser

def read_config(config):
    """Reads the configuration file NECKAr.cfg

    :param config: ConfigParser Object
    :return: input collection, list of output collections  and the dump collection
    """
    host = config.get('Database', 'host')
    port=config.getint('Database','port')

    auth = config.getboolean('Database','auth')
    user=config.get('Database','user')
    password=config.get('Database','password')

    try:
        client=MongoClient(host,port)
    except errors.ConnectionFailure:
        print("Connection to the database cannot be made. Plase check the config file")


    db_read_name=config.get('Database','db_write') # where info was writtenn to in the first step
    db_in=client[db_read_name]               #Database from where information is extracted
    db_all_name=config.get('Database','db_dump') # where info was writtenn to in the first step
    db_all=client[db_all_name]

    input_collection_name=config.get('Database','collection_write')
    input_collection=db_in[input_collection_name]
    all_collection_name = config.get('Database','collection_dump')
    all_collection=db_all[all_collection_name]

    languages = config.items( "LODLinks" )
    output_coll_list={}
    for lang, coll_name in languages:
        output_coll_list[lang]=db_in[coll_name]
    print("Config File read in")


    return input_collection, output_coll_list, all_collection



def get_linksfromWikidata(WD_id, entry,collection):
    """ get links to other Databases from dumo

    :param WD_id: Wikidata id of enity <class 'string'>
    :param entry: entity object <class 'dict'>
    :param collection: collection to search in
    :return: entry <class 'dict'>
    """
    entry_org = collection.find_one({"id":WD_id})
    if entry_org:
        if "P345" in entry_org["claims"]:
            mainsnak=entry_org["claims"]["P345"][0]["mainsnak"]
            if mainsnak["snaktype"] == "value":
                entry["IMDB_id"] = mainsnak["datavalue"]["value"]
            else:
                print(entry["WD_id"], "P345 value missing")
        if "P434" in entry_org["claims"]:
            mainsnak=entry_org["claims"]["P434"][0]["mainsnak"]
            if mainsnak["snaktype"] == "value":
                entry["MusicBrainzArtist_id"] = mainsnak["datavalue"]["value"]
            else:
                print(entry["WD_id"], "P434 value missing")
        if "P227" in entry_org["claims"]:
            mainsnak=entry_org["claims"]["P227"][0]["mainsnak"]
            if mainsnak["snaktype"] == "value":
                entry["GND_id"] = mainsnak["datavalue"]["value"]
            else:
                print( entry["WD_id"], "P227 value missing")
        if "P1566" in entry_org["claims"]:
            mainsnak=entry_org["claims"]["P1566"][0]["mainsnak"]
            if mainsnak["snaktype"] == "value":
                entry["geonames_id"]= mainsnak["datavalue"]["value"]
            else:
                print(entry["WD_id"], "P1566 value missing")
        if "P402" in entry_org["claims"]:
            mainsnak=entry_org["claims"]["P402"][0]["mainsnak"]
            if mainsnak["snaktype"] == "value":
                entry["OSM_id"] = mainsnak["datavalue"]["value"]
            else:
                print(entry["WD_id"], "P402 value missing")
    return entry

def create_LODdictionary(entry,myclient,lang="en",):
    """ creates url to Wikidata, Wikipedia an dbpedia (the last depends on langauge) and gets links to LOD
    calls function 'get_linksfromWikidata'


    :param entry: entity object <class 'dict'>
    :param myclient: connection to db
    :param lang: language <class 'string'>
    :return: nothing but adds information to entry
    """
    entry["WD_id_URL"] = "http://www.wikidata.org/wiki/"+entry["WD_id"]
    entry["WP_id_URL"] = "http://"+lang+".wikipedia.org/wiki/"+entry["WP_id"].replace(" ","_")
    entry = get_linksfromWikidata(entry["WD_id"], entry, myclient)
    if lang == "en":
        entry["dbpedia_URL"] = "http://dbpedia.org/resource/"+entry["WP_id"].replace(" ","_")
    else:
        if "WP_id_en" in entry:
            entry["dbpedia_URL_en"] = "http://dbpedia.org/resource/"+entry["WP_id_en"].replace(" ","_")
        entry["dbpedia_URL"] = "http://"+lang+".dbpedia.org/resource/"+entry["WP_id"].replace(" ","_")


if __name__ == "__main__":
    """NECKAr: Named Entity Classifier for Wikidata

    this tool categorizes Wikidata items into 6 categories
    the parameters are set in NECKAr.cfg """

    config = configparser.ConfigParser()
    config.read('../NECKAr.cfg')

    input_collection, output_list, all_coll = read_config(config)
    print(type(output_list))

    for lang, output_coll in output_list.items():
        #print(lang)
        #print(output_coll)
        for entity in input_collection.find({lang+"_sitelink":{"$exists":True}}).sort("id",1):
            entry={}
            entry["label"] = entity["norm_name"]
            entry["neClass"] = entity["neClass"]
            entry["WD_id"] = entity["id"]
            entry["WP_id"] = entity[lang+"_sitelink"]

            if lang!= "en" and "en_sitelink" in entity:
                entry["WP_id_en_URL"] = "http://en.wikipedia.org/wiki/"+entity["en_sitelink"].replace(" ","_")

            create_LODdictionary(entry, all_coll, lang)

            output_coll.insert_one(entry)






