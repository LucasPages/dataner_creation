# DataNER

This repository contains the code used to create the DataNER corpus, which is annotated for NER using Wikipedia and WikiData.

## Dependencies

You need to [install MongoDB](https://www.mongodb.com/docs/manual/administration/install-community/) in order to use this repository.


## Description

The code contained in this repository will process a Wikipedia xml dump and a WikiData json dump and use them
to build a corpus annotated with named entities.

It was developed as part of a (french-speaking) master's thesis at Université de Montréal. The findings of the thesis sadly showed this process led to a lesser quality corpus in comparison to other similar corpora.
The code itself still constitutes an interesting contribution to approach this method, thus justifying publishing it.


## How to use

1. Download the [Wikipedia](https://en.wikipedia.org/wiki/Wikipedia:Database_download) and [WikiData](https://www.wikidata.org/wiki/Wikidata:Database_download#JSON_dumps_(recommended)) dump of your liking.
2. Download the WikiExtractor GitHub and NECKAr tool and move them into their respective folders in this repository (see README files)
3. Add WikiData dump path to the NECKAr.cfg file in the NECKAr folder.
4. Run the `process_wikidata_dump.sh` script.
5. Run the `process_wikipedia_dump.sh` script.
6. (_Optional_) Run the `augment_mentions.py` script to create more named entities in your corpus.
7. Run the `extract_collection.py` script to create the corpus.

## Disclaimer

This code was experimented with and used on a 24-threads computer, it might be very slow on a more "normal" one.
If the scripts take an unreasonable time to run, I recommend using a subset of Wikipedia to still be able to produce a corpus.


## References

This code is based on two other works :

* Giusepppe Attardi. Wikiextractor. https://github.com/attardi/wikiextractor, 2015.

* Johanna Geiß, Andreas Spitz, and Michael Gertz. Neckar : A named entity classifier for
wikidata. In Georg Rehm and Thierry Declerck, editors, Language Technologies for the
Challenges of the Digital Age, pages 115–129, Cham, 2018. Springer International Publi-
shing. ISBN 978-3-319-73706-5.

## Contact

Please reach out to [lucas.pages@umontreal.ca](mailto:lucas.pages@umontreal.ca) if you have any question about this repository.