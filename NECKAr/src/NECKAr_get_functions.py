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
#      02.03.2017                                     #
#      last update 21.03.2017 bei Johanna Geiß        #
#######################################################
#This code find all the auxillary information which is to be stored with each entity of all listed categories

######################################################################################################
# Common Fields
######################################################################################################

def get_WDid(json_object):
    """
    Gets Wikidata id of item

    :param json_object: entity object <class 'dict'>
    :return: id <class 'string'>
    """
    id = json_object["id"]
    return id


def get_label(json_object, id):
    """Gets en label of item

    :param json_object: entity object <class 'dict'>
    :param id: Wikidata id  <class 'string'>
    :return: norm_name: label <class 'string'> | None
    """
    norm_name=None
    if "labels" in json_object:
        labels = json_object["labels"]  #labels is a dictionary where the display name for each language is defined
        if "en" in labels:  #default: use English label as normalized name
            norm_name = labels["en"]["value"]
        elif "en-gb" in labels:
            norm_name = labels["en-gb"]["value"]
        elif "en-ca" in labels:
            norm_name = labels["en-ca"]["value"]
        elif "de" in labels:  #if English label does not exists use German
            norm_name = labels["de"]["value"]
        elif labels.values():
            #norm_name=id   						#if no English or German label exists use id
            norm_name = list(labels.values())[0]["value"]
        else:
            norm_name = id
    else:
        norm_name = id
    return norm_name


def get_description(json_obejct):
    """Gets English description of an item

    :param json_obejct: entity object <class 'dict'>
    :return: description <class 'string'> | None
    """
    description = None
    if "descriptions" in json_obejct:
        if "en" in json_obejct["descriptions"]:
            description = json_obejct["descriptions"]["en"]["value"]
    return description


def get_en_sitelink(json_object):
    """Gets link of an item to the English Wikipedia

    :param json_object:  entity object <class 'dict'>
    :return: en_sitelink <class 'string'> | None
    """
    en_sitelink = None
    if "sitelinks" in json_object:
        if "enwiki" in json_object["sitelinks"]:
            en_sitelink = json_object["sitelinks"]["enwiki"]["title"]
    return en_sitelink

def get_de_sitelink(json_object):
    """Gets link of an item to the German Wikipedia

    :param json_object: entity object <class 'dict'>
    :return: de_sitelink <class 'string'> | None
    """
    de_sitelink = None
    if "sitelinks" in json_object:
        if "dewiki" in json_object["sitelinks"]:
            de_sitelink = json_object["sitelinks"]["dewiki"]["title"]
    return de_sitelink
#################################################################################################################
# Common fields written
#################################################################################################################

#################################################################################################################
# Specific Fields for each neClass
#################################################################################################################

#########################
#Person
#########################

def get_datebirth(json_object):
    """Gets date of birth of a person
    This function calls the functions get_datelife with thh property P569

    :param json_object: entity object <class 'dict'>
    :return: date ob birth <class 'string'> | None
    """
    return get_datelife(json_object, "P569")

def get_datedeath(json_object):
    """Gets date of death of a person
    This function calls the functions get_datelife with thh property P570

    :param json_object: entity object <class 'dict'>
    :return: date ob death <class 'string'>| None
    """
    return get_datelife(json_object, "P570")


def get_datelife(json_object, P):
    """Gets dates for person
        this only returns a date if it is an explicit date of birth or dead, no latest possible date(P1326) or range (befor/after)

    :param json_object: ntity object <class 'dict'>
    :param P: Property (defines if date of birth (P569) or date of death (P570) is searched)
    :return: date <class 'string'> | None
    """

    value = None
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if P in claims:  #if "claims" contain the property P569= date of birth
            for props in claims[P]:
                if props["mainsnak"]["property"] == P:
                    if "datavalue" in props["mainsnak"]:
                        after = props["mainsnak"]["datavalue"]["value"]["after"]
                        before = props["mainsnak"]["datavalue"]["value"]["before"]
                        if after == before == 0:
                            value = props["mainsnak"]["datavalue"]["value"]["time"]
                            # prefix = value[0]
                            # if prefix == "-":
                            #     prefix = "BC"
                            # else:
                            #     prefix = ""
                            #
                            # cleanedvalue = value[1:].lstrip("0").split("T")[0]
                            # cv = cleanedvalue.split("-")[0]
                            # if cv == "":
                            #     cv = 0
                            # #todo create ISOdate
                            # year = "%04i" % int(cv)
                            # month = cleanedvalue.split("-")[1]
                            # day = cleanedvalue.split("-")[2]
                            # value = prefix + year + "-" + month + "-" + day
    return value

