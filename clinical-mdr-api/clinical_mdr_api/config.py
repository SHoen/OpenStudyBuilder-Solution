"""Configuration parameters."""
import os
import urllib.parse
from os import environ
from typing import Optional

from neomodel import config
from pydantic import BaseSettings

# Teach urljoin that Neo4j DSN URLs like bolt:// and neo4j:// semantically similar to http://
for scheme in ("bolt", "bolt+s", "neo4j", "neo4j+s"):
    urllib.parse.uses_relative.append(scheme)
    urllib.parse.uses_netloc.append(scheme)

neo4j_dsn = environ.get("NEO4J_DSN")
config.DATABASE_URL = neo4j_dsn
db_name = environ.get("NEO4J_DATABASE")
if db_name:
    config.DATABASE_URL = urllib.parse.urljoin(neo4j_dsn, f"/{db_name}")


class Settings(BaseSettings):
    app_name: str = "Clinical MDR API"
    neo4j_dsn: Optional[str]
    neo4j_database: str = environ.get("NEO4J_DATABASE", "neo4j")


settings = Settings()

CACHE_MAX_SIZE = 1000
CACHE_TTL = 3600

MAX_INT_NEO4J = 9223372036854775807
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 1000
NON_VISIT_NUMBER = 29500
UNSCHEDULED_VISIT_NUMBER = 29999
FIXED_WEEK_PERIOD = 7

XML_STYLESHEET_DIR_PATH = "xml_stylesheets/"

CT_UID_BOOLEAN_YES = "C49488_Y"
CT_UID_BOOLEAN_NO = "C49487_N"
STUDY_EPOCH_TYPE_NAME = "Epoch Type"
STUDY_EPOCH_SUBTYPE_NAME = "Epoch Sub Type"
STUDY_EPOCH_EPOCH_NAME = "Epoch"
BASIC_EPOCH_NAME = "Basic"
STUDY_EPOCH_EPOCH_UID = "C99079"
STUDY_DISEASE_MILESTONE_TYPE_NAME = "Disease Milestone Type"

STUDY_VISIT_TYPE_NAME = "VisitType"
STUDY_VISIT_NAME = "VisitName"
STUDY_DAY_NAME = "StudyDay"
STUDY_DURATION_DAYS_NAME = "StudyDurationDays"
STUDY_WEEK_NAME = "StudyWeek"
STUDY_DURATION_WEEKS_NAME = "StudyDurationWeeks"
STUDY_TIMEPOINT_NAME = "TimePoint"
STUDY_VISIT_TIMEREF_NAME = "Time Point Reference"
STUDY_ELEMENT_SUBTYPE_NAME = "Element Sub Type"
GLOBAL_ANCHOR_VISIT_NAME = "Global anchor visit"
PREVIOUS_VISIT_NAME = "Previous Visit"
ANCHOR_VISIT_IN_VISIT_GROUP = "Anchor visit in visit group"
STUDY_ENDPOINT_TP_NAME = "StudyEndpoint"
STUDY_FIELD_PREFERRED_TIME_UNIT_NAME = "preferred_time_unit"

STUDY_VISIT_SUBLABEL = "Visit Sub Label"
STUDY_VISIT_CONTACT_MODE_NAME = "Visit Contact Mode"
STUDY_VISIT_EPOCH_ALLOCATION_NAME = "Epoch Allocation"
DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"

DAY_UNIT_NAME = "day"
# conversion to second which is master unit for time units
DAY_UNIT_CONVERSION_FACTOR_TO_MASTER = 86400
WEEK_UNIT_NAME = "week"
# conversion to second which is master unit for time units
WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER = 604800
STUDY_TIME_UNIT_SUBSET = "Study Time"

DEFAULT_STUDY_FIELD_CONFIG_FILE = (
    "clinical_mdr_api/tests/data/study_fields_modified.csv"
)

LIBRARY_SUBSTANCES_CODELIST_NAME = "UNII"

APPINSIGHTS_CONNECTION = environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")

OPENAPI_SCHEMA_API_ROOT_PATH = environ.get("UVICORN_ROOT_PATH", "/")

TRACING_DISABLED = environ.get("TRACING_DISABLED", "false").lower() == "true"

# Absolute path of application root directory
APP_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
