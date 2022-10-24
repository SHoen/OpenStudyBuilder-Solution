from importers.metrics import Metrics
from os import environ
import os
import csv
from typing import Optional, Sequence, Any
import re
from aiohttp_trace import request_tracer
import json

from importers.functions.utils import load_env
from importers.functions.parsers import map_boolean
from importers.importer import BaseImporter, open_file

metrics = Metrics()

API_HEADERS = {"Accept": "application/json"}

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")

MDR_MIGRATION_STUDY = load_env("MDR_MIGRATION_STUDY")
MDR_MIGRATION_STUDY_TYPE = load_env("MDR_MIGRATION_STUDY_TYPE")
MDR_MIGRATION_PROJECTS = load_env("MDR_MIGRATION_PROJECTS")

MDR_MOCKUP_OBJECTIVES_OBJECTS = load_env("MDR_MOCKUP_OBJECTIVES_OBJECTS")
MDR_MOCKUP_ENDPOINTS_OBJECTS = load_env("MDR_MOCKUP_ENDPOINTS_OBJECTS")
MDR_MOCKUP_TIMEFRAMES_OBJECTS = load_env("MDR_MOCKUP_TIMEFRAMES_OBJECTS")
MDR_MOCKUP_STUDY_OBJECTIVES = load_env("MDR_MOCKUP_STUDY_OBJECTIVES")
MDR_MOCKUP_STUDY_ENDPOINTS = load_env("MDR_MOCKUP_STUDY_ENDPOINTS")


# ---------------------------------------------------------------
# ETL for mockup
# ---------------------------------------------------------------
#
# Library objects
objective_template_mapper = {
    "OBJECTIVE": lambda row, headers: {
        "path": "/objective-templates",
        "body": {
            "name": row[headers.index("name")],
            "libraryName": row[headers.index("library")],
            "indicationUids": [],
            "cathegoryUids": [],
        },
    }
}

objective_mapper = {
    "OBJECTIVE": lambda row, headers: {
        "path": "/objectives",
        "name": row[headers.index("name")],
        "libraryName": row[headers.index("library")],
        "first_value": row[headers.index("first_value")],
        "first_conjunction": row[headers.index("first_conjunction")],
        "second_value": row[headers.index("second_value")],
        "second_conjunction": row[headers.index("second_conjunction")],
    }
}

endpoint_template_mapper = {
    "ENDPOINT": lambda row, headers: {
        "path": "/endpoint-templates",
        "body": {
            "name": row[headers.index("name")],
            "libraryName": row[headers.index("library")],
        },
    }
}

endpoint_mapper = {
    "ENDPOINT": lambda row, headers: {
        "path": "/endpoints",
        "name": row[headers.index("name")],
        "libraryName": row[headers.index("library")],
        "first_value": row[headers.index("first_value")],
        "first_conjunction": row[headers.index("first_conjunction")],
        "second_value": row[headers.index("second_value")],
        "second_conjunction": row[headers.index("second_conjunction")],
    }
}

timeframe_template_mapper = {
    "TIMEFRAME": lambda row, headers: {
        "path": "/timeframe-templates",
        "body": {
            "name": row[headers.index("name")],
            "libraryName": row[headers.index("library")],
        },
    }
}

timeframe_mapper = {
    "TIMEFRAME": lambda row, headers: {
        "path": "/timeframes",
        "name": row[headers.index("name")],
        "libraryName": row[headers.index("library")],
        "first_value": row[headers.index("first_value")],
        "first_conjunction": row[headers.index("first_conjunction")],
        "second_value": row[headers.index("second_value")],
        "second_conjunction": row[headers.index("second_conjunction")],
    }
}

# Study
study_mapper = {
    "STUDY": lambda row, headers: {
        "" "path": "/studies",
        "body": {
            "studyNumber": row[headers.index("IMPACT_NUM")],
            "studyAcronym": "",  # row[headers.index("TRL_ID")]
            "projectNumber": row[headers.index("PROJ")],
        },
        "patch": {
            "ctGovId": row[headers.index("CLINICAL_TRIALS_GOV")],
            "eudractId": row[headers.index("EUDRACT_NUM")],
        },
    },
    "STUDY_TYPE": lambda row, headers: {
        "patch": {
            "studyNumber": row[headers.index("IMPACT_NUM")],
            "studyDefineParamName": row[headers.index("TSPARAM")],
            "cValue": row[headers.index("TSVAL")],
            "cCode": row[headers.index("TSVALCD")],
        },
        "componentMappings": {
            "Intervention Model": "studyIntervention",
            "Trial is Randomized": "studyIntervention",
            "Trial Blinding Schema": "studyIntervention",
            "Control Type Response": "studyIntervention",
            "Trial Title": "studyDescription",
            "Trial Phase Classification": "highLevelStudyDesign",
            "Trial Type Response": "highLevelStudyDesign",
        },
        "parameterMappings": {
            "Intervention Model": "interventionModelCode",
            "Trial is Randomized": "isTrialRandomised",
            "Trial Blinding Schema": "trialBlindingSchemaCode",
            "Control Type Response": "controlTypeCode",
            "Trial Title": "studyTitle",
            "Trial Phase Classification": "trialPhaseCode",
            "Trial Type Response": "trialTypeCodes",
        },
    },
}