gender_dict = {6581097: "male",
               6581072: "female",
               1097630: "intersex",
               303479: "hermaphrodite",
               189125: "transgender",
               1052281: "transgender female",
               2449503: "transgender male",
               48270: "genderqueer",
               1399232: "fa-afafine",
               3277905: "mahu",
               746411: "kathoey",
               350374: "fakaleiti",
               660882: "hijra"}
def get_gender(json_object):
    """
    Gets gender of person ("P21")

    :param json_object: entity object <class 'dict'>
    :return: gender  <class 'string'>|  <class 'int'> | None
    """
    gender_id=None
    gender=None
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P21" in claims:
            for props in claims["P21"]:
                if props["mainsnak"]["property"] == "P21":
                    if "datavalue" in props["mainsnak"]:
                        gender_id = props["mainsnak"]["datavalue"]["value"]["numeric-id"]
    gender=gender_dict.get(gender_id,gender_id)
    return gender

def get_occupation(json_object):
    """Gets occupation of person ("P106")

    :param json_object: entity object <class 'dict'>
    :return: occupation <class 'string'>
    """
    occupation=[]
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P106" in claims:
            for props in claims["P106"]:
                if props["mainsnak"]["property"] == "P106":
                    if "datavalue" in props["mainsnak"]:
                        occupation.append(props["mainsnak"]["datavalue"]["value"]["numeric-id"])
    return occupation

def get_alias_list(json_object):
    """Gets aliases and other language labels of a person

    :param json_object: entity object <class 'dict'>
    :return: aliaslist (list of strings)
    """
    aliaslist = set([])
    if "labels" in json_object:
        labels = json_object["labels"]
        for lang in labels:  #get language labels
            alias = labels[lang]["value"]
            if len(alias) > 125:
                alias = alias[:125]
            aliaslist.add(alias)

    if "aliases" in json_object:
        aliases = json_object["aliases"]  #get language aliases
        for lang in aliases:
            for aliasentry in aliases[lang]:
                alias = aliasentry["value"]
                if len(alias) > 124:
                    alias = alias[:124]
                aliaslist.add(alias)
    return list(aliaslist)

#################################################################################################
#########################
#Location
#########################
def get_location_inside(json_object):
    """gets the id of the country (P17) and or continent (P30) the enities is in

    :param json_object: entity object <class 'dict'>
    :return: tuple of id of country (in_country) and id of continent (in_continent) (both lists of int)
    """
    in_country=[]
    in_continent=[]
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P17" in claims:         #Claims for country
            for p17entry in claims["P17"]:
                if "datavalue" in p17entry["mainsnak"]:
                    in_country.append(p17entry["mainsnak"]["datavalue"]["value"]["numeric-id"])

        if "P30" in claims:         #Claims for continent
            for p30entry in claims["P30"]:
                if "datavalue" in p30entry["mainsnak"]:
                    in_continent.append(p30entry["mainsnak"]["datavalue"]["value"]["numeric-id"])
    return in_country, in_continent


