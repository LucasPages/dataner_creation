Those two files are configuration files for the extraction process that creates DataNER.
They serve as parameters for the `extract_collection.py` script.

* anchors.yaml : only extracts anchors from the MongoDB collections
* dataner_config.yaml : extracts all entities that have been created through the augmentation process. You need to have run `augment_mentions.py` to use this one.