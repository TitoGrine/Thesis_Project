from .constants import ENTITY_MAP


def map_entity_to_name(entity_code):
    if entity_code in ENTITY_MAP.keys():
        return ENTITY_MAP[entity_code]