def get_poi(json_object,country_subclass,settlement_subclass, city_subclass, sea_subclass, river_subclass, mountain_subclass, mountainr_subclass, state_subclass,hgte_subclass):
    """
     gets the location type of the entity

     :param json_object: entity object <class 'dict'>
     :param country_subclass: list of all country (Q6256, Q3624078, Q1763527) subclasses
     :param settlement_subclass: list of all settlement (Q486972) subclasses
     :param city_subclass: list of all city (Q515) subclasses
     :param sea_subclass: list of all sea (Q165) subclasses
     :param river_subclass: list of all river (Q4022) subclasses
     :param mountain_subclass: list of all mountain (Q8502) subclasses
     :param mountainr_subclass: list of all mountain range (Q41437459) subclasses
     :param state_subclass: list of all state (Q7275) subclasses
     :param hgte_subclass: list of all human geographic territorail entity (Q15642541) subclasses
     :return: list of types (list of strings)
    """

    poi=[]
    #subdirectory='subclass_all_loc'
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P31" in claims:
            for p31entry in json_object["claims"]["P31"]:
                if "datavalue" in p31entry["mainsnak"]:
                    if p31entry["mainsnak"]["datavalue"]["value"]["numeric-id"] == 5107: #continent
                        poi.append("Continent")
                    if p31entry["mainsnak"]["datavalue"]["value"]["numeric-id"] in country_subclass:\
                            #write_functions.location_type_object(subdirectory,'subclass_country.txt'): #country
                        poi.append("Country")
                    if p31entry["mainsnak"]["datavalue"]["value"]["numeric-id"] in settlement_subclass: #settlement
                            #write_functions.location_type_object(subdirectory,'subclass_city.txt'): #city
                        poi.append("Settlement")
                    if p31entry["mainsnak"]["datavalue"]["value"]["numeric-id"] in city_subclass:
                            #write_functions.location_type_object(subdirectory,'subclass_city.txt'):
                        poi.append("City")
                    if p31entry["mainsnak"]["datavalue"]["value"]["numeric-id"] in sea_subclass: #Sea
                        poi.append("Sea")
                    if p31entry["mainsnak"]["datavalue"]["value"]["numeric-id"] in river_subclass:
                            #write_functions.location_type_object(subdirectory,'subclass_river.txt'): #river
                        poi.append("River")
                    if p31entry["mainsnak"]["datavalue"]["value"]["numeric-id"] in mountain_subclass:
                            #write_functions.location_type_object(subdirectory,'subclass_mountain.txt'): #mountain
                        poi.append("Mountain")
                    if p31entry["mainsnak"]["datavalue"]["value"]["numeric-id"] in mountainr_subclass:
                            #write_functions.location_type_object(subdirectory,'subclass_mountainrange.txt'): #mountain range
                        poi.append("Mountain Range")
                    if p31entry["mainsnak"]["datavalue"]["value"]["numeric-id"] in state_subclass:
                            #write_functions.location_type_object(subdirectory,'subclass_state.txt'): #State
                        poi.append("State")
                    #if p31entry["mainsnak"]["datavalue"]["value"]["numeric-id"] in POI_subclass:
                            #write_functions.location_type_object(subdirectory,'subclass_location.txt'): #POI
                        #poi.append("POI")
                    if p31entry["mainsnak"]["datavalue"]["value"]["numeric-id"] in hgte_subclass:
                            #write_functions.location_type_object(subdirectory,'subclass_human-geographic-territorial-entity.txt'): #human_geo_territory
                        poi.append("human_geographic_territorial_entity")
    poi=set(poi)
    return list(poi)


def get_coordinate(json_object):
    """gets coordinate location of entity

    :param json_object: entity object <class 'dict'>
    :return: coordinate [long (int), lat (int)] | None
    """
    coordinate=None
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P625" in claims:
            if "datavalue" in json_object["claims"]["P625"][0]["mainsnak"]:
                long = json_object["claims"]["P625"][0]["mainsnak"]["datavalue"]["value"]["longitude"]
                lat = json_object["claims"]["P625"][0]["mainsnak"]["datavalue"]["value"]["latitude"]
                coordinate=[long, lat]
                #coordinate.append(str(json_object["claims"]["P625"][0]["mainsnak"]["datavalue"]\
                #["value"]["latitude"]) +" "+ str(json_object["claims"]["P625"][0]["mainsnak"]\
                #["datavalue"]["value"]["longitude"]))
    return coordinate

