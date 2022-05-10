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


import NECKAr_get_functions as get_functions
import bson.objectid

######################################################################################################
# Common Entries
######################################################################################################
def write_common_fields(item):
    """
    All entities have a set of comon inforamtion: id, label, description, en_sitelinkk and de_sitelink.
    This function extracts these information from the dump and stores them in a dictionary.

    :param item: entity object <class 'dict'>
    :return: entry: dictionary with information about the entry <class 'dict'>
    """
    entry={}
    entry["id"]=get_functions.get_WDid(item)
    entry["_id"]=bson.objectid.ObjectId()
    wdid=entry["id"]

    name = get_functions.get_label(item,wdid)
    if name:
        entry["norm_name"]=name

    descr = get_functions.get_description(item)
    if descr:
        entry["description"]=descr

    enlink = get_functions.get_en_sitelink(item)
    if enlink:
        entry["en_sitelink"]=enlink

    delink = get_functions.get_de_sitelink(item)
    if delink:
        entry["de_sitelink"]=delink

    return entry






