from importers.metrics import Metrics
from os import environ
import os
import csv
from typing import Optional, Sequence, Any
import re
from aiohttp_trace import request_tracer
import json
import copy
import sys
from functools import lru_cache

from importers.functions.utils import load_env
from importers.functions.parsers import map_boolean
from importers.importer import BaseImporter, open_file
from importers import import_templates

metrics = Metrics()

API_HEADERS = {"Accept": "application/json"}

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False").lower() == "true"
API_BASE_URL = load_env("API_BASE_URL")

IMPORT_PROJECTS = load_env("IMPORT_PROJECTS")
MDR_MIGRATION_EXPORTED_PROGRAMMES=environ.get("MDR_MIGRATION_EXPORTED_PROGRAMMES","True").lower() == "true"
MDR_MIGRATION_EXPORTED_BRANDS=environ.get("MDR_MIGRATION_EXPORTED_BRANDS","True").lower() == "true"
MDR_MIGRATION_EXPORTED_ACTIVITIES=environ.get("MDR_MIGRATION_EXPORTED_ACTIVITIES","True").lower() == "true"
MDR_MIGRATION_EXPORTED_ACTIVITY_INSTANCES=environ.get("MDR_MIGRATION_EXPORTED_ACTIVITY_INSTANCES","True").lower() == "true"
MDR_MIGRATION_EXPORTED_UNITS=environ.get("MDR_MIGRATION_EXPORTED_UNITS","True").lower() == "true"
MDR_MIGRATION_EXPORTED_COMPOUNDS=environ.get("MDR_MIGRATION_EXPORTED_COMPOUNDS","True").lower() == "true"
MDR_MIGRATION_EXPORTED_TEMPLATES=environ.get("MDR_MIGRATION_EXPORTED_TEMPLATES","True").lower() == "true"
MDR_MIGRATION_EXPORTED_PROJECTS=environ.get("MDR_MIGRATION_EXPORTED_PROJECTS","True").lower() == "true"
MDR_MIGRATION_EXPORTED_STUDIES=environ.get("MDR_MIGRATION_EXPORTED_STUDIES","True").lower() == "true"
INCLUDE_STUDY_NUMBERS = environ.get("INCLUDE_STUDY_NUMBERS", "")
EXCLUDE_STUDY_NUMBERS = environ.get("EXCLUDE_STUDY_NUMBERS", "")

IMPORT_DIR = os.path.dirname(IMPORT_PROJECTS)

ENDPOINT_TO_KEY_MAP = {
    "objective": {
        "get": "study-objectives",
        "post": "study-objectives/create",
        "data": "objective",
        "uid": "studyObjectiveUid",
    },
    "criteria": {
        "get": "study-criteria",
        "post": "study-criteria/create",
        "data": "criteria",
        "uid": "studyCriteriaUid",
    },
    "endpoint": {
        "get": "study-endpoints",
        "post": "study-endpoints/create",
        "data": "endpoint",
        "uid": "studyEndpointUid",
    },
    "activity_description": {
        "get": "study-activities",
        "post": "study-activities/create",
        "data": "activity",
        "uid": "studyActivityUid",
    },
}


