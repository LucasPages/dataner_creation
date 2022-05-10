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
# last updated 21.3.2017 by Johanna Geiß              #
#######################################################

from requests import get
import json


def get_wikidata_item_tree_item_idsSPARQL(root_items, forward_properties=None, backward_properties=None):
    """Return ids of WikiData items, which are in the tree spanned by the given root items and claims relating them
        to other items.

    :param root_items: iterable[int] One or multiple item entities that are the root elements of the tree
    :param forward_properties: iterable[int] | None property-claims to follow forward; that is, if root item R has
        a claim P:I, and P is in the list, the search will branch recursively to item I as well.
    :param backward_properties: iterable[int] | None property-claims to follow in reverse; that is, if (for a root
        item R) an item I has a claim P:R, and P is in the list, the search will branch recursively to item I as well.
    :return: iterable[int]: List with ids of WikiData items in the tree
    """

    query = '''PREFIX wikibase: <http://wikiba.se/ontology#>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>'''
    if forward_properties:
        query += '''SELECT ?WD_id WHERE {
                  ?tree0 (wdt:P%s)* ?WD_id .
                  BIND (wd:%s AS ?tree0)
                  }'''%( ','.join(map(str, forward_properties)), ','.join(map(str, root_items)))
    elif backward_properties:
        query+='''SELECT ?WD_id WHERE {
                    ?WD_id (wdt:P%s)* wd:Q%s .
                    }'''%(','.join(map(str, backward_properties)), ','.join(map(str, root_items)))
    #print(query)

    url = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
    data = get(url, params={'query': query, 'format': 'json'})
    with open("test", "w+") as test_output:
        test_output.write(data.text)
    try:
        data = json.loads(data.text)
    except json.decoder.JSONDecodeError:
        return []

    ids = []
    for item in data['results']['bindings']:
        this_id=item["WD_id"]["value"].split("/")[-1].lstrip("Q")
        try:
            this_id = int(this_id)
            ids.append(this_id)
        except ValueError:
            print("ERROR\tWikidata Processor:get_wikidata_item_tree_item_idsSPARQL\tCould not convert data to an integer.", this_id)
    return ids