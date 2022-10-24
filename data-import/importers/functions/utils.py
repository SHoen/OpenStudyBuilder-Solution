import requests
import logging
from os import environ

from importers.metrics import Metrics

loglevel = environ.get("LOG_LEVEL", "INFO")
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError("Invalid log level: %s" % loglevel)
logging.basicConfig(
    level=numeric_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("legacy_mdr_migrations - utils")

metrics = Metrics()


def load_env(key: str, default: str = None):
    value = environ.get(key)
    logger.info("%s=%s", key, value)
    if value is None and default is None:
        logger.error("%s is not set and no default was provided", key)
        raise EnvironmentError("Failed because {} is not set.".format(key))
    if value is not None:
        return value
    else:
        logger.warning("%s is not set, using default value: %s", key, value)
        return default


# API_BASE_URL = load_env("API_BASE_URL")
# API_HEADERS = {'Accept': 'application/json'}


def sanitize_value(val: str):
    if isinstance(val, str):
        val = val.strip()
    if val == "False":
        return False
    elif val == "None":
        return None
    elif val == "":
        return None
    elif val == "True":
        return True
    else:
        return val


def camel_case_data(datadict):
    def snake_to_camel(name):
        if name.startswith("_"):
            name = name[1:]
        name = "".join(word.title() for word in name.split("_"))
        name = "{}{}".format(name[0].lower(), name[1:])
        name = sanitize_value(name)
        return name

    return_value = {}
    for key, value in datadict.items():
        return_value[snake_to_camel(key)] = sanitize_value(value)
    return return_value


# def simple_post_to_api(path, body, simple_path):
#     response = requests.post(API_BASE_URL + path, headers=API_HEADERS, json=body)
#     if response.ok:
#         metrics.icrement(simple_path)
#         logger.info("POST %s %s", path, "success")
#         return response.json()
#     else:
#         logger.warning("POST %s", path)
#         if "message" in response.json().keys() and (
#                 "all ready" in response.json()["message"] or "Duplicate template" in response.json()["message"]):
#             logger.warning(response.json())
#             metrics.icrement(simple_path + "-AlreadyExists")
#         else:
#             logger.warning(response.text)
#             metrics.icrement(simple_path + "-ERROR")
#         return None


def create_logger(name):
    loglevel = environ.get("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % loglevel)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(name)
    return logger
