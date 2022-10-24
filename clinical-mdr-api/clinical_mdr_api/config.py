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
    api_running_version: str = "develop"


settings = Settings()

CACHE_MAX_SIZE = 1000
CACHE_TTL = 3600

MAX_PAGE_SIZE = 1000
NON_VISIT_NUMBER = 29500
UNSCHEDULED_VISIT_NUMBER = 29999
FIXED_WEEK_PERIOD = 7

STUDY_EPOCH_TYPE_NAME = "Epoch Type"
STUDY_EPOCH_SUBTYPE_NAME = "Epoch Sub Type"
STUDY_EPOCH_EPOCH_NAME = "Epoch"
BASIC_EPOCH_NAME = "Basic"
STUDY_EPOCH_EPOCH_UID = "C99079"
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
STUDY_ENDPOINT_TP_NAME = "StudyEndpoint"

STUDY_VISIT_SUBLABEL = "Visit Sub Label"
STUDY_VISIT_CONTACT_MODE_NAME = "Visit Contact Mode"
STUDY_VISIT_EPOCH_ALLOCATION_NAME = "Epoch Allocation"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

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

APPINSIGHTS_CONNECTION = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")

BUILD_ID = os.environ.get("BUILD_ID") or "unknown-build"
COMMIT_ID = os.environ.get("COMMIT_ID") or "unknown-commit"
