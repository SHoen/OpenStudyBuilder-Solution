import re
from typing import Optional, Sequence, Union

from bs4 import BeautifulSoup

from clinical_mdr_api.domain.iso_languages import langs


def get_iso_lang_data(
    q: str,
    key: str = "639-3",
    return_key: Optional[str] = None,
    ignore_case: bool = True,
) -> Union[str, dict, list]:
    """
    Return language data of a specific language

    q: value to search for.
    key: name of the key to search the value of (if str) or in (if list). Default is 639-3.
    return_key: name of the key that should be returned. If None, all data of the specific language will be returned.
    ignore_case: whether the case should be ignored or not
    """
    if not isinstance(q, str):
        raise TypeError(f"Expected type str but found {type(q)}")

    if ignore_case:
        q = q.casefold()

    try:
        for lang in langs:
            if ignore_case:
                value = (
                    lang[key].casefold()
                    if isinstance(lang[key], str)
                    else [val.casefold() for val in lang[key]]
                )
            else:
                value = lang[key]

            if value == q or (isinstance(value, list) and q in value):
                return lang if not return_key else lang[return_key]
    except KeyError as e:
        raise KeyError(f"The key [{e}] was not found") from e

    raise ValueError(f"Value of key [{key}] is not equal to the provided value [{q}]")


def normalize_string(s: Optional[str]) -> Optional[str]:
    if s is not None:
        s = s.strip()
    return None if s == "" else s


def strip_html(html):
    return BeautifulSoup(html, "lxml").text


def convert_to_plain(text):
    no_html = strip_html(text)
    no_brackets = no_html.replace("[", "").replace("]", "")
    return no_brackets


def extract_parameters(name: str) -> Sequence[str]:
    """
    Extracts all parameters that are included in the specified name.
    Parameters are those strings that are in square brackets; e.g. 'My [Activity]' has 'Activity' as parameter.

    :param name: the name of the objective template potentially including some parameters in square brackets
    :return: List[str] including the parameter names; potentially includes duplicates
    """
    return re.findall(r"\[([\w\s\-]+)]", name)


def is_syntax_of_template_name_correct(name: str) -> bool:
    """
    Checks the syntax of the name.
    The syntax is considered to be valid if all of the following conditions are true:
    * The name consists of at least one printable character.
    * The name contains no brackets or a matching number of opening and closing brackets [].
    * The name does not contain nested brackets like this: [a[b]c].
    * The parameters within the brackets need to consist of at least one character.

    :param name: the name of the template (e.g. an objective template or an endpoint template ..)
    :return: True if the syntax of the name is valid.
    """
    if not isinstance(name, str):
        raise TypeError(f"Expected type str but found {type(name)}")

    if len(name.strip()) == 0:
        return False

    brackets_counter = 0
    char_counter = 0
    for char in name:
        if char == "[":
            brackets_counter += 1
            char_counter = 0
        elif char == "]":
            if char_counter == 0:
                return False
            brackets_counter -= 1
            char_counter = 0
        else:
            char_counter += 1

        if brackets_counter < 0 or brackets_counter > 1:
            return False

    return brackets_counter == 0


def factorize_dict(data: dict) -> dict:
    return_dict = {}
    for key, value in data.items():
        new_key = key if key.startswith("_") else "_" + key
        return_dict[new_key] = value
    return return_dict


def defactorize_dict(data: dict) -> dict:
    return_dict = {}
    for key, value in data.items():
        new_key = key[1:] if key.startswith("_") else key
        return_dict[new_key] = value
    return return_dict