def get_population(json_object):
    """gets population of entity

    :param json_object: entity object <class 'dict'>
    :return: population (int) | None
    """
    population=None
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P1082" in claims:
            if "datavalue" in json_object["claims"]["P1082"][0]["mainsnak"]:
                amount=json_object["claims"]["P1082"][0]["mainsnak"]["datavalue"]["value"]["amount"]
                amount=amount[1:]
                unit=json_object["claims"]["P1082"][0]["mainsnak"]["datavalue"]["value"]["unit"]
                if (amount.isdigit() and unit.isdigit()):
                    population=int(amount)*int(unit)

    return population


def get_geonamesID(json_object):
    """gets geonames ID of entity

    :param json_object:  entity object <class 'dict'>
    :return: geonames ID (string)| None
    """
    geonamesID=None
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P1566" in claims:
            for props in claims["P1566"]:
                if "datavalue" in props["mainsnak"]:
                    geonamesID=props["mainsnak"]["datavalue"]["value"]

    return geonamesID



#################################################################################################

#########################
#Organization
#########################
def get_official_language(json_object):
    """ Gets official language (P37) of object

    :param json_object: entity object <class 'dict'>
    :return: official language (int)  | None
    """
    official_language=[]
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P37" in claims:
            for props in claims["P37"]:
                if "datavalue" in props["mainsnak"]:
                        official_language.append(props["mainsnak"]["datavalue"]["value"]["numeric-id"])

    return official_language


def get_inception(json_object):
    """Gets date of inception (P571)

    :param json_object: entity object <class 'dict'>
    :return: date of inception (string)  | None
    """
    inception=None
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P571" in claims:
            inception=get_datelife(json_object, "P571")

    return inception


def get_hq_location(json_object):
    """Gets HQ Location (P159)

       :param json_object: entity object <class 'dict'>
       :return: hq_location (int)  | None
       """
    hq_location=None
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P159" in claims:
            for props in claims["P159"]:
                if "datavalue" in props["mainsnak"]:
                    hq_location=props["mainsnak"]["datavalue"]["value"]["numeric-id"]

    return hq_location


def get_official_website(json_object):
    """Gets official website (P856)

           :param json_object: entity object <class 'dict'>
           :return: official_website (string)  | None
           """
    official_website=None
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P856" in claims:
            for props in claims["P856"]:
                if "datavalue" in props["mainsnak"]:
                    official_website=props["mainsnak"]["datavalue"]["value"]

    return official_website


def get_founder(json_object):
    """Gets founder (P112)

           :param json_object: entity object <class 'dict'>
           :return: founder (list of int)
           """
    founder=[]
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P112" in claims:
            for props in claims["P112"]:
                if "datavalue" in props["mainsnak"]:
                    founder.append(props["mainsnak"]["datavalue"]["value"]["numeric-id"])

    return founder


def get_ceo(json_object):
    """Gets CEO (P169)

           :param json_object: entity object <class 'dict'>
           :return: ceo (list of int)
           """
    ceo=[]
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P169" in claims:
            for props in claims["P169"]:
                if "datavalue" in props["mainsnak"]:
                    ceo.append(props["mainsnak"]["datavalue"]["value"]["numeric-id"])

    return ceo


def get_country(json_object):
    """Gets country (P17)

           :param json_object: entity object <class 'dict'>
           :return: country (list of int)
           """
    country=[]
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P17" in claims:         #Claims for country
            for p17entry in claims["P17"]:
                if "datavalue" in p17entry["mainsnak"]:
                    country.append(p17entry["mainsnak"]["datavalue"]["value"]["numeric-id"])

    return country


def get_instance_of(json_object):
    """Gets the id of the organization type (instance of) (P131)

           :param json_object: entity object <class 'dict'>
           :return: instance_of (list of int)
           """
    instance_of=[]
    if "claims" in json_object:  # if claims are available for the item
        claims = json_object["claims"]
        if "P31" in claims:         #Claims for country
            for props in claims["P31"]:
                if "datavalue" in props["mainsnak"]:
                    instance_of.append(props["mainsnak"]["datavalue"]["value"]["numeric-id"])

    return instance_of