import spacy

from src.utils import map_entity_to_name

nlp = spacy.load("en_core_web_sm", disable=["tok2vec", "tagger", "parser", "attribute_ruler", "lemmatizer"])


def extract_link_entities(corpus, extraction_params):
    entities = {key.replace("_", ""): set() for key, _ in extraction_params.items()}

    doc = nlp(corpus[:1000000])

    for entity in doc.ents:
        try:
            entities[map_entity_to_name(entity.label_)].add(entity.text)
        except KeyError:
            continue

    entities = {ley: list(value) for ley, value in entities.items()}

    return entities