# project
project_mapper = {
    "PROJECT": lambda row, headers: {
        "" "path": "/projects",
        "clinical_programme_path": "/clinical-programmes",
        "body": {
            "projectNumber": row[headers.index("project_code")],
            "name": row[headers.index("project_name")],
            "brandName": row[headers.index("brand_name")],
            "description": row[headers.index("description")],
            "clinicalProgrammeUid": "temp",
        },
        "clinical_programme_body": {
            "name": row[headers.index("clinical_programme_name")]
        },
    }
}


class Mockdata(BaseImporter):
    logging_name = "mockdata"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)
        self.all_activity_instances = self.api.get_all_activity_objects(
            "activity-instances"
        )
        self.template_parameters_dict = self.get_template_parameter_values()
        self.all_studies_dict = self.api.get_studies_as_dict()

    ### Helper functions
    def get_template_parameter_values(self):
        values = {}
        for res in self.all_activity_instances:
            values[res["name"]] = res
        return values

    # Handler for templates for objective, timeframe and endpoint
    def handle_templates(self, csvfile, mapper):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        for row in readCSV:
            data = mapper(row, headers)
            self.log.info(f"Adding template '{data['body']['name']}'")
            res = self.api.post_to_api(data)
            if res is not None:
                if self.api.approve_item(res["uid"], data["path"] + "/"):
                    self.log.info(f"Approved template '{data['body']['name']}'")
                    self.metrics.icrement(data["path"] + "--Approve")
                else:
                    self.log.error(
                        f"Failed to approve template '{data['body']['name']}'"
                    )
                    self.metrics.icrement(data["path"] + "--ApproveError")

    # Handler for objective, timeframe and endpoint
    def general_handler(self, csvfile, objecttype, mapper):
        self.log.info(f"Fetching existing templates for {objecttype}")
        templates = self.api.get_templates_as_dict(f"/{objecttype}-templates")

        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        for row in readCSV:
            _class = objecttype.upper()
            data = mapper[_class](row, headers)
            # get the objectives
            if data["name"] in templates:
                template = templates[data["name"]]
            else:
                self.log.error(
                    "%s template with name %s is not found", objecttype, data["name"]
                )
                self.metrics.icrement(data["path"] + "--ERROR")
                continue
            # get the values correctly with the conjections
            parameter_values = []
            types = []
            for temp_type in re.findall("\[.*?\]", template["name"]):
                types.append(temp_type.replace("[", "").replace("]", ""))

            # first value
            if data["first_value"]:
                first_value = data["first_value"]
                if "+" in first_value:
                    all_values = first_value.split("+")
                else:
                    all_values = [first_value]
                values = self.create_values(all_values, types[0])
                if values is None:
                    continue
                if data["first_conjunction"]:
                    conjunction = data["first_conjunction"]
                else:
                    conjunction = ""
                parameter_values.append(
                    {"values": values, "conjunction": conjunction, "position": 1}
                )
            if data["second_value"]:
                second_value = data["second_value"]
                if "+" in second_value:
                    all_values = second_value.split()
                else:
                    all_values = [second_value]
                values = self.create_values(all_values, types[1])
                if values is None:
                    continue
                if data["second_conjunction"]:
                    conjunction = data["second_conjunction"]
                else:
                    conjunction = ""
                parameter_values.append(
                    {"values": values, "conjunction": conjunction, "position": 2}
                )
            body = {
                "parameterValues": parameter_values,
                f"{objecttype}TemplateUid": template["uid"],
                "libraryName": data["libraryName"],
            }
            self.log.info(
                f"Adding '{objecttype}' with name '{data['name']}' to library '{data['libraryName']}'"
            )
            res = self.api.post_to_api({"body": body, "path": data["path"]})
            if res is not None:
                if self.api.approve_item(res["uid"], data["path"] + "/"):
                    self.log.info("Approve ok")
                    self.metrics.icrement(data["path"] + "--Approve")
                else:
                    self.log.error("Approve failed")
                    self.metrics.icrement(data["path"] + "--ApproveError")
            else:
                self.log.error(
                    f"Failed to add '{objecttype}' with name '{data['name']}' to library '{data['libraryName']}'"
                )

    def create_values(self, all_values, value_type):
        values = []
        index = 1
        for value_name in all_values:
            if value_name in self.template_parameters_dict:
                value = self.template_parameters_dict[value_name]
            else:
                self.log.warning(
                    "template parameter with name %s is not found", value_name
                )
                # self.metrics.icrement(data["path"] + "--TEMPLATE_PARAMATER_VALUE_DOES_NOT_EXISTS")
                return None
            new_value = {}
            new_value["uid"] = value["uid"]
            new_value["name"] = value["name"]
            new_value["type"] = value_type
            new_value["index"] = index
            index += 1
            values.append(new_value)
        return values

    # Adding objevtive templates and approving them
    @open_file()
    def handle_objective_templates(self, csvfile):
        mapper = objective_template_mapper["OBJECTIVE"]
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        snomed_uid = self.api.find_dictionary_uid("SNOMED")
        all_cathegories = self.api.get_terms_for_codelist_name("Objective Category")

        for row in readCSV:
            data = mapper(row, headers)
            indications = row[headers.index("indication")]
            if indications != "":
                for ind in indications.split("|"):
                    uid = self.api.find_dictionary_item_uid_from_name(snomed_uid, ind)
                    if uid is not None:
                        data["body"]["indicationUids"].append(uid)
                    else:
                        self.log.warning(f"Unable to find indication {ind}")

            cathegories = row[headers.index("cathegory")]
            if cathegories != "":
                for cat in cathegories.split("|"):
                    uid = self.get_uid_for_sponsor_preferred_name(all_cathegories, cat)
                    if uid is not None:
                        data["body"]["cathegoryUids"].append(uid)
                    else:
                        self.log.warning(f"Unable to find cathegory {cat}")
            testing = row[headers.index("testing")]
            if testing.lower() == "yes":
                data["body"]["confirmatoryTesting"] = True
            elif testing.lower() == "no":
                data["body"]["confirmatoryTesting"] = False
            self.log.info(f"Adding template '{data['body']['name']}'")
            res = self.api.post_to_api(data)
            if res is not None:
                if self.api.approve_item(res["uid"], data["path"] + "/"):
                    self.log.info(f"Approved template '{data['body']['name']}'")
                    self.metrics.icrement(data["path"] + "--Approve")
                else:
                    self.log.error(
                        f"Failed to approve template '{data['body']['name']}'"
                    )
                    self.metrics.icrement(data["path"] + "--ApproveError")

    # Adding objectives and approving them
    @open_file()
    def handle_objectives(self, csvfile):
        mapper = objective_mapper
        self.general_handler(csvfile, "objective", mapper)

    # Adding endpoint templates and approving them
    @open_file()
    def handle_endpoint_templates(self, csvfile):
        mapper = endpoint_template_mapper["ENDPOINT"]
        self.handle_templates(csvfile, mapper)

    # Adding endpoint and approving them
    @open_file()
    def handle_endpoints(self, csvfile):
        mapper = endpoint_mapper
        self.general_handler(csvfile, "endpoint", mapper)

    # Adding timeframe templates and approving them
    @open_file()
    def handle_timeframe_templates(self, csvfile):
        mapper = timeframe_template_mapper["TIMEFRAME"]
        self.handle_templates(csvfile, mapper)

    # Adding timeframe and approving them
    @open_file()
    def handle_timeframes(self, csvfile):
        mapper = timeframe_mapper
        self.general_handler(csvfile, "timeframe", mapper)

    # Study objectives
    @open_file()
    def handle_study_objectives(self, csvfile):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        all_studies_dict = self.api.get_studies_as_dict()
        for row in readCSV:
            study_id = row[headers.index("study_id")]
            if study_id in all_studies_dict:
                study = all_studies_dict[study_id]
            else:
                self.log.warning("Study with Study Id '%s' is not found", study_id)
                self.metrics.icrement(
                    "/study-objectives/select/" + "--STUDY_ID_DOES_NOT_EXISTS"
                )
                continue
            objective_name = row[headers.index("objective")]
            objective = self.api.find_object_by_name(objective_name, "/objectives")
            if objective is None:
                objective_uid = ""
            else:
                objective_uid = objective["uid"]
            objective_level = row[headers.index("objective_level")]
            body = {"objectiveUid": objective_uid, "objectiveLevelUid": objective_level}
            self.log.info(
                f"Add study objective '{objective_name}' for study id '{study_id}'"
            )
            path = "/study/" + study["uid"] + "/study-objectives/select"
            self.api.simple_post_to_api(path, body, "/study-objectives/select")

    # Study endpoints
    @open_file()
    def handle_study_endpoints(self, csvfile):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        all_studies_dict = self.api.get_studies_as_dict()
        for row in readCSV:
            body = {}
            study_id = row[headers.index("study_id")]
            if study_id in all_studies_dict:
                study = all_studies_dict[study_id]
            else:
                self.log.warning("Study with Study Id '%s' is not found", study_id)
                self.metrics.icrement(
                    "/study-endpoints/select/" + "--STUDY_ID_DOES_NOT_EXISTS"
                )
                continue
            endpoint_name = row[headers.index("endpoint")]
            endpoint = self.api.find_object_by_name(endpoint_name, "/endpoints")
            if endpoint is not None:
                body["endpointUid"] = endpoint["uid"]
            timeframe_name = row[headers.index("timeframe")]
            timeframe = self.api.find_object_by_name(timeframe_name, "/timeframes")
            if timeframe is not None:
                body["timeframeUid"] = timeframe["uid"]
            units = row[headers.index("units")].split("+")
            if not len(units) == 1 and units[0] == 1:
                separator = row[headers.index("unit_seperator")]
                body["endpointUnits"] = {"units": units, "separator": separator}
            endpoint_level = row[headers.index("endpoint_level")]
            if endpoint_level != "":
                body["endpointLevel"] = endpoint_level
            # study objective
            all_study_objectives = self.api.get_study_objectives_for_study(study["uid"])
            study_objective = row[headers.index("study_objective")]
            if study_objective in all_study_objectives:
                body["studyObjectiveUid"] = all_study_objectives[study_objective]
            path = "/study/" + study["uid"] + "/study-endpoints/select"
            self.log.info(
                f"Add study endpoint '{endpoint_name}' for study id '{study_id}'"
            )
            self.api.simple_post_to_api(path, body, "/study-endpoints/select")

    def update_data(
        self, patch, study_data
    ):  # smarter solution for this when I know more about the data to patch
        study_data["currentMetadata"]["identificationMetadata"]["registryIdentifiers"][
            "ctGovId"
        ] = patch["ctGovId"]
        study_data["currentMetadata"]["identificationMetadata"]["registryIdentifiers"][
            "eudractId"
        ] = patch["eudractId"]

    @open_file()
    def handle_study(self, csvfile):
        readCSV = csv.reader(csvfile, delimiter=",")
        study_headers = next(readCSV)
        # Fetching existing data
        all_studies = self.api.get_all_identifiers(
            self.api.get_all_from_api("/studies"), "studyNumber"
        )
        for row in readCSV:
            # only for not empty rows
            if row:
                _class = "STUDY"
                data = study_mapper[_class](row, study_headers)
                # Checking if study already exists by study number
                if data["body"]["studyNumber"] not in all_studies:
                    all_studies.append(data["body"]["studyNumber"])
                    study_data = self.api.post_to_api(data)
                    # Patch the update information
                    if study_data is not None:
                        # we need to keep track of previously patched data in order to know if specific field is for example
                        # array field, and if so then we have to append new value to array instead just patching single value
                        patched_data = {}
                        self.update_data(data["patch"], study_data)
                        self.api.patch_to_api(study_data, data["path"] + "/")
                        patched_data.update(data["patch"])
                        with open(
                            MDR_MIGRATION_STUDY_TYPE, encoding="utf-8", errors="ignore"
                        ) as studyTypeCsvFile:
                            readStudyTypeCSV = csv.reader(
                                studyTypeCsvFile, delimiter=","
                            )
                            study_type_headers = next(readStudyTypeCSV)
                            for studyTypeRow in readStudyTypeCSV:
                                # only for not empty rows
                                if studyTypeRow:
                                    # have to prepare structure here, as /studies POST request returns actually only
                                    # identification metadata and version metadata
                                    study_data_template = study_data
                                    study_data_template["currentMetadata"][
                                        "highLevelStudyDesign"
                                    ] = {}
                                    study_data_template["currentMetadata"][
                                        "studyIntervention"
                                    ] = {}
                                    study_data_template["currentMetadata"][
                                        "studyDescription"
                                    ] = {}
                                    _class = "STUDY_TYPE"
                                    study_patch_data = study_mapper[_class](
                                        studyTypeRow, study_type_headers
                                    )
                                    if (
                                        data["body"]["studyNumber"]
                                        == study_patch_data["patch"]["studyNumber"]
                                    ):
                                        parameter_name = study_patch_data["patch"][
                                            "studyDefineParamName"
                                        ]
                                        component_name = study_patch_data[
                                            "componentMappings"
                                        ][parameter_name]
                                        api_param_name = study_patch_data[
                                            "parameterMappings"
                                        ][parameter_name]
                                        data_to_patch = study_patch_data["patch"][
                                            "cCode"
                                        ]
                                        if api_param_name.endswith("Codes"):
                                            if api_param_name not in patched_data:
                                                dict_to_patch = {
                                                    "termUid": data_to_patch
                                                }
                                                study_data_template["currentMetadata"][
                                                    component_name
                                                ][api_param_name] = [dict_to_patch]
                                                patched_data[api_param_name] = [
                                                    dict_to_patch
                                                ]
                                            else:
                                                dict_to_patch = {
                                                    "termUid": data_to_patch
                                                }
                                                existingCodes = patched_data[
                                                    api_param_name
                                                ]
                                                existingCodes.append(dict_to_patch)
                                                study_data_template["currentMetadata"][
                                                    component_name
                                                ][api_param_name] = existingCodes
                                                patched_data[
                                                    api_param_name
                                                ] = existingCodes
                                        elif api_param_name.endswith("Code"):
                                            dict_to_patch = {"termUid": data_to_patch}
                                            study_data_template["currentMetadata"][
                                                component_name
                                            ][api_param_name] = dict_to_patch
                                        elif api_param_name == "isTrialRandomised":
                                            data_to_patch = map_boolean(
                                                study_patch_data["patch"]["cValue"]
                                            )
                                            study_data_template["currentMetadata"][
                                                component_name
                                            ][api_param_name] = data_to_patch
                                            patched_data[api_param_name] = data_to_patch
                                        else:
                                            study_data_template["currentMetadata"][
                                                component_name
                                            ][api_param_name] = data_to_patch
                                            patched_data[api_param_name] = data_to_patch

                                        self.api.patch_to_api(
                                            study_data_template, data["path"]
                                        )
                else:
                    self.metrics.icrement(data["path"] + "--AlreadyExist")

    @open_file()
    def handle_projects(self, csvfile):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        # Fetching existing data
        all_programmes = self.api.get_all_identifiers(
            self.api.get_all_from_api("/clinical-programmes"), "name", "uid"
        )
        all_projects = self.api.get_all_identifiers(
            self.api.get_all_from_api("/projects"), "name"
        )

        for row in readCSV:
            _class = "PROJECT"
            data = project_mapper[_class](row, headers)
            # creating clinical program if it does not already exists
            if data["clinical_programme_body"]["name"] in all_programmes:
                uid = all_programmes[data["clinical_programme_body"]["name"]]
            else:
                res = self.api.post_to_api(
                    data,
                    data["clinical_programme_body"],
                    data["clinical_programme_path"],
                )
                if res is not None:
                    uid = res["uid"]
                    all_programmes[data["clinical_programme_body"]["name"]] = uid
                else:
                    continue  # there will be a error log from the api call

            if data["body"]["name"] not in all_projects:
                all_projects.append(data["body"]["name"])
                data["body"]["clinicalProgrammeUid"] = uid
                self.api.post_to_api(data)
            else:
                self.metrics.icrement(data["path"] + "--AlreadyExist")

    def run(self):
        self.log.info("Migrating mock data")
        self.handle_projects(MDR_MIGRATION_PROJECTS)
        self.handle_study(MDR_MIGRATION_STUDY)
        self.handle_objective_templates(MDR_MOCKUP_OBJECTIVES_OBJECTS)
        self.handle_objectives(MDR_MOCKUP_OBJECTIVES_OBJECTS)
        self.handle_endpoint_templates(MDR_MOCKUP_ENDPOINTS_OBJECTS)
        self.handle_endpoints(MDR_MOCKUP_ENDPOINTS_OBJECTS)
        self.handle_timeframe_templates(MDR_MOCKUP_TIMEFRAMES_OBJECTS)
        self.handle_timeframes(MDR_MOCKUP_TIMEFRAMES_OBJECTS)
        self.handle_study_objectives(MDR_MOCKUP_STUDY_OBJECTIVES)
        self.handle_study_endpoints(MDR_MOCKUP_STUDY_ENDPOINTS)
        self.log.info("Done migrating mock data")


def main():
    metr = Metrics()
    migrator = Mockdata(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
