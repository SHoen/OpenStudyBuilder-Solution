from typing import Sequence

from pydantic import BaseModel


def list_concept_wildcard_properties(target_model: BaseModel = None) -> Sequence[str]:
    """
    Returns a list of properties on which to apply wildcard filtering, formatted as defined in the Cypher query.

    :param target_model: Used to define a specific target model, ie name or attributes.
    :return: List of strings, representing property names
    """
    property_list = []

    for attribute, attrDesc in target_model.__fields__.items():
        # Wildcard filtering only searches in properties of type string
        if (
            attrDesc.type_ is str
            and not attribute in ["possibleActions"]
            # remove fields that shouldn't be included in wildcard filter
            and not attrDesc.field_info.extra.get("removeFromWildcard", False)
        ):
            property_list.append(attribute)
    return list(set(property_list))