class MockdataJson(BaseImporter):
    logging_name = "mockdata_json"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)
        self.log.info("Preparing lookup tables")

        # TODO replace all these lookup tables with lookup functions
        self.all_study_times = self.api.get_all_identifiers(
            self.api.get_all_from_api("/concepts/unit-definitions?subset=Study Time"),
            identifier="name",
            value="uid",
        )

    @lru_cache(maxsize=10000)
    def lookup_ct_term_uid(
        self, codelist_name, value, key="sponsorPreferredName", uid_key="termUid"
    ):
        self.log.info(
            f"Looking up term with '{key}' == '{value}' in codelist '{codelist_name}', returning uid from '{uid_key}'"
        )
        filt = {key: {"v": [value], "op": "eq"}}
        data = self.api.get_all_identifiers(
            self.api.get_all_from_api(
                f"/ct/terms/names?size=1&codelist_name={codelist_name}&filters={json.dumps(filt)}"
            ),
            identifier=key,
            value=uid_key,
        )
        uid = data.get(value, None)
        if uid:
            self.log.debug(
                f"Found term with '{key}' == '{value}' in codelist '{codelist_name}', uid '{uid}'"
            )
            return uid
        self.log.warning(
            f"Could not find term with '{key}' == '{value}' in codelist '{codelist_name}'"
        )

    @lru_cache(maxsize=10000)
    def lookup_concept_uid(self, name, endpoint, subset=None):
        self.log.info(f"Looking up concept {endpoint} with name '{name}'")
        filt = {"name": {"v": [name], "op": "eq"}}
        path = f"/concepts/{endpoint}?filters={json.dumps(filt)}"
        if subset:
            path = f"{path}&subset={subset}"
        items = self.api.get_all_from_api(path)
        if items is not None and len(items) > 0:
            uid = items[0].get("uid", None)
            self.log.info(
                f"Found concept {endpoint} with name '{name}' and uid '{uid}'"
            )
            return uid
        self.log.warning(f"Could not find concept {endpoint} with name '{name}'")

    def lookup_activity_uid(self, name):
        return self.lookup_concept_uid(name, "activities/activities")

    def lookup_activity_group_uid(self, name):
        return self.lookup_concept_uid(name, "activities/activity-groups")

    def lookup_activity_subgroup_uid(self, name):
        return self.lookup_concept_uid(name, "activities/activity-sub-groups")

    # Unused for now
    def lookup_activity_instance_uid(self, name):
        return self.lookup_concept_uid(name, "activities/activity-instances")

    def lookup_compound_uid(self, name):
        return self.lookup_concept_uid(name, "compounds")

    def lookup_compound_alias_uid(self, name):
        return self.lookup_concept_uid(name, "compound-aliases")

    def lookup_unit_uid(self, name, subset=None):
        uid = self.lookup_concept_uid(name, "unit-definitions", subset=subset)
        if uid is None:
            self.log.info(f"Unit name '{name}' not found, trying again with lowercase '{name.lower()}'")
            uid = self.lookup_concept_uid(name.lower(), "unit-definitions", subset=subset)
        if uid is None:
            self.log.info(f"Unit name '{name}' not found, trying again with uppercase '{name.upper()}'")
            uid = self.lookup_concept_uid(name.upper(), "unit-definitions", subset=subset)
        self.log.info(f"Looked up unit name '{name}', found uid '{uid}'")
        return uid

    @lru_cache(maxsize=10000)
    def lookup_dictionary_uid(self, name):
        self.log.info(f"Looking up dictionary with name '{name}'")
        items = self.api.get_all_from_api(f"/dictionaries/codelists/{name}")
        if items is not None and len(items) > 0:
            uid = items[0].get("codelistUid", None)
            self.log.debug(f"Found dictionary with name '{name}' and uid '{uid}'")
            return uid
        self.log.warning(f"Could not find dictionary with name '{name}'")

    @lru_cache(maxsize=10000)
    def lookup_ct_codelist_uid(self, name):
        self.log.info(f"Looking up ct codelist with name '{name}'")
        filt = {"name": {"v": [name], "op": "eq"}}
        items = self.api.get_all_from_api(f"/ct/codelists/names?filters={json.dumps(filt)}")
        if items is not None and len(items) > 0:
            uid = items[0].get("codelistUid", None)
            self.log.debug(f"Found ct codelist with name '{name}' and uid '{uid}'")
            return uid
        self.log.warning(f"Could not find ct codelist with name '{name}'")

    @lru_cache(maxsize=10000)
    def get_study_by_key(self, key, value):
        filt = {key: {"v": [value], "op": "eq"}}
        items = self.api.get_all_from_api(
            f"/studies?filters={json.dumps(filt)}", items_only=True
        )
        if items is not None and len(items) > 0:
            uid = items[0]["uid"]
            self.log.debug(f"Found study with '{key}' == '{value}' and uid '{uid}'")
            return items[0]
        self.log.warning(f"Could not find study with '{key}' == '{value}'")

    def lookup_study_uid_from_id(self, study_id):
        data = self.get_study_by_key("studyId", study_id)
        try:
            return data["uid"]
        except (TypeError, KeyError):
            return None

    def lookup_study_uid_from_number(self, study_number):
        data = self.get_study_by_key("studyNumber", str(study_number))
        try:
            return data["uid"]
        except (TypeError, KeyError):
            return None

    def fetch_study_compounds(self, study_uid):
        self.log.info(f"Fetching study compounds for study uid '{study_uid}'")
        items = self.api.get_all_from_api(f"/study/{study_uid}/study-compounds")
        if items is None:
            items = []
        self.log.debug(f"Got {len(items)} study compounds")
        return items

    @lru_cache(maxsize=10000)
    def fetch_codelist_terms(self, name):
        self.log.info(f"Fetching terms for codelist with name '{name}'")
        items = self.api.get_all_from_api(f"/ct/terms?codelist_name={name}")
        if items is None:
            items = []
        self.log.debug(f"Got {len(items)} terms from codelist with name '{name}'")
        return items

    @lru_cache(maxsize=10000)
    def fetch_dictionary_terms(self, name):
        uid = self.lookup_dictionary_uid(name)
        self.log.info(f"Fetching terms for dictionary with name '{name}'")
        items = self.api.get_all_from_api(f"/dictionaries/terms?codelist_uid={uid}")
        if items is None:
            items = []
        self.log.debug(f"Got {len(items)} terms from dictionary with name '{name}'")
        return items

    @lru_cache(maxsize=10000)
    def lookup_dictionary_term_uid(self, dictionary_name, term_name):
        self.log.info(
            f"Looking up term with name '{term_name}' from dictionary '{dictionary_name}'"
        )
        snomed_uid = self.lookup_dictionary_uid(dictionary_name)
        filt = {"name": {"v": [term_name], "op": "eq"}}
        items = self.api.get_all_from_api(
            f"/dictionaries/terms?codelist_uid={snomed_uid}&filters={json.dumps(filt)}"
        )
        if items is not None and len(items) > 0:
            uid = items[0].get("termUid", None)
            self.log.debug(f"Found term with name '{term_name}' and uid '{uid}'")
            return uid
        self.log.warning(f"Could not find term with name '{term_name}'")

    @lru_cache(maxsize=10000)
    def lookup_codelist_term_uid(self, codelist_name, sponsor_preferred_name):
        self.log.info(
            f"Looking up term with name '{sponsor_preferred_name}' from dictionary '{codelist_name}'"
        )
        terms = self.fetch_codelist_terms(codelist_name)
        if terms is not None:
            for term in terms:
                if term["name"]["sponsorPreferredName"] == sponsor_preferred_name:
                    uid = term["termUid"]
                    self.log.debug(
                        f"Found term with sponsor preferred name '{sponsor_preferred_name}' and uid '{uid}'"
                    )
                    return uid
        self.log.warning(
            f"Could not find term with sponsor preferred name '{sponsor_preferred_name}'"
        )

    @lru_cache(maxsize=10000)
    def lookup_study_epoch_uid(self, study_uid, epoch_name):
        self.log.info(
            f"Looking up study epoch name '{epoch_name}' for study '{study_uid}'"
        )
        filt = {"epochName": {"v": [epoch_name], "op": "eq"}}
        items = self.api.get_all_from_api(
            f"/study/{study_uid}/study-epochs?filters={json.dumps(filt)}"
        )
        if items is not None and len(items) > 0:
            uid = items[0].get("uid", None)
            self.log.debug(f"Found study epoch with name '{epoch_name}' and uid '{uid}'")
            return uid
        self.log.warning(f"Could not find study epoch with name '{epoch_name}'")

    @lru_cache(maxsize=10000)
    def get_template_parameters(self, param_type):
        items = self.api.get_all_from_api(
            f"/template-parameters/{param_type}/values", items_only=False
        )
        return items

    def create_tp_based_on_simple_concept(self, name, param_type):
        path = None
        if param_type == "NumericValue":
            path = "/concepts/numeric-values"
        elif param_type == "TextValue":
            path = "/concepts/text-values"
        res = self.api.simple_post_to_api(path=path,
                                          body={"value": name, "libraryName": "Sponsor", "templateParameter": True})
        if res:
            self.log.info(
                f"Created parameter with name '{name}' of type '{param_type}'"
            )
            uid = res.get("uid", None)
            return uid
        else:
            self.log.error(
                f"Failed to create parameter with name '{name}' of type '{param_type}'"
            )
    @lru_cache(maxsize=10000)
    def lookup_parameter_value_uid(self, name, param_type):
        # SimpleConcepts based template parameters have to be created before
        # they are used in instantiation
        if param_type in ["NumericValue", "TextValue"]:
            uid = self.create_tp_based_on_simple_concept(name=name, param_type=param_type)
            return uid
        else:
            self.log.info(f"Looking up parameter with name '{name}' of type '{param_type}'")
            items = self.get_template_parameters(param_type)
            if items is not None:
                for val in items:
                    # we have to lookup in sentence case as well as if possible we return
                    # name sentence case property for template parameter value
                    # TODO add name_sentence_case property to the /template-parameters/../values endpoint
                    # and compare this value here
                    # used .lower() for a hot fix
                    if val["name"] == name or val["name"].lower() == name:
                        uid = val.get("uid", None)
                        self.log.debug(
                            f"Found parameter with name '{name}' and sentence case {val['name'].lower()} and uid '{uid}'"
                        )
                        return uid
            self.log.warning(f"Could not find parameter with name or name_sentence_case equal to'{name}'")

    @lru_cache(maxsize=10000)
    def lookup_template_uid(self, name, template_type, log=True, shortname=None):
        if shortname is None:
            shortname = name
        path = f"/{template_type}-templates"
        self.log.info(f"Looking up {template_type} template with name '{shortname}'")
        filt = {"name": {"v": [name], "op": "eq"}}
        items = self.api.get_all_from_api(f"{path}?filters={json.dumps(filt)}")
        if items is not None and len(items) > 0:
            uid = items[0].get("uid", None)
            if log:
                self.log.debug(
                    f"Found {template_type} template with name '{shortname}' and uid '{uid}'"
                )
            return uid
        if log:
            self.log.warning(f"Could not find {template_type} template with name '{shortname}'")

    @lru_cache(maxsize=10000)
    def lookup_study_template_instance_uid(self, name, study_uid, template_type):
        mapper = ENDPOINT_TO_KEY_MAP[template_type]
        endpoint = mapper["get"]
        data_key = mapper["data"]
        uid_key = mapper["uid"]
        path = f"/study/{study_uid}/{endpoint}"
        self.log.info(f"Looking for {endpoint.replace('-', ' ')} with name '{name}'")
        items = self.api.get_all_from_api(path, items_only=False)
        # Some of the enpoints return the data under "items".
        if "items" in items:
            items = items["items"]
        if items is not None:
            for item in items:
                if not item.get(data_key):
                    continue
                item_name = item[data_key].get("name")
                if item_name == name:
                    uid = item.get(uid_key, None)
                    self.log.debug(
                        f"Found {endpoint.replace('-', ' ')} with name '{name}' and uid '{uid}'"
                    )
                    return uid
        self.log.warning(
            f"Could not find {endpoint.replace('-', ' ')} with name '{name}'"
        )

    @lru_cache(maxsize=10000)
    def lookup_study_visit_uid(self, study_uid, visit_name):
        self.log.info(
            f"Looking up study visit name '{visit_name}' for study '{study_uid}'"
        )
        filt = {"visitName": {"v": [visit_name], "op": "eq"}}
        items = self.api.get_all_from_api(
            f"/study/{study_uid}/study-visits?filters={json.dumps(filt)}"
        )
        if items is not None and len(items) > 0:
            uid = items[0].get("uid", None)
            self.log.debug(f"Found study visit with name '{visit_name}' and uid '{uid}'")
            return uid
        self.log.warning(f"Could not find study visit with name '{visit_name}'")

    @lru_cache(maxsize=10000)
    def lookup_study_activity_uid(self, study_uid, activity_name):
        self.log.info(
            f"Looking up study activity name '{activity_name}' for study '{study_uid}'"
        )
        filt = {"activity.name": {"v": [activity_name], "op": "eq"}}
        items = self.api.get_all_from_api(
            f"/study/{study_uid}/study-activities?filters={json.dumps(filt)}"
        )
        if items is not None and len(items) > 0:
            uid = items[0].get("studyActivityUid")
            self.log.debug(f"Found study activity with name '{activity_name}' and uid '{uid}'")
            return uid
        self.log.warning(f"Could not find study activity with name '{activity_name}'")

    def lookup_timeframe(self, name):
        path = "/timeframes"
        self.log.info(f"Looking for timeframe with name '{name}'")
        filt = {"name": {"v": [name], "op": "eq"}}
        items = self.api.get_all_from_api(f"{path}?filters={json.dumps(filt)}")
        if items is not None and len(items) > 0:
            uid = items[0].get("uid", None)
            self.log.debug(f"Found timeframe with name '{name}' and uid '{uid}'")
            return uid
        self.log.warning(f"Could not find timeframe with name '{name}'")

    def print_cache_stats(self):
        print("\nCache summary")
        print(f"{'function':35s}\thits\tmisses")
        for key in dir(self):
            item = getattr(self, key)
            if hasattr(item, "cache_info"):
                info = item.cache_info()
                print(f"{key:35s}\t{info.hits}\t{info.misses}")

    ####################### Helper functions ######################

    def append_if_not_none(self, thelist, value):
        if value is not None:
            thelist.append(value)

    def fetch_all_activities(self):
        activities = {}
        for item in self.api.get_all_from_api("/concepts/activities/activities"):
            activities[item["name"]] = item["uid"]
        return activities

    def fetch_all_activity_groups(self):
        groups = {}
        for item in self.api.get_all_from_api("/concepts/activities/activity-groups"):
            groups[item["name"]] = item["uid"]
        return groups

    def fetch_all_activity_subgroups(self):
        subs = {}
        for item in self.api.get_all_from_api("/concepts/activities/activity-sub-groups"):
            subs[item["name"]] = item["uid"]
        return subs

    def map_sponsor_name_to_uid(self, data):
        temp_dict = {}
        if data is not None:
            for item in data:
                temp_dict[item["name"]["sponsorPreferredName"]] = item["termUid"]
        return temp_dict

    def map_epoch_name_to_uids(self, data):
        temp_dict = {}
        if data is not None:
            for item in data:
                # Remove any trailing number
                name = item["epochName"].rstrip("0123456789 ")
                if name not in temp_dict:
                    temp_dict[name] = []
                temp_dict[name].append({"order": item["order"], "uid": item["uid"]})
        new_dict = {}

        def get_order(data):
            return int(data["order"])

        for key, val in temp_dict.items():
            val.sort(key=get_order)
            new_dict[key] = [v["uid"] for v in val]

        return new_dict

    def map_fields_to_dict(self, data, key, value):
        temp_dict = {}
        if data is not None:
            for item in data:
                name = item[key]
                temp_dict[name] = item[value]
        return temp_dict

    def caseless_dict_lookup(self, input_dict, key):
        return next(
            (
                value
                for dict_key, value in input_dict.items()
                if dict_key.lower() == key.lower()
            )
        )

    def _check_for_duplicate_epoch(self, new, existing):
        if existing is None:
            return False
        for item in existing:
            # print(item["epochSubTypeName"], new["epochSubTypeName"], item["description"], new["description"])
            if (
                item["epochSubTypeName"] == new["epochSubTypeName"]
                and item["description"] == new["description"]
            ):
                return True
        return False

    def _compare_dict_path(self, a, b, path):
        aval = self._get_dict_path(a, path)
        bval = self._get_dict_path(b, path)
        return aval == bval

    def _get_dict_path(self, d, path):
        dp = d
        for p in path:
            if not isinstance(dp, dict) or p not in dp:
                return None
            dp = dp[p]
        return dp

    def _check_for_duplicate_study_compound(self, new, existing):
        if existing is None:
            return False
        for item in existing:
            if (
                item["compound"]["name"] == new["compound"]["name"]
                and item["compoundAlias"]["name"] == new["compoundAlias"]["name"]
                and item["typeOfTreatment"]["name"] == new["typeOfTreatment"]["name"]
                and self._compare_dict_path(item, new, ["dosageForm", "name"])
                and self._compare_dict_path(item, new, ["strengthValue", "value"])
                and self._compare_dict_path(item, new, ["strengthValue", "unitLabel"])
                and self._compare_dict_path(item, new, ["routeOfAdministration", "name"])
                and self._compare_dict_path(item, new, ["dispensedIn", "name"])
                and self._compare_dict_path(item, new, ["device", "name"])
                and item.get("otherInfo") == new.get("otherInfo")
            ):
                return True
        return False

    def _check_for_duplicate_visit(self, new, existing):
        if existing is None:
            return False
        for item in existing:
            # print(item["epochSubTypeName"], new["epochSubTypeName"], item["description"], new["description"])
            if (
                item["description"] == new["description"]
                and item["visitTypeName"] == new["visitTypeName"]
            ):
                return True
        return False

    def _check_for_duplicate_arm(self, new, existing):
        if existing is None:
            return False
        for item in existing:
            # print(item)
            if item["name"] == new["name"]:
                return True
        return False

    def _check_for_duplicate_element(self, new, existing):
        if existing is None:
            return False
        for item in existing:
            # print(item)
            if item["name"] == new["name"]:
                return True
        return False

    # Recursive walk through a dict to copy all values
    def _copy_parameters(self, data_old, template, clone=True):
        if clone:
            data_new = copy.deepcopy(template)
        else:
            data_new = template
        for key in data_new.keys():
            if not key.lower().endswith("uid") and data_old is not None:
                value = data_old.get(key, None)
                if isinstance(data_new[key], dict):
                    self._copy_parameters(value, data_new[key], clone=False)
                else:
                    data_new[key] = value
        return data_new

    def create_dict_path(self, data, path, key, value):
        pos = data
        for p in path:
            if p not in pos:
                pos[p] = {}
            # print("enter",p)
            pos = pos[p]
        # print("create", key, value)
        pos[key] = value

    # Recursive walk through a dict to copy all values
    def _copy_parameters_with_values(self, data_old, template, path=[], data_new={}):
        for key in list(template.keys()):
            if not key.lower().endswith("uid"):
                value_old = data_old.get(key, None)
                # print(json.dumps(value_old, indent=2))
                # print("Process key:", key, type(value_old))
                if isinstance(value_old, dict):
                    # print("Dive deeper:", path, key)
                    self._copy_parameters_with_values(
                        value_old, template[key], path=path + [key], data_new=data_new
                    )
                elif isinstance(value_old, (list, str)) and len(value_old) > 0:
                    # print("Create list or str:", path, key, value_old)
                    # TODO don't simply replace lists, handle properly!
                    self.create_dict_path(data_new, path, key, value_old)
                elif isinstance(value_old, (int, float)):
                    # print("Create number:", path, key, value_old)
                    self.create_dict_path(data_new, path, key, value_old)
                # else:
                # print("Skip:", path, key, value_old)
            # else:
            # print("Skip key:", key)
        return data_new

    def get_dict_path(self, data, path, default=None):
        pos = data
        # print(json.dumps(pos, indent=2))
        for p in path[0:-1]:
            # print("--- go to", p)
            pos = pos.get(p, {})
            # print(json.dumps(pos, indent=2))
        return pos.get(path[-1], default)

    # Some sponsor preferred names have changed.
    # This is a helper to allow importing old data.
    def update_name(self, name, codelist_name):
        if codelist_name == "Study Type":
            suffix = [" Study"]
        elif codelist_name == "Trial Type":
            suffix = [" Study", " Trial"]
        elif codelist_name == "Control Type":
            suffix = [" Control"]
        elif codelist_name == "Trial Blinding Schema":
            suffix = [" Study"]
        elif codelist_name == "Intervention Model Response":
            suffix = [" Study"]
        else:
            return name
        for s in suffix:
            if name.endswith(s):
                return name[0:-len(suffix)]
        return name


    ################### Study metadata helpers ################

    def fill_age_unit(self, data, key):
        name = self.get_dict_path(data, [key, "durationUnitCode", "name"], default=None)
        if name:
            #uid = self.lookup_ct_term_uid("Age Unit", name)
            uid = self.lookup_unit_uid(name, subset="Age Unit")
            if uid:
                self.log.info(f"Found time unit '{name}' with uid '{uid}'")
                self.create_dict_path(data, [key, "durationUnitCode"], "termUid", uid)
            else:
                self.log.warning(f"Could not find time unit '{name}'")

    def fill_general_term(self, data, key, codelist_name):
        name = self.get_dict_path(data, [key, "name"], default=None)
        if name:
            name = self.update_name(name, codelist_name)
            uid = self.lookup_ct_term_uid(codelist_name, name)
            if uid:
                self.log.info(
                    f"Found term '{name}' with uid '{uid}' in codelist '{codelist_name}'"
                )
                self.create_dict_path(data, [key], "termUid", uid)
            else:
                self.log.warning(
                    f"Could not find term '{name}' in codelist '{codelist_name}'"
                )

    def fill_general_term_list(self, data, key, codelist_name):
        items = data.get(key, [])
        if items:
            for item in items:
                name = item["name"]
                uid = self.lookup_ct_term_uid(codelist_name, name)
                if uid:
                    self.log.info(
                        f"Found term name '{name}' with uid '{uid}' in codelist '{codelist_name}'"
                    )
                    item["termUid"] = uid
                else:
                    self.log.warning(
                        f"Could not find term '{name}' in codelist '{codelist_name}'"
                    )

    def fill_snomed_term_list(self, data, key):
        items = data.get(key, [])
        if items:
            for item in items:
                name = item["name"]
                uid = self.lookup_dictionary_term_uid("SNOMED", name)
                if uid:
                    self.log.info(
                        f"Found term name '{name}' with uid '{uid}' in SNOMED'"
                    )
                    item["termUid"] = uid
                else:
                    self.log.warning(f"Could not find term '{name}' in SNOMED'")

    def fill_null_value_codes(self, data, template):
        for key in list(data.keys()):
            if key.endswith("NullValueCode"):
                data_key = key.replace("NullValueCode", "")
                self.log.info(f"Handle null value for {data_key}")
                if data.get(data_key, None) is None:
                    self.log.info(f"No data, update {key}")
                    self.fill_general_term(data, key, "Null Flavor")
                else:
                    self.log.info(f"Data found, null {key}")
                    data[key] = None
            else:
                nullvalue_key = key + "NullValueCode"
                if nullvalue_key in template:
                    self.log.info(
                        f"Data exists for '{key}', set '{nullvalue_key}' to None"
                    )
                    data[nullvalue_key] = None

    ################### Study metadata uid lookups ################

    def fill_high_level_study_design(self, data):
        self.log.info("--- Looking up data for High Level Study Design ---")
        metadata = self.get_dict_path(
            data, ["currentMetadata", "highLevelStudyDesign"], default={}
        )
        template = self.get_dict_path(
            import_templates.study_patch,
            ["currentMetadata", "highLevelStudyDesign"],
            default={},
        )

        self.fill_age_unit(metadata, "confirmedResponseMinimumDuration")

        self.fill_general_term(metadata, "studyTypeCode", "Study Type")
        self.fill_general_term(metadata, "trialPhaseCode", "Trial Phase")

        items = metadata.get("diagnosisGroupsCodes", [])
        if items:
            for item in items:
                name = item["name"]
                uid = self.lookup_ct_term_uid("Trial Type", name)
                if uid:
                    self.log.info(f"Found trial type '{name}' with uid '{uid}'")
                    item["termUid"] = uid
                else:
                    self.log.warning(f"Could not find trial type '{name}'")

        self.fill_null_value_codes(metadata, template)

    def fill_study_population(self, data):
        self.log.info("--- Looking up data for Study Population ---")
        metadata = self.get_dict_path(
            data, ["currentMetadata", "studyPopulation"], default={}
        )
        template = self.get_dict_path(
            import_templates.study_patch,
            ["currentMetadata", "studyPopulation"],
            default={},
        )

        self.fill_age_unit(metadata, "plannedMaximumAgeOfSubjects")
        self.fill_age_unit(metadata, "plannedMinimumAgeOfSubjects")
        self.fill_age_unit(metadata, "stableDiseaseMinimumDuration")

        self.fill_general_term(metadata, "sexOfParticipantsCode", "Sex of Participants")

        self.fill_snomed_term_list(metadata, "diagnosisGroupsCodes")
        self.fill_snomed_term_list(metadata, "diseaseConditionsOrIndicationsCodes")
        self.fill_snomed_term_list(metadata, "therapeuticAreasCodes")
        self.fill_null_value_codes(metadata, template)

    def fill_study_intervention(self, data):
        self.log.info("--- Looking up data for Study Interventions ---")
        metadata = self.get_dict_path(
            data, ["currentMetadata", "studyIntervention"], default={}
        )
        template = self.get_dict_path(
            import_templates.study_patch,
            ["currentMetadata", "studyIntervention"],
            default={},
        )

        self.fill_general_term(metadata, "controlTypeCode", "Control Type")
        self.fill_general_term(metadata, "interventionModelCode", "Intervention Model")
        self.fill_general_term(metadata, "interventionTypeCode", "Intervention Type")
        self.fill_general_term(
            metadata, "trialBlindingSchemaCode", "Trial Blinding Schema"
        )
        self.fill_age_unit(metadata, "plannedStudyLength")
        self.fill_general_term_list(
            metadata, "trialIntentTypesCodes", "Trial Indication Type"
        )
        self.fill_null_value_codes(metadata, template)

    ####################### Import functions ######################

    # Projects
    @open_file()
    def handle_projects(self, jsonfile):
        self.log.info("======== Projects ========")
        import_data = json.load(jsonfile)

        all_project_numbers = self.api.get_all_identifiers(
            self.api.get_all_from_api("/projects"), "projectNumber"
        )
        all_clinical_programmes = self.api.get_all_identifiers(
            self.api.get_all_from_api("/clinical-programmes", items_only=False),
            identifier="name",
            value="uid",
        )

        # Create the project
        for project in import_data:
            data = self._copy_parameters(
                project,
                import_templates.project,
            )
            program_name = project["clinicalProgramme"]["name"]
            project_number = project["projectNumber"]
            data["clinicalProgrammeUid"] = all_clinical_programmes.get(
                program_name
            )
            if data["clinicalProgrammeUid"] is None:
                self.log.error(
                    f"Unable to find programme {program_name}, skipping this project"
                )
                continue
            # self.log.info(f"=== Handle project '{project_number}' ===")
            # print(json.dumps(data, indent=2))

            if project_number not in all_project_numbers:
                self.log.info(f"Add project '{project_number}'")
                self.api.simple_post_to_api("/projects", data, "/studies")
            else:
                self.log.info(f"Skipping existing project '{project_number}'")

    def filter_studies(self, studies):
        include_numbers = [
            int(nbr) for nbr in INCLUDE_STUDY_NUMBERS.split(",") if len(nbr.strip()) > 0
        ]
        exclude_numbers = [
            int(nbr) for nbr in EXCLUDE_STUDY_NUMBERS.split(",") if len(nbr.strip()) > 0
        ]
        studies_copy = []
        for study in studies:
            to_copy = True
            study_number = int(
                study["currentMetadata"]["identificationMetadata"]["studyNumber"]
            )
            study_uid = study["uid"]
            if len(include_numbers) > 0 and study_number not in include_numbers:
                to_copy = False
            if len(exclude_numbers) > 0 and study_number in exclude_numbers:
                to_copy = False
            if to_copy:
                self.log.info(
                    f"Including study number {study_number} with uid '{study_uid}'"
                )
                studies_copy.append(study)
            else:
                self.log.info(
                    f"Excluding study number {study_number} with uid '{study_uid}'"
                )
        return studies_copy

    # Handle studies.
    @open_file()
    def handle_studies(self, jsonfile):
        self.log.info("======== Studies ========")
        all_studies = json.load(jsonfile)
        filtered_studies = self.filter_studies(all_studies)
        for study_data in filtered_studies:
            study_name = study_data["currentMetadata"]["identificationMetadata"][
                "studyId"
            ]
            exported_uid = study_data["uid"]
            # nbr = int(study_data["studyNumber"])
            # if nbr != 1003:
            #    continue
            study_json = os.path.join(IMPORT_DIR, f"studies.{exported_uid}.json")
            self.handle_study(study_json)
            self.handle_study_design(exported_uid, study_name)

    @open_file()
    def handle_study(self, jsonfile):
        import_data = json.load(jsonfile)
        # Create the study
        data = self._copy_parameters(
            import_data["currentMetadata"]["identificationMetadata"],
            import_templates.study,
        )
        study_nbr = import_data["currentMetadata"]["identificationMetadata"][
            "studyNumber"
        ]
        study_id = import_data["currentMetadata"]["identificationMetadata"]["studyId"]
        path = "/studies"
        self.log.info(f"=== Handle study '{study_id}' ===")

        if self.lookup_study_uid_from_number(study_nbr) is None:
            self.log.info(f"Add study '{study_id}' with study number {study_nbr}")
            study_data = self.api.simple_post_to_api("/studies", data, "/studies")
        else:
            self.log.info(
                f"Skip adding already existing study '{study_id}' with study number {study_nbr}"
            )
            study_data = self.get_study_by_key("studyId", study_id)
        # Patch it to add more data
        self.log.info(f"Patching study '{study_id}' with study number {study_nbr}")
        patch_data = copy.deepcopy(import_templates.study_patch)
        # patch_data.update(study_data)
        data = self._copy_parameters_with_values(
            import_data, patch_data, data_new=study_data
        )

        self.fill_high_level_study_design(data)
        self.fill_study_population(data)
        self.fill_study_intervention(data)

        # print(json.dumps(data, indent=2))
        self.api.patch_to_api(data, "/studies/")

    # Read mockup study designs and fill in the corresponding data
    def handle_study_design(self, exported_uid, study_name):
        self.log.info(f"======== Study Design for {study_name} ========")
        # Epochs

        epoch_json = os.path.join(IMPORT_DIR, f"study.{exported_uid}.study-epochs.json")
        self.handle_study_epochs(epoch_json, study_name)
        ## Visits
        visit_json = os.path.join(IMPORT_DIR, f"study.{exported_uid}.study-visits.json")
        self.handle_study_visits(visit_json, study_name)
        # Arms
        arms_json = os.path.join(IMPORT_DIR, f"study.{exported_uid}.study-arms.json")
        self.handle_study_arms(arms_json, study_name)

        # Study branches
        branches_json = os.path.join(
            IMPORT_DIR, f"study.{exported_uid}.study-branch-arms.json"
        )
        self.handle_study_branch_arms(branches_json, study_name)

        # TODO Study cohorts

        # Elements
        elements_json = os.path.join(
            IMPORT_DIR, f"study.{exported_uid}.study-elements.json"
        )
        self.handle_study_elements(elements_json, study_name)
        # Matrix
        matrix_json = os.path.join(
            IMPORT_DIR, f"study.{exported_uid}.study-design-cells.json"
        )
        self.handle_study_matrix(matrix_json, study_name)
        # Activities
        activities_json = os.path.join(
            IMPORT_DIR, f"study.{exported_uid}.study-activities.json"
        )
        self.handle_study_activities(activities_json, study_name)
        # Criteria
        criteria_json = os.path.join(
            IMPORT_DIR, f"study.{exported_uid}.study-criteria.json"
        )
        self.handle_study_template_instances(criteria_json, "criteria", study_name)
        # Objectives
        objective_json = os.path.join(
            IMPORT_DIR, f"study.{exported_uid}.study-objectives.json"
        )
        self.handle_study_template_instances(objective_json, "objective", study_name)
        # Endpoints
        endpoint_json = os.path.join(
            IMPORT_DIR, f"study.{exported_uid}.study-endpoints.json"
        )
        self.handle_study_template_instances(endpoint_json, "endpoint", study_name)
        # Study compounds
        comp_json = os.path.join(
            IMPORT_DIR, f"study.{exported_uid}.study-compounds.json"
        )
        self.handle_study_compounds(comp_json, study_name)

        # Study activity schedule
        sched_json = os.path.join(
            IMPORT_DIR, f"study.{exported_uid}.study-activity-schedules.json"
        )
        self.handle_study_activity_schedules(sched_json, study_name)

    @open_file()
    def handle_study_matrix(self, jsonfile, study_name):
        self.log.info(f"======== Study design matrix for study {study_name} ========")
        study_uid = self.lookup_study_uid_from_id(study_name)
        study_elements = self.api.get_all_from_api(f"/study/{study_uid}/study-elements")

        study_elements = self.map_fields_to_dict(study_elements, "name", "elementUid")
        study_arms = self.api.get_all_from_api(f"/study/{study_uid}/study-arms")
        study_arms = self.map_fields_to_dict(study_arms, "name", "armUid")
        study_branch_arms = self.api.get_all_from_api(
            f"/study/{study_uid}/study-branch-arms"
        )
        study_branch_arms = self.map_fields_to_dict(
            study_branch_arms, "name", "branchArmUid"
        )

        imported = json.load(jsonfile)
        for item in imported:
            data = dict(import_templates.study_design_cell)
            data["activityInstanceUid"] = None
            arm_name = item["studyArmName"]
            if arm_name is not None:
                try:
                    data["studyArmUid"] = self.caseless_dict_lookup(
                        study_arms, arm_name
                    )
                except (StopIteration, AttributeError):
                    self.log.warning(
                        f"Unable to find study arm {arm_name}, skipping this entry"
                    )
            else:
                data["studyArmUid"] = None

            branch_arm_name = item["studyBranchArmName"]
            if branch_arm_name is not None:
                try:
                    data["studyBranchArmUid"] = self.caseless_dict_lookup(
                        study_branch_arms, branch_arm_name
                    )
                except (StopIteration, AttributeError):
                    self.log.warning(f"Unable to find study arm {branch_arm_name}")
            else:
                data["studyBranchArmUid"] = None

            epoch_name = item["studyEpochName"]
            data["studyEpochUid"] = self.lookup_study_epoch_uid(study_uid, epoch_name)
            if data["studyEpochUid"] is not None:
                self.log.info(
                    f"Found study epoch {epoch_name} with uid {data['studyEpochUid']}"
                )
            else:
                self.log.error(
                    f"Unable to find study epoch {epoch_name}, skipping this entry"
                )
                continue

            element_name = item["studyElementName"]
            try:
                data["studyElementUid"] = self.caseless_dict_lookup(
                    study_elements, element_name
                )
            except StopIteration:
                self.log.error(
                    f"Unable to find study element {element_name}, skipping this entry"
                )
                continue
            # print(json.dumps(data, indent=2))
            path = f"/study/{study_uid}/study-design-cells"
            self.log.info(
                f"Add study design cell with epoch '{epoch_name}', arm '{arm_name}', element '{element_name}' for study '{study_name}' with id '{study_uid}'"
            )
            self.api.simple_post_to_api(path, data, "/study-design-cells")

    @open_file()
    def handle_study_activities(self, jsonfile, study_name):
        self.log.info(f"======== Study activities for study {study_name} ========")
        study_uid = self.lookup_study_uid_from_id(study_name)
        imported = json.load(jsonfile)
        for item in imported:
            data = dict(import_templates.study_activity)
            data["activityInstanceUid"] = None
            flow_name = item["flowchartGroup"]["sponsorPreferredName"]
            data["flowchartGroupUid"] = self.lookup_ct_term_uid(
                "Flowchart Group", flow_name
            )
            if data["flowchartGroupUid"] is None:
                self.log.error(
                    f"Unable to find flowchart group {flow_name}, skipping this entry"
                )
                continue
            act_name = item["activity"]["name"]
            data["activityUid"] = self.lookup_activity_uid(act_name)
            if data["activityUid"] is None:
                self.log.error(
                    f"Unable to find activity {act_name}, skipping this entry"
                )
                continue
            # print(json.dumps(data, indent=2))
            path = f"/study/{study_uid}/study-activities/create"
            self.log.info(
                f"Add study activity '{act_name}' with flowchart group '{flow_name}' for study '{study_name}' with id '{study_uid}'"
            )
            self.api.simple_post_to_api(path, data, "/study-activities/create")

    @open_file()
    def handle_study_epochs(self, jsonfile, study_name):
        self.log.info(f"======== Study epochs for study '{study_name}' ========")

        # all_unit_subset_terms = self.api.get_all_identifiers(
        #        self.api.get_all_from_api("/ct/terms/names?codelist_name=Unit Subset"),
        #        identifier="sponsorPreferredName",
        #        value="termUid")
        # study_time_subset_uid = all_unit_subset_terms["Study Time"]

        study_uid = self.lookup_study_uid_from_id(study_name)
        study_epochs = self.api.get_all_from_api(f"/study/{study_uid}/study-epochs")

        epochs_to_add = []
        imported = json.load(jsonfile)

        # Need to sort in order
        def get_order(data):
            return int(data["order"])
        imported.sort(key=get_order)

        for imported_epoch in imported:
            epoch_name = imported_epoch["epochName"]
            if self._check_for_duplicate_epoch(imported_epoch, study_epochs):
                self.log.info(
                    f"Study epoch '{epoch_name}' with description '{imported_epoch['description']}' already exists, skipping"
                )
                continue

            data = dict(import_templates.study_epoch)
            for key in data.keys():
                if "Uid" not in key:
                    data[key] = imported_epoch.get(key, None)

            # Look up study uid
            # study_name = imported_epoch["studyName"]
            data["studyUid"] = study_uid

            # epoch subtype
            epoch_sub_name = imported_epoch["epochSubTypeName"]

            uid = self.lookup_ct_term_uid("Epoch Sub Type", epoch_sub_name)
            if uid:
                self.log.info(
                    f"Found epoch subtype '{epoch_sub_name}' with uid '{uid}'"
                )
                data["epochSubType"] = uid
            else:
                self.log.error(
                    f"Unable to find epoch subtype {epoch_sub_name}, skipping this entry"
                )
                continue

            # duration unit, is this used??
            # "durationUnit": null,

            # print(json.dumps(data, indent=2))

            # We need to call preview to get the correctly numbered Epoch
            self.log.info(
                f"Preview study epoch '{epoch_name}' for study '{study_name}' with id '{study_uid}'"
            )
            path = f"/study/{study_uid}/study-epochs/preview"
            preview_data = {
                "epochSubType": data["epochSubType"],
                "studyUid": data["studyUid"]
                }

            preview = self.api.simple_post_to_api(path, preview_data, "/study-epochs/preview")
            if preview is None:
                self.log.error(
                    f"Unable to preview study epoch {epoch_name}, skipping this entry"
                )
                continue

            # Update epoch from preview result
            data["epoch"] = preview["epoch"]

            path = f"/study/{study_uid}/study-epochs"
            self.log.info(
                f"Add study epoch '{epoch_name}' as '{preview['epochName']}' for study '{study_name}' with id '{study_uid}'"
            )
            if epoch_name != preview['epochName']:
                self.log.warning(
                f"Study epoch '{epoch_name}' changed name to '{preview['epochName']}'"
            )
            self.api.simple_post_to_api(path, data, "/study-epochs")


    @open_file()
    def handle_study_visits(self, jsonfile, study_name):
        self.log.info(f"======== Study visits for study '{study_name}' ========")
        study_uid = self.lookup_study_uid_from_id(study_name)
        study_visits = self.api.get_all_from_api(f"/study/{study_uid}/study-visits")

        imported = json.load(jsonfile)

        # Need to sort in order
        def get_order(data):
            return int(data["uniqueVisitNumber"])

        imported.sort(key=get_order)

        for imported_visit in imported:
            data = dict(import_templates.study_visit)
            if self._check_for_duplicate_visit(imported_visit, study_visits):
                self.log.info(
                    f"Study visit of type '{imported_visit['visitTypeName']}' with description '{imported_visit['description']}' already exists, skipping"
                )
                continue
            # else:
            #    print(json.dumps(imported_visit, indent=2))
            #    print(json.dumps(study_visits, indent=2))

            for key in data.keys():
                if "Uid" not in key:
                    data[key] = imported_visit.get(key, None)

            data["studyUid"] = study_uid

            epoch_name = imported_visit["studyEpochName"]
            data["studyEpochUid"] = self.lookup_study_epoch_uid(study_uid, epoch_name)
            if data["studyEpochUid"] is not None:
                self.log.info(
                    f"Found study epoch {epoch_name} with uid {data['studyEpochUid']}"
                )
            else:
                self.log.error(
                    f"Unable to find study epoch {epoch_name}, skipping this entry"
                )
                continue


            visit_type = imported_visit["visitTypeName"]
            data["visitTypeUid"] = self.lookup_ct_term_uid("VisitType", visit_type)
            if data["visitTypeUid"] is not None:
                self.log.info(
                    f"Found visit type {visit_type} with uid {data['visitTypeUid']}"
                )
            else:
                self.log.error(
                    f"Unable to find visit type {visit_type}, skipping this entry"
                )
                continue

            timeref = imported_visit["timeReferenceName"]
            data["timeReferenceUid"] = self.lookup_ct_term_uid(
                "Time Point Reference", timeref
            )
            if data["timeReferenceUid"] is not None:
                self.log.info(
                    f"Found time ref {timeref} with uid {data['timeReferenceUid']}"
                )
            else:
                self.log.error(
                    f"Unable to find visit time reference {timeref}, skipping this entry"
                )
                continue

            timeunit = imported_visit["timeUnitName"]
            try:
                data["timeUnitUid"] = self.caseless_dict_lookup(
                    self.all_study_times, timeunit
                )
                self.log.info(
                    f"Found time unit {timeunit} with uid {data['timeUnitUid']}"
                )
            except StopIteration:
                self.log.error(
                    f"Unable to find visit time unit {timeunit}, skipping this entry"
                )
                continue

            winunit = imported_visit["visitWindowUnitName"]
            try:
                data["visitWindowUnitUid"] = self.caseless_dict_lookup(
                    self.all_study_times, winunit
                )
                self.log.info(
                    f"Found time window unit {winunit} with uid {data['visitWindowUnitUid']}"
                )
            except StopIteration:
                self.log.error(
                    f"Unable to find visit window unit {winunit}, skipping this entry"
                )
                continue

            contmode = imported_visit["visitContactModeName"]
            data["visitContactModeUid"] = self.lookup_ct_term_uid(
                "Visit Contact Mode", contmode
            )
            if data["visitContactModeUid"] is not None:
                self.log.info(
                    f"Found visit contact mode {contmode} with uid {data['visitContactModeUid']}"
                )
            else:
                self.log.error(
                    f"Unable to find visit contact mode {contmode}, skipping this entry"
                )
                continue

            # Remove any remaining "string" values
            for key, item in data.items():
                if item == "string":
                    # print(f"Cleaning {key}")
                    data[key] = None
            # print(json.dumps(data, indent=2))

            path = f"/study/{study_uid}/study-visits"
            self.log.info(f"Add study visit with desc '{data['description']}'")
            self.api.simple_post_to_api(path, data, "/study-visits")

    @open_file()
    def handle_study_arms(self, jsonfile, study_name):
        self.log.info(f"======== Study arms for study '{study_name}' ========")

        study_uid = self.lookup_study_uid_from_id(study_name)
        study_arms = self.api.get_all_from_api(f"/study/{study_uid}/study-arms")

        imported = json.load(jsonfile)
        for imported_arm in imported:
            if self._check_for_duplicate_arm(imported_arm, study_arms):
                self.log.info(
                    f"Study arm '{imported_arm['name']}' with description '{imported_arm['description']}' already exists, skipping"
                )
                continue

            data = dict(import_templates.study_arm)
            for key in data.keys():
                if "Uid" not in key:
                    data[key] = imported_arm.get(key, None)

            armtype = imported_arm.get("armType", None)
            if armtype is None:
                armtype = {}
            armtype_name = armtype.get("sponsorPreferredName", "")
            if armtype_name == "":
                # Is this an old json? Try getting "type"
                armtype_name = imported_arm.get("type", None)
                if not armtype_name:
                    self.log.error(
                        "Unable to get arm type name from imported data, skipping this entry"
                    )
                    continue
            data["armTypeUid"] = self.lookup_ct_term_uid("Arm Type", armtype_name)
            if data["armTypeUid"] is None:
                self.log.error(
                    f"Unable to find study arm type {armtype_name}, skipping this entry"
                )
                continue

            # duration unit, is this used??
            # "durationUnit": null,

            # print(json.dumps(data, indent=2))
            path = f"/study/{study_uid}/study-arms/create"
            self.log.info(
                f"Add study arm '{imported_arm['name']}' for study '{study_name}' with id '{study_uid}'"
            )
            self.api.simple_post_to_api(path, data, "/study-arms/create")

    @open_file()
    def handle_study_branch_arms(self, jsonfile, study_name):
        self.log.info(f"======== Study branch arms for study '{study_name}' ========")

        study_uid = self.lookup_study_uid_from_id(study_name)
        study_arms = self.api.get_all_from_api(f"/study/{study_uid}/study-arms")
        study_branch_arms = self.api.get_all_from_api(
            f"/study/{study_uid}/study-branch-arms"
        )

        imported = json.load(jsonfile)
        for imported_branch in imported:
            if self._check_for_duplicate_arm(imported_branch, study_branch_arms):
                self.log.info(
                    f"Study branch arm '{imported_branch['name']}' with description '{imported_branch['description']}' already exists, skipping"
                )
                continue

            data = dict(import_templates.study_branch)
            for key in data.keys():
                if "Uid" not in key:
                    data[key] = imported_branch.get(key, None)
            armroot = imported_branch.get("armRoot", {})
            if armroot is None:
                armroot = {}
            arm_name = armroot.get("name", "")

            # TODO!!!
            for arm in study_arms:
                if arm["name"] == arm_name:
                    data["armUid"] = arm["armUid"]
                    break
            if data["armUid"] is None:
                self.log.error(
                    f"Unable to find study arm {arm_name}, skipping this entry"
                )
                continue

            # duration unit, is this used??
            # "durationUnit": null,

            # print(json.dumps(data, indent=2))
            path = f"/study/{study_uid}/study-branch-arms/create"
            self.log.info(
                f"Add study branch arm '{imported_branch['name']}' for study '{study_name}' with id '{study_uid}'"
            )
            self.api.simple_post_to_api(path, data, "/study-branch-arms/create")

    @open_file()
    def handle_study_elements(self, jsonfile, study_name):
        self.log.info(f"======== Study elements for study '{study_name}' ========")
        study_uid = self.lookup_study_uid_from_id(study_name)
        study_elements = self.api.get_all_from_api(f"/study/{study_uid}/study-elements")

        imported = json.load(jsonfile)
        for imported_el in imported:
            if self._check_for_duplicate_element(imported_el, study_elements):
                self.log.info(
                    f"Study element '{imported_el['name']}' with description '{imported_el['description']}' already exists, skipping"
                )
                continue

            data = dict(import_templates.study_element)
            for key in data.keys():
                if "Uid" not in key:
                    data[key] = imported_el.get(key, None)

            element_subtype_name = imported_el.get("elementSubType", {}).get(
                "sponsorPreferredName", ""
            )
            if element_subtype_name == "":
                # Old json files? Try with the old name
                element_subtype_name = imported_el.get("elementSubTypeName", "")
            data["elementSubTypeUid"] = self.lookup_ct_term_uid(
                "Element Sub Type", element_subtype_name
            )
            if data["elementSubTypeUid"] is None:
                self.log.error(
                    f"Unable to find element sub type {element_subtype_name}, skipping this entry"
                )
                continue
            no_treatment_subtypes = ("Screening", "Run-in", "Wash-out", "Follow-up")
            treatment_subtypes = ("Treatment",)

            # TODO why is this called "code"??? makes no sense
            # element_type_name = imported_el["code"]
            if element_subtype_name in no_treatment_subtypes:
                element_type_name = "No Treatment"
            elif element_subtype_name in treatment_subtypes:
                element_type_name = "Treatment"
            else:
                element_type_name = ""

            data["code"] = self.lookup_ct_term_uid("Element Type", element_type_name)
            if data["code"] is None:
                self.log.error(
                    f"Unable to find element type {element_type_name}, skipping this entry"
                )
                continue

            if "plannedDuration" in imported_el and imported_el["plannedDuration"] is not None:
                unit_name = imported_el["plannedDuration"]["durationUnitCode"]["name"]
                uid = self.lookup_unit_uid(unit_name, subset="Age Unit")
                if uid:
                    data["plannedDuration"]["durationUnitCode"]["name"] = unit_name
                    data["plannedDuration"]["durationUnitCode"]["termUid"] = uid
                    data["plannedDuration"]["durationValue"] = imported_el["plannedDuration"]["durationValue"]
                else:
                    self.log.error(
                        f"Unable to find unit {unit_name}, skipping planned duration for this element"
                    )

            # print(json.dumps(data, indent=2))
            path = f"/study/{study_uid}/study-elements/create"
            self.log.info(
                f"Add study arm '{imported_el['name']}' for study '{study_name}' with id '{study_uid}'"
            )
            self.api.simple_post_to_api(path, data, "/study-elements/create")

    def handle_templates(self):
        self.log.info("======== Syntax templates ========")
        objective_template_json = os.path.join(IMPORT_DIR, "objective-templates.json")
        self.handle_all_templates(objective_template_json, "objective")

        criteria_template_json = os.path.join(IMPORT_DIR, "criteria-templates.json")
        self.handle_all_templates(criteria_template_json, "criteria")

        endpoint_template_json = os.path.join(IMPORT_DIR, "endpoint-templates.json")
        self.handle_all_templates(endpoint_template_json, "endpoint")

        timeframe_template_json = os.path.join(IMPORT_DIR, "timeframe-templates.json")
        self.handle_all_templates(timeframe_template_json, "timeframe")

        activity_description_template_json = os.path.join(
            IMPORT_DIR, "activity-description-templates.json"
        )
        self.handle_all_templates(
            activity_description_template_json, "activity_description"
        )

    @open_file()
    def handle_all_templates(self, jsonfile, template_type):
        self.log.info(f"======== {template_type} templates ========")
        import_data = json.load(jsonfile)
        category_codelist = None
        subcategory_codelist = None
        if template_type == "objective":
            post_data = import_templates.objective_template
            category_codelist = "Objective Category"
            path = "/objective-templates"
        elif template_type == "criteria":
            post_data = import_templates.criteria_template
            category_codelist = "Criteria Category"
            subcategory_codelist = "Criteria Sub Category"
            type_codelist = "Criteria Type"
            path = "/criteria-templates"
        elif template_type == "endpoint":
            post_data = import_templates.endpoint_template
            category_codelist = "Endpoint Category"
            path = "/endpoint-templates"
        elif template_type == "timeframe":
            post_data = import_templates.timeframe_template
            path = "/timeframe-templates"
        elif template_type == "activity_description":
            post_data = import_templates.activity_description_template
            category_codelist = None
            subcategory_codelist = None
            path = "/activity-description-templates"
        else:
            raise RuntimeError(f"Unknown template type {template_type}")

        # Create the template
        for imported_template in import_data:
            data = copy.deepcopy(post_data)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    if key in imported_template:
                        value = imported_template.get(key, None)
                        if not isinstance(value, (dict, list, tuple)):
                            data[key] = value
            shortname = data["name"]
            if len(shortname) > 60:
                shortname = shortname[0:60] + "..."
            if self.lookup_template_uid(data["name"], template_type, log=False, shortname=shortname) is not None:
                self.log.info(f"Skipping existing {template_type} template with name '{shortname}'")
                continue
            if "defaultParameterValues" in post_data:
                data["defaultParameterValues"] = []
                parameter_template = post_data["defaultParameterValues"][0]
                value_template = parameter_template["values"][0]
                if (
                    "0" in imported_template["defaultParameterValues"]
                    and imported_template["defaultParameterValues"]["0"] is not None
                ):
                    for parameter in imported_template["defaultParameterValues"]["0"]:
                        paramdata = copy.deepcopy(parameter_template)
                        for key in paramdata.keys():
                            paramdata[key] = parameter.get(key, None)
                        paramdata["values"] = []
                        for val in parameter["values"]:
                            valuedata = copy.deepcopy(value_template)
                            for key in val.keys():
                                if not key.lower().endswith("uid"):
                                    valuedata[key] = val.get(key, None)
                                else:
                                    valuedata[key] = self.lookup_parameter_value_uid(
                                        val.get("name", None), val.get("type", None))
                            paramdata["values"].append(valuedata)
                        # Only include if the parameter has some content
                        if len(paramdata["values"]) > 0:
                            data["defaultParameterValues"].append(paramdata)

            if "indicationUids" in post_data:
                data["indicationUids"] = []
                if imported_template["indications"] is not None:
                    for indication in imported_template["indications"]:
                        name = indication["name"]
                        library = indication["libraryName"]
                        uid = self.lookup_dictionary_term_uid(library, name)
                        if uid:
                            data["indicationUids"].append(uid)
            if "categoryUids" in post_data:
                data["categoryUids"] = []
                if imported_template["categories"] is not None:
                    for category in imported_template["categories"]:
                        name = category["name"]["sponsorPreferredName"]
                        uid = self.lookup_codelist_term_uid(category_codelist, name)
                        if uid:
                            data["categoryUids"].append(uid)
            if "subCategoryUids" in post_data:
                data["subCategoryUids"] = []
                if imported_template["subCategories"] is not None:
                    for category in imported_template["subCategories"]:
                        name = category["name"]["sponsorPreferredName"]
                        uid = self.lookup_codelist_term_uid(subcategory_codelist, name)
                        if uid:
                            data["categoryUids"].append(uid)
            if "activityUids" in post_data:
                data["activityUids"] = []
                if imported_template["activities"] is not None:
                    for act in imported_template["activities"]:
                        name = act["name"]
                        uid = self.lookup_activity_uid(name)
                        if uid:
                            data["activityUids"].append(uid)
            if "activityGroupUids" in post_data:
                data["activityGroupUids"] = []
                if imported_template["activityGroups"] is not None:
                    for group in imported_template["activityGroups"]:
                        name = group["name"]
                        uid = self.lookup_activity_group_uid(name)
                        if uid:
                            data["activityGroupUids"].append(uid)
            if "activitySubGroupUids" in post_data:
                data["activitySubGroupUids"] = []
                if imported_template["activitySubGroups"] is not None:
                    for group in imported_template["activitySubGroups"]:
                        name = group["name"]
                        uid = self.lookup_activity_subgroup_uid(name)
                        if uid:
                            data["activitySubGroupUids"].append(uid)
            if "typeUid" in post_data:
                name = imported_template["type"]["name"]["sponsorPreferredName"]
                uid = self.lookup_codelist_term_uid(type_codelist, name)
                if uid:
                    data["typeUid"] = uid
            if "studyObjectiveUid" in post_data:
                # TODO add this, currently not provided by get endpoint. Used by endpoint templates.
                print("TODO lookup study objective")
            if "endpointUnits" in post_data:
                # TODO add this, currently not provided by get endpoint. Used by endpoint templates.
                print("TODO lookup endpoint units")

            # print("====================  Data to post for", template_type, "templates")
            # print(json.dumps(data, indent=2))
            res = self.api.simple_post_to_api(path, data)
            if res is not None:
                if self.api.approve_item(res["uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.error(
                    f"Failed to add {template_type} template with name '{shortname}'"
                )

    def fill_parameter_values(self, new_data, imported_values, post_template):
        data_complete = True
        if "parameterValues" in post_template:
            new_data["parameterValues"] = []
            parameter_template = post_template["parameterValues"][0]
            value_template = parameter_template["values"][0]
            for parameter in imported_values:
                if "value" in parameter:
                    # TODO what is this??
                    pass
                paramdata = copy.deepcopy(parameter_template)
                for key in paramdata.keys():
                    paramdata[key] = parameter.get(key, None)
                paramdata["values"] = []
                for val in parameter["values"]:
                    valuedata = copy.deepcopy(value_template)
                    uid_found = True
                    for key in val.keys():
                        if not key.lower().endswith("uid"):
                            valuedata[key] = val.get(key, None)
                        else:
                            valuedata[key] = self.lookup_parameter_value_uid(
                                val.get("name", None), val.get("type", None)
                            )
                            if valuedata[key] is None:
                                self.log.warning(f"Could not find parameter value '{val.get('name', '')}")
                                uid_found = False
                                data_complete = False
                    if uid_found:
                        paramdata["values"].append(valuedata)
                # Only include if the parameter has some content
                if len(paramdata["values"]) > 0:
                    new_data["parameterValues"].append(paramdata)
        return data_complete

    def create_timeframe(self, timeframe_data):
        existing_uid = self.lookup_timeframe(timeframe_data["name"])
        if existing_uid is not None:
            return existing_uid
        post_data = import_templates.timeframes
        path = "/timeframes"
        data = copy.deepcopy(post_data)
        for key in data.keys():
            if not key.lower().endswith("uid"):
                if key in timeframe_data:
                    value = timeframe_data.get(key, None)
                    if not isinstance(value, (dict, list, tuple)):
                        data[key] = value
        self.fill_parameter_values(data, timeframe_data["parameterValues"], post_data)
        data["nameOverride"] = None
        data["libraryName"] = timeframe_data["library"]["name"]
        data["timeframeTemplateUid"] = self.lookup_template_uid(
            timeframe_data["timeframeTemplate"]["name"], "timeframe"
        )
        res = self.api.simple_post_to_api(path, data, path)
        if res is not None:
            if self.api.approve_item(res["uid"], path):
                self.log.info("Approve ok")
                self.metrics.icrement(path + "--Approve")
                return res["uid"]
            else:
                self.log.error("Approve failed")
                self.metrics.icrement(path + "--ApproveError")
        else:
            self.log.error(
                f"Failed to add timeframe with name '{timeframe_data['timeframeTemplate']['name']}'"
            )

    @open_file()
    def handle_study_template_instances(self, jsonfile, template_type, study_name):
        self.log.info(f"======== Study {template_type} for study {study_name} =======")
        study_uid = self.lookup_study_uid_from_id(study_name)
        import_data = json.load(jsonfile)
        if template_type == "objective":
            post_data = import_templates.study_objective
            path = f"/study/{study_uid}/study-objectives/create"
        elif template_type == "criteria":
            post_data = import_templates.study_criteria
            path = f"/study/{study_uid}/study-criteria/create"
        elif template_type == "endpoint":
            post_data = import_templates.study_endpoint
            path = f"/study/{study_uid}/study-endpoints/create"
        elif template_type == "activity_description":
            post_data = import_templates.study_activity_description
            path = f"/study/{study_uid}/study-activities/create"
        else:
            raise RuntimeError(f"Unknown type {template_type}")
        mapper = ENDPOINT_TO_KEY_MAP[template_type]
        path = f"/study/{study_uid}/{mapper['post']}"

        data_key_import = f"{template_type}Data"
        data_key_export = template_type
        # Create the template instance
        for imported_template in import_data:
            instance = imported_template[data_key_export]
            if not instance:
                continue
            instance_name = instance.get("name")
            if (
                self.lookup_study_template_instance_uid(
                    instance_name, study_uid, template_type
                )
                is not None
            ):
                self.log.info(
                    f"Skipping existing {template_type} with name {instance_name}"
                )
                continue
            data = copy.deepcopy(post_data)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    if key in imported_template:
                        value = imported_template.get(key, None)
                        if not isinstance(value, (dict, list, tuple)):
                            data[key] = value
            parameters_complete = self.fill_parameter_values(
                data[data_key_import],
                instance["parameterValues"],
                post_data[data_key_import],
            )
            if not parameters_complete:
                self.log.error(f"Missing parameter values, skipping template instance '{instance_name}'")
                continue
            if f"{template_type}TemplateUid" in post_data[data_key_import]:
                data[data_key_import][
                    f"{template_type}TemplateUid"
                ] = self.lookup_template_uid(
                    instance[f"{template_type}Template"]["name"], template_type
                )
            if "nameOverride" in post_data[data_key_import]:
                data[data_key_import][
                    "nameOverride"
                ] = None  # imported_template[data_key_export]["name"]
            if "libraryName" in post_data[data_key_import]:
                data[data_key_import]["libraryName"] = instance["library"]["name"]
            if "objectiveLevelUid" in post_data:
                data["objectiveLevelUid"] = self.lookup_codelist_term_uid(
                    "Objective Level",
                    imported_template["objectiveLevel"]["sponsorPreferredName"],
                )
            if "studyObjectiveUid" in post_data:
                name = imported_template["studyObjective"]["objective"]["name"]
                data["studyObjectiveUid"] = self.lookup_study_template_instance_uid(
                    name, study_uid, "objective"
                )
            if "endpointLevelUid" in post_data:
                if imported_template["endpointLevel"] is not None:
                    data["endpointLevelUid"] = self.lookup_codelist_term_uid(
                        "Endpoint Level",
                        imported_template["endpointLevel"]["sponsorPreferredName"],
                    )
                else:
                    data["endpointLevelUid"] = None
            if "endpointSubLevelUid" in post_data:
                if imported_template["endpointSubLevel"] is not None:
                    data["endpointSubLevelUid"] = self.lookup_codelist_term_uid(
                        "Endpoint Sub Level",
                        imported_template["endpointSubLevel"]["sponsorPreferredName"],
                    )
                else:
                    data["endpointSubLevelUid"] = None
            if "endpointUnits" in post_data:
                # TODO add this once fixed in api!
                # The endpoint currently doesn't provide the unit name, only uid.
                data["endpointUnits"] = {"units": [], "separator": None}
            if "timeframeUid" in post_data:
                if imported_template["timeframe"] is not None:
                    data["timeframeUid"] = self.create_timeframe(
                        imported_template["timeframe"]
                    )
                else:
                    data["timeframeUid"] = None

            # TODO check for duplicates before posting
            #print(json.dumps(data, indent=2))
            res = self.api.simple_post_to_api(path, data, path)
            if res is None:
                self.log.error(f"Failed to add {template_type} template")

    @open_file()
    def handle_compound_aliases(self, jsonfile):
        self.log.info("======== Compound aliases ========")
        import_data = json.load(jsonfile)
        for alias in import_data:
            data = copy.deepcopy(import_templates.compound_alias)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    value = alias.get(key, None)
                    if not isinstance(value, (dict, list, tuple)):
                        data[key] = value
            data["compoundUid"] = self.lookup_compound_uid(alias["compound"]["name"])
            path = "/concepts/compound-aliases"
            res = self.api.simple_post_to_api(path, data, "/concepts/compound-aliases")
            if res is not None:
                if self.api.approve_item(res["uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add compound alias '{data['name']}'")

    @open_file()
    def handle_compounds(self, jsonfile):
        self.log.info("======== Compounds ========")
        import_data = json.load(jsonfile)
        for comp in import_data:
            data = copy.deepcopy(import_templates.compound)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    if key in comp:
                        value = comp.get(key, None)
                        if not isinstance(value, (dict, list, tuple)):
                            data[key] = value
            for device in comp["deliveryDevices"]:
                name = device["name"]
                uid = self.lookup_codelist_term_uid("Delivery Device", name)
                self.append_if_not_none(data["deliveryDevicesUids"], uid)
            for disp in comp["dispensers"]:
                name = disp["name"]
                uid = self.lookup_codelist_term_uid("Compound Dispensed In", name)
                self.append_if_not_none(data["dispensersUids"], uid)
            for dose in comp["doseValues"]:
                uid = self.create_or_get_numeric_value(dose, "Dose Unit")
                self.append_if_not_none(data["doseValuesUids"], uid)
            for dose in comp["strengthValues"]:
                uid = self.create_or_get_numeric_value(dose, "Dose Unit")
                self.append_if_not_none(data["strengthValuesUids"], uid)
            for dose in comp["lagTimes"]:
                uid = self.create_or_get_lag_time(dose)
                self.append_if_not_none(data["lagTimesUids"], uid)
            for dose in comp["doseFrequencies"]:
                # TODO get some data that uses this
                uid = self.create_or_get_numeric_value(dose, "TODO")
                self.append_if_not_none(data["doseFrequencyUids"], uid)
            uid = self.create_or_get_numeric_value(comp["halfLife"], "Age Unit")
            data["halfLifeUid"] = uid
            # print(json.dumps(data, indent=2))
            path = "/concepts/compounds"
            res = self.api.simple_post_to_api(path, data, "/concepts/compounds")
            if res is not None:
                if self.api.approve_item(res["uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add compound '{data['name']}'")

    def create_or_get_numeric_value(self, value, subset):
        if value is None:
            return None
        data = copy.deepcopy(import_templates.numeric_value_with_unit)
        for key in data.keys():
            if not key.lower().endswith("uid"):
                data[key] = value.get(key, data[key])
        data["unitDefinitionUid"] = self.lookup_unit_uid(
            value["unitLabel"], subset=subset
        )
        data["libraryName"] = "Sponsor"
        for key, val in data.items():
            if val == "string":
                data[key] = None
        val = self.api.simple_post_to_api("/concepts/numeric-values-with-unit", data)
        if val is not None:
            return val.get("uid", None)

    def create_or_get_lag_time(self, value):
        data = copy.deepcopy(import_templates.lag_time)
        for key in data.keys():
            if not key.lower().endswith("uid"):
                data[key] = value.get(key, data[key])
        data["unitDefinitionUid"] = self.lookup_unit_uid(
            value["unitLabel"], subset="Age Unit"
        )
        data["sdtmDomainUid"] = self.lookup_ct_term_uid(
            "SDTM Domain Abbreviation", value["sdtmDomainLabel"]
        )
        data["libraryName"] = "Sponsor"
        for key, val in data.items():
            if val == "string":
                data[key] = None
        # print(json.dumps(data, indent=2))
        val = self.api.simple_post_to_api("/concepts/lag-times", data)
        if val is not None:
            return val.get("uid", None)

    @open_file()
    def handle_study_compounds(self, jsonfile, study_name):
        self.log.info(f"======== Study compounds for study {study_name} ========")
        study_uid = self.lookup_study_uid_from_id(study_name)
        imported = json.load(jsonfile)
        existing = self.fetch_study_compounds(study_uid)
        for item in imported:
            if self._check_for_duplicate_study_compound(item, existing):
                self.log.info(f"Skipping existing study compound '{item['compoundAlias']['name']}'")
                continue
            data = dict(import_templates.study_compound)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    data[key] = item.get(key, data[key])
            if item["compoundAlias"] is not None:
                data["compoundAliasUid"] = self.lookup_compound_alias_uid(
                    item["compoundAlias"]["name"]
                )
            if item["strengthValue"] is not None:
                data["strengthValueUid"] = self.create_or_get_numeric_value(
                    item["strengthValue"], "Dose Unit"
                )
            if item["device"] is not None:
                data["deviceUid"] = self.lookup_codelist_term_uid(
                    "Delivery Device", item["device"]["name"]
                )
            if item["dispensedIn"] is not None:
                data["dispensedInUid"] = self.lookup_codelist_term_uid(
                    "Compound Dispensed In", item["dispensedIn"]["name"]
                )
            if item["reasonForMissingNullValue"] is not None:
                data["reasonForMissingNullValueUid"] = self.lookup_ct_term_uid(
                    "Null Flavor", item["reasonForMissingNullValue"]["name"]
                )
            if item["typeOfTreatment"] is not None:
                data["typeOfTreatmentUid"] = self.lookup_codelist_term_uid(
                    "Type of Treatment", item["typeOfTreatment"]["name"]
                )
            if item["routeOfAdministration"] is not None:
                data["routeOfAdministrationUid"] = self.lookup_codelist_term_uid(
                    "Route of Administration", item["routeOfAdministration"]["name"]
                )
            if item["dosageForm"] is not None:
                data["dosageFormUid"] = self.lookup_codelist_term_uid(
                    "Pharmaceutical Dosage Form", item["dosageForm"]["name"]
                )
            # TODO handle formulation
            # "formulationUid": "formulation"/"name"??

            # Remove any remaining "string" values
            for key, val in data.items():
                if val == "string":
                    # print(f"Cleaning {key}")
                    data[key] = None
            # print(json.dumps(data, indent=2))
            # TODO check for existing to avoid duplicates! Need to check nearly all fields..
            path = f"/study/{study_uid}/study-compounds/select"
            self.log.info(
                f"Add study compound '{item['compoundAlias']['name']}' for study '{study_name}' with id '{study_uid}'"
            )
            self.api.simple_post_to_api(path, data)

    @open_file()
    def handle_study_activity_schedules(self, jsonfile, study_name):
        self.log.info(f"======== Study activity schedules for study {study_name} ========")
        study_uid = self.lookup_study_uid_from_id(study_name)
        imported = json.load(jsonfile)
        for item in imported:
            data = dict(import_templates.study_activity_schedule)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    data[key] = item.get(key, data[key])
            data["studyActivityUid"] = self.lookup_study_activity_uid(study_uid, item["studyActivityName"])
            data["studyVisitUid"] = self.lookup_study_visit_uid(study_uid, item["studyVisitName"])
            path = f"/study/{study_uid}/study-activity-schedules"
            self.log.info(
                f"Schedule activity '{item['studyActivityName']}' to visit '{item['studyVisitName']}'"
            )
            self.api.simple_post_to_api(path, data)

    @open_file()
    def handle_dictionaries(self, jsonfile, dict_name):
        self.log.info(f"======== Dictionary {dict_name} ========")
        imported = json.load(jsonfile)
        codelist_uid = self.lookup_dictionary_uid(dict_name)
        existing_terms = self.fetch_dictionary_terms(dict_name)
        existing_names = [term["name"] for term in existing_terms]
        for term in imported:
            name = term.get("name")
            if name in existing_names:
                self.log.info(f"Skipping existing term '{name}'")
                continue
            data = dict(import_templates.dictionary_term)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    data[key] = term.get(key, data[key])
            data["codelistUid"] = codelist_uid

            path = "/dictionaries/terms"
            self.log.info(f"Adding term '{name}' to dictionary '{dict_name}' with uid '{codelist_uid}'")
            res = self.api.simple_post_to_api(path, data)
            if res is not None:
                if self.api.approve_item(res["termUid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add ct term '{data['name']}'")

    @open_file()
    def handle_ct_extensions(self, jsonfile, codelist_name):
        self.log.info(f"======== CT extensions for {codelist_name} ========")
        imported = json.load(jsonfile)
        codelist_uid = self.lookup_ct_codelist_uid(codelist_name)
        existing_terms = self.fetch_codelist_terms("Unit")
        existing_names = [term["name"]["sponsorPreferredName"] for term in existing_terms]
        for term in imported:
            name = term.get("name", {}).get("sponsorPreferredName")
            if name in existing_names:
                self.log.info(f"Skipping existing term '{name}'")
                continue
            data = dict(import_templates.ct_term)
            data["catalogueName"] = term.get("catalogueName")
            data["codelistUid"] = codelist_uid
            data["codeSubmissionValue"] = term.get("attributes", {}).get("codeSubmissionValue")
            data["nameSubmissionValue"] = term.get("attributes", {}).get("nameSubmissionValue")
            data["nciPreferredName"] = term.get("attributes", {}).get("nciPreferredName")
            data["definition"] = term.get("attributes", {}).get("definition")
            data["sponsorPreferredName"] = term.get("name", {}).get("sponsorPreferredName")
            data["sponsorPreferredNameSentenceCase"] = term.get("name", {}).get("sponsorPreferredNameSentenceCase")
            data["order"] = term.get("name", {}).get("order")
            data["libraryName"] = term.get("libraryName")

            path = "/ct/terms"
            self.log.info(f"Adding term '{name}' to codelist '{codelist_name}' with uid '{codelist_uid}'")
            res = self.api.simple_post_to_api(path, data)
            if res is not None:
                if self.api.approve_item_names_and_attributes(res["termUid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add ct term '{data['sponsorPreferredName']}'")

    @open_file()
    def handle_unit_definitions(self, jsonfile):
        self.log.info("======== Unit definitions ========")
        imported = json.load(jsonfile)
        for unit in imported:
            name = unit["name"]
            existing = self.lookup_concept_uid(name, "unit-definitions")
            if existing:
                self.log.info(f"Skipping existing unit '{name}'")
                continue
            data = dict(import_templates.unit_definition)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    data[key] = unit.get(key, data[key])
            data["ctUnits"] = []
            for ct in unit["ctUnits"]:
                uid = self.lookup_ct_term_uid("Unit", ct["name"])
                if uid is not None:
                    data["ctUnits"].append(uid)
            data["unitSubsets"] = []
            for ct in unit["unitSubsets"]:
                uid = self.lookup_ct_term_uid("Unit Subset", ct["name"])
                if uid is not None:
                    data["unitSubsets"].append(uid)
            if unit["ucum"] is not None:
                data["ucum"] = self.lookup_dictionary_term_uid(
                    "UCUM", unit.get("ucum", {}).get("name", None)
                )
            if unit["unitDimension"] is not None:
                data["unitDimension"] = self.lookup_codelist_term_uid(
                    "Unit Dimension", unit.get("unitDimension", {}).get("name", None)
                )
            path = "/concepts/unit-definitions"
            res = self.api.simple_post_to_api(path, data)
            if res is not None:
                if self.api.approve_item(res["uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add unit definition '{data['name']}'")

    @open_file()
    def handle_activity_groups(self, jsonfile):
        self.log.info("======== Activity groups ========")
        imported = json.load(jsonfile)
        existing_groups = self.fetch_all_activity_groups()
        existing_names = list(existing_groups.keys())
        for group in imported:
            name = group["name"]
            if name in existing_names:
                self.log.info(f"Skipping existing activity group '{name}'")
                continue
            data = dict(import_templates.activity_groups)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    data[key] = group.get(key, data[key])
            path = "/concepts/activities/activity-groups"
            res = self.api.simple_post_to_api(path, data)
            if res is not None:
                if self.api.approve_item(res["uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add activity '{data['name']}'")

    @open_file()
    def handle_activity_subgroups(self, jsonfile):
        self.log.info("======== Activity sub groups ========")
        imported = json.load(jsonfile)
        existing_groups = self.fetch_all_activity_subgroups()
        existing_names = list(existing_groups.keys())
        for group in imported:
            name = group["name"]
            if name in existing_names:
                self.log.info(f"Skipping existing activity sub group '{name}'")
                continue
            data = dict(import_templates.activity_groups)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    data[key] = group.get(key, data[key])

            # Support data from the old api where activity subgroups could belong to more than one group.
            if "activityGroups" in group:
                if group["activityGroups"] is not None and len(group["activityGroups"]) > 0:
                    group["activityGroup"] = group["activityGroups"][0]
                    if len(group["activityGroups"]) > 1:
                        self.log.warning(f"Migrating legacy activity subgroup '{name}' which was part of several groups, keeping a single group only.")
            if group["activityGroup"] is not None:
                uid = self.lookup_activity_group_uid(group["activityGroup"]["name"])
                if uid:
                    data["activityGroup"] = uid
            path = "/concepts/activities/activity-sub-groups"
            res = self.api.simple_post_to_api(path, data)
            if res is not None:
                if self.api.approve_item(res["uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add activity '{data['name']}'")

    @open_file()
    def handle_activities(self, jsonfile):
        self.log.info("======== Activities ========")
        imported = json.load(jsonfile)
        existing_activities = self.fetch_all_activities()
        existing_names = list(existing_activities.keys())
        for activity in imported:
            name = activity["name"]
            if name in existing_names:
                self.log.info(f"Skipping existing activity '{name}'")
                continue
            data = dict(import_templates.activity)
            for key in data.keys():
                if not key.lower().endswith("uid"):
                    data[key] = activity.get(key, data[key])

            # Support data from the old api where activities could belong to more than one subgroup.
            if "activitySubGroups" in activity and len(activity["activitySubGroups"]) > 0:
                # Keep only the first one
                activity["activitySubGroup"] = activity["activitySubGroups"][0]
                if len(activity["activitySubGroups"]) > 1:
                        self.log.warning(f"Migrating legacy activity '{name}' which was part of several subgroups, keeping a single subgroup only.")

            if "activitySubGroup" in activity:
                subgrp_name = activity["activitySubGroup"]["name"]
                uid = self.lookup_activity_subgroup_uid(subgrp_name)
                data["activitySubGroup"] = uid

            path = "/concepts/activities/activities"
            res = self.api.simple_post_to_api(path, data)
            if res is not None:
                if self.api.approve_item(res["uid"], path):
                    self.log.info("Approve ok")
                    self.metrics.icrement(path + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(path + "--ApproveError")
            else:
                self.log.warning(f"Failed to add activity '{data['name']}'")

    def run(self):
        self.log.info("Migrating json mock data")

        # TODO Clinical programmes
        #if MDR_MIGRATION_EXPORTED_PROGRAMMES:
        #   programmes_json = os.path.join(IMPORT_DIR, "clinical-programmes.json")
        #   self.handle_clinical_programmes(programmes_json)
        #else:
        #    self.log.info("Skipping clinical programmes")

        # TODO Brands
        #if MDR_MIGRATION_EXPORTED_BRANDS:
        #   brands_json = os.path.join(IMPORT_DIR, "brands.json")
        #   self.handle_brands(brands_json)
        #else:
        #    self.log.info("Skipping brands")

        # Dictionaries
        snomed_json = os.path.join(IMPORT_DIR, "dictionaries.SNOMED.json")
        self.handle_dictionaries(snomed_json, "SNOMED")
        unii_json = os.path.join(IMPORT_DIR, "dictionaries.UNII.json")
        self.handle_dictionaries(unii_json, "UNII")
        medrt_json = os.path.join(IMPORT_DIR, "dictionaries.MED-RT.json")
        self.handle_dictionaries(medrt_json, "MED-RT")
        ucum_json = os.path.join(IMPORT_DIR, "dictionaries.UCUM.json")
        self.handle_dictionaries(ucum_json, "UCUM")

        # Unit definitions
        units_ct_json = os.path.join(IMPORT_DIR, "ct.terms.Unit.json")
        self.handle_ct_extensions(units_ct_json, "Unit")

        # Unit definitions
        if MDR_MIGRATION_EXPORTED_UNITS:
            units_json = os.path.join(IMPORT_DIR, "concepts.unit-definitions.json")
            self.handle_unit_definitions(units_json)
        else:
            self.log.info("Skipping units")

        # Activities
        if MDR_MIGRATION_EXPORTED_ACTIVITIES:
            act_grp_json = os.path.join(IMPORT_DIR, "concepts.activities.activity-groups.json")
            self.handle_activity_groups(act_grp_json)
            act_subgrp_json = os.path.join(IMPORT_DIR, "concepts.activities.activity-sub-groups.json")
            self.handle_activity_subgroups(act_subgrp_json)
            act_json = os.path.join(IMPORT_DIR, "concepts.activities.activities.json")
            self.handle_activities(act_json)
        else:
            self.log.info("Skipping activities")

        # TODO Activity instances

        # Compounds and compound aliases
        if MDR_MIGRATION_EXPORTED_COMPOUNDS:
            compounds_json = os.path.join(IMPORT_DIR, "concepts.compounds.json")
            self.handle_compounds(compounds_json)
            comp_alias_json = os.path.join(IMPORT_DIR, "concepts.compound-aliases.json")
            self.handle_compound_aliases(comp_alias_json)
        else:
            self.log.info("Skipping compounds")

        # Syntax templates
        if MDR_MIGRATION_EXPORTED_TEMPLATES:
            self.handle_templates()
        else:
            self.log.info("Skipping syntax templates")

        # Projects
        if MDR_MIGRATION_EXPORTED_PROJECTS:
            self.handle_projects(IMPORT_PROJECTS)
        else:
            self.log.info("Skipping projects")

        # Studies with study design
        if MDR_MIGRATION_EXPORTED_STUDIES:
            studies_json = os.path.join(IMPORT_DIR, "studies.json")
            self.handle_studies(studies_json)
        else:
            self.log.info("Skipping studies")

        self.log.info("Done migrating json mock data")


def main():
    metr = Metrics()
    migrator = MockdataJson(metrics_inst=metr)
    migrator.run()
    migrator.print_cache_stats()
    metr.print()


if __name__ == "__main__":
    main()
