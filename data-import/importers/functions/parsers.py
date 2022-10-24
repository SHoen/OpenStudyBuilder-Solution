from typing import Optional, Sequence, Any
import logging

logger = logging.getLogger("legacy_mdr_migrations")
# ---------------------------------------------------------------
# Utilites for parsing and converting data
# ---------------------------------------------------------------
#
def parse_YN_as_bool(yn: str) -> bool:
    if yn == "Y":
        return True
    elif yn == "N":
        return False
    else:
        logger.warning("Failed to parse %s to boolean, defaulting to False", yn)
        return False


def parse_to_int(s: str) -> int:
    try:
        return int(s)
    except ValueError:
        logger.warning("Failed to parse %s to integer, defaulting to 0", s)
        return 0


def title_case(s: str) -> str:
    exceptions = ["And", "Or", "The", "A", "Of", "In"]
    words = s.title().split(" ")
    return " ".join(
        [words[0]]
        + [word.lowercase() if word in exceptions else word for word in words[1:]]
    )


def pass_float(value: str) -> Optional[float]:
    # SAS DEFAUTL for NULL is "."
    if value == ".":
        return None
    try:
        new_value = float(value.replace("E", "e"))
    except:
        new_value = 0.0
        logger.warning("Unable to parse string %s to float value", value)
    return new_value


def map_boolean(bool_str: str) -> bool:
    if bool_str == "Y" or bool_str == "T":
        return True
    elif bool_str == "F" or bool_str == "N":
        return False
    else:
        logger.warning(
            "Unable to map string :'"
            + bool_str
            + "' to a boolean value, default is set to false"
        )
        return False


def map_boolean_exc(bool_str: str) -> bool:
    if bool_str == "Y" or bool_str == "T":
        return True
    elif bool_str == "F" or bool_str == "N":
        return False
    else:
        raise ValueError("Unable to map string :'" + bool_str + "' to a boolean value")


def find_term_by_name(term_name: str, all_terms: Sequence[dict]) -> Optional[str]:
    termUid = None
    for term in all_terms:
        if term["name"]["sponsorPreferredName"].lower() == term_name.lower():
            termUid = term["termUid"]
            break
        elif term["attributes"]["codeSubmissionValue"] is not None:
            if term["attributes"]["codeSubmissionValue"].lower() == term_name.lower():
                termUid = term["termUid"]
                break
        elif term["attributes"]["nameSubmissionValue"] is not None:
            if term["attributes"]["nameSubmissionValue"].lower() == term_name.lower():
                termUid = term["termUid"]
                break
    return termUid


def update_uid_list_dict(key: str, dictionary: dict, value_to_add: Any):
    if key not in dictionary:
        dictionary[key] = [value_to_add]
    else:
        dictionary[key].append(value_to_add)
