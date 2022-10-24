from importers.importer import BaseImporter, open_file, open_file_async
from importers.metrics import Metrics
import asyncio
import aiohttp
import csv
import time
from typing import Optional, Sequence, Any

from importers.functions.parsers import map_boolean_exc, find_term_by_name
from importers.functions.utils import load_env

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")
MDR_MIGRATION_EPOCH = load_env("MDR_MIGRATION_EPOCH")
MDR_MIGRATION_EPOCH_SUB_TYPE = load_env("MDR_MIGRATION_EPOCH_SUB_TYPE")
MDR_MIGRATION_SPONSOR_CODELIST_DEFINITIONS = load_env(
    "MDR_MIGRATION_SPONSOR_CODELIST_DEFINITIONS"
)
MDR_MIGRATION_ENDPOINT_LEVEL = load_env("MDR_MIGRATION_ENDPOINT_LEVEL")
MDR_MIGRATION_OBJECTIVE_LEVEL = load_env("MDR_MIGRATION_OBJECTIVE_LEVEL")
MDR_MIGRATION_OPERATOR = load_env("MDR_MIGRATION_OPERATOR")
MDR_MIGRATION_EPOCH_TYPE = load_env("MDR_MIGRATION_EPOCH_TYPE")
MDR_MIGRATION_CODELIST_PARAMETER_SET = load_env("MDR_MIGRATION_CODELIST_PARAMETER_SET")


epoch_sub_type = {
    "EPOCH_SUB_TYPE": lambda row, headers: {
        "path": "/ct/terms",
        "codelist": "GEN_EPOCH_SUB_TYPE",
        "body": {
            "catalogueName": "SDTM CT",
            "codeSubmissionValue": row[headers.index("GEN_EPOCH_SUB_TYPE_CD")],
            "nameSubmissionValue": row[headers.index("GEN_EPOCH_SUB_TYPE_CD")],
            "nciPreferredName": "UNK",
            "definition": "",
            "sponsorPreferredName": row[headers.index("GEN_EPOCH_SUB_TYPE")],
            "sponsorPreferredNameSentenceCase": row[
                headers.index("GEN_EPOCH_SUB_TYPE")
            ].lower(),
            "order": row[headers.index("CD_VAL_SORT_SEQ")],
            "libraryName": "Sponsor",
        },
    }
}

epoch = {
    "EPOCH": lambda row, headers: {
        "path": "/ct/terms",
        "codelist": "Epoch",
        "body": {
            "catalogueName": "SDTM CT",
            "codeSubmissionValue": row[headers.index("GEN_EPOCH_CD")],
            "nameSubmissionValue": row[headers.index("GEN_EPOCH_CD")],
            "nciPreferredName": "UNK",
            "definition": "",
            "sponsorPreferredName": row[headers.index("GEN_EPOCH_LB")],
            "sponsorPreferredNameSentenceCase": row[
                headers.index("GEN_EPOCH_LB")
            ].lower(),
            "order": row[headers.index("CD_VAL_SORT_SEQ")],
            "libraryName": "Sponsor",
        },
    }
}

endpoint_level = {
    "MDR_MIGRATION_ENDPOINT_LEVEL": lambda row, headers: {
        "path": "/ct/terms",
        "codelist": row[headers.index("CD_LIST_ID")],
        "uid": row[headers.index("CT_CD")],
        "body": {
            "order": row[headers.index("CD_VAL_SORT_SEG")],
            "sponsorPreferredName": row[headers.index("CD_VAL_LB")],
            "sponsorPreferredNameSentenceCase": row[headers.index("CD_VAL_LB_LC")],
            "changeDescription": "Migration",
        },
    }
}


objective_level = {
    "MDR_MIGRATION_OBJECTIVE_LEVEL": lambda row, headers: {
        "path": "/ct/terms",
        "codelist": row[headers.index("CD_LIST_ID")],
        "uid": row[headers.index("CT_CD")],
        "body": {
            "order": row[headers.index("CD_VAL_SORT_SEG")],
            "sponsorPreferredName": row[headers.index("CD_VAL_LB")],
            "sponsorPreferredNameSentenceCase": row[headers.index("CD_VAL_LB_LC")],
            "changeDescription": "Migration",
        },
    }
}

time_units = {
    "COMMON_MAPPING": lambda row, headers: {
        "path": "/ct/terms",
        "codelist": row[headers.index("CODELIST_NAME")],
        "termUid": row[headers.index("CT_CD")],
    }
}

# ---------------------------------------------------------------
# Utilites for parsing and converting data
# ---------------------------------------------------------------
#


def sample_from_dict(d, sample=10):
    if SAMPLE:
        keys = list(d)[0:sample]
        values = [d[k] for k in keys]
        return dict(zip(keys, values))
    else:
        return d


def sample_from_list(d, sample=10):
    if SAMPLE:
        return d[0:sample]
    else:
        return d


# Standard codelists terms in sponsor library
# TODO the split between StandardCodeListTerms1 and 2
# is just done because all the things in part 2 are handled
# in a standardised way, while part 1 (this file) uses
# specific functions for each part.
# Can the things in this file also be standardized in a similar fashion?
class StandardCodelistTerms1(BaseImporter):
    logging_name = "standard_codelistterms1"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)
        self.sponsor_codelist_legacy_name_map = {}
        self.init_legacy_map(MDR_MIGRATION_SPONSOR_CODELIST_DEFINITIONS)
        self.code_lists_uids = self.api.get_code_lists_uids()

    @open_file()
    def init_legacy_map(self, csvfile):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        for row in readCSV:
            legacy_codelist_id = row[headers.index("legacy_codelist_id")]
            new_codelist_name = row[headers.index("new_codelist_name")]
            if legacy_codelist_id == "" or legacy_codelist_id == None:
                if new_codelist_name == "Objective Level":
                    self.sponsor_codelist_legacy_name_map[
                        "ObjectiveLevel"
                    ] = new_codelist_name
                elif new_codelist_name == "Endpoint Level":
                    self.sponsor_codelist_legacy_name_map[
                        "EndpointLevel"
                    ] = new_codelist_name
            else:
                self.sponsor_codelist_legacy_name_map[
                    legacy_codelist_id
                ] = new_codelist_name

    @open_file()
    def handle_epoch_subtype(self, csvfile):
        self.ensure_cache()
        self.code_lists_uids = self.api.get_code_lists_uids()
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        parent_type_terms = self.api.get_terms_for_codelist_name("Epoch Type")
        for row in readCSV:
            parentTermUid = find_term_by_name(
                row[headers.index("GEN_EPOCH_TYPE")], parent_type_terms
            )

            _class = "EPOCH_SUB_TYPE"
            data = epoch_sub_type[_class](row, headers)
            if (
                row[headers.index("CD_LIST_ID")]
                not in self.sponsor_codelist_legacy_name_map
            ):
                self.log.error(
                    f"Epoch subtype '{row[headers.index('CD_LIST_ID')]}' not found in legacy name map, skipping"
                )
                self.metrics.icrement(
                    data["path"] + "-Names Epoch Sub Type - SkippedASMissingCodelistUid"
                )
                continue
            codelist_name = self.sponsor_codelist_legacy_name_map["GEN_EPOCH_SUB_TYPE"]
            if codelist_name in self.code_lists_uids:
                data["body"]["codelistUid"] = self.code_lists_uids[codelist_name]
            else:
                self.log.error(f"Codelist '{codelist_name}' not found, skipping")
                self.metrics.icrement(
                    data["path"] + "-Names Epoch Sub Type - SkippedASMissingCodelistUid"
                )
                continue
            reused_item = False
            # connect cdisc epoch sub type term with a sponsor epoch sub type term
            if row[headers.index("CT_CD")].startswith("C") and parentTermUid:
                reused_item = True
                termUid = f"{row[headers.index('CT_CD')]}_{row[headers.index('GEN_EPOCH_SUB_TYPE_CD')]}"
            else:
                res = self.api.post_to_api(data)
                subtype = row[headers.index("GEN_EPOCH_SUB_TYPE")]
                subtype_code = row[headers.index("GEN_EPOCH_SUB_TYPE_CD")]
                if res is not None:
                    termUid = res["termUid"]
                    self.cache.added_terms[subtype] = res
                    # Approve Names
                    self.api.simple_approve2(
                        data["path"], f"/{termUid}/names/approve", label="Names"
                    )
                    # Approve attributes
                    self.api.simple_approve2(
                        "/ct/terms",
                        f"/{termUid}/attributes/approve",
                        label="Attributes",
                    )
                else:
                    termUid = None
                    if subtype in self.cache.added_terms:
                        termUid = self.cache.added_terms[subtype]["termUid"]
                    elif subtype_code in self.cache.all_terms_code_submission_values:
                        termUid = self.cache.all_terms_code_submission_values[
                            subtype_code
                        ]
                    elif subtype_code in self.cache.all_terms_name_submission_values:
                        termUid = self.cache.all_terms_name_submission_values[
                            subtype_code
                        ]
                    elif subtype in self.cache.all_term_name_values:
                        termUid = self.cache.all_term_name_values[subtype]["termUid"]
                    reused_item = True

            if termUid and parentTermUid:
                self.api.post_to_api(
                    {
                        "path": f"/ct/terms/{termUid}/add-parent?parent_uid={parentTermUid}&relationship_type=type",
                        "body": {},
                    }
                )
                if reused_item:
                    codelist_uid = data["body"]["codelistUid"]
                    # add a term to the epoch sub type codelist
                    self.api.post_to_api(
                        {
                            "path": "/ct/codelists/" + codelist_uid + "/add-term",
                            "body": {
                                "termUid": termUid,
                                "order": data["body"]["order"],
                            },
                        }
                    )
                    # Start a new version
                    self.api.post_to_api(
                        {
                            "path": "/ct/terms/" + termUid + "/names/new-version",
                            "body": {},
                        }
                    )
                    # patch the names
                    data["body"]["changeDescription"] = "Migration modification"
                    res = self.api.simple_patch(
                        data["body"],
                        "/ct/terms/" + termUid + "/names",
                        "/ct/terms/names",
                    )
                    # Approve Names
                    self.api.simple_approve2(
                        "/ct/terms", f"/{termUid}/names/approve", label="Names"
                    )

    @open_file()
    def handle_epoch(self, csvfile):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        parent_sub_type_terms = self.api.get_terms_for_codelist_name("Epoch Sub Type")
        for row in readCSV:
            parentTermUid = find_term_by_name(
                row[headers.index("GEN_EPOCH_SUB_TYPE")], parent_sub_type_terms
            )

            _class = "EPOCH"
            data = epoch[_class](row, headers)
            data["body"]["codelistUid"] = "C99079"
            termUid = (
                f"{row[headers.index('CT_CD')]}_{row[headers.index('GEN_EPOCH_CD')]}"
            )

            if termUid and parentTermUid:
                self.api.post_to_api(
                    {
                        "path": f"/ct/terms/{termUid}/add-parent?parent_uid={parentTermUid}&relationship_type=subtype",
                        "body": {},
                    }
                )
                codelist_uid = data["body"]["codelistUid"]
                # add a term to the epoch codelist
                self.api.post_to_api(
                    {
                        "path": "/ct/codelists/" + codelist_uid + "/add-term",
                        "body": {"termUid": termUid, "order": data["body"]["order"]},
                    }
                )
                # Start a new version
                self.api.post_to_api(
                    {"path": "/ct/terms/" + termUid + "/names/new-version", "body": {}}
                )
                # patch the names
                data["body"]["changeDescription"] = "Migration modification"
                res = self.api.simple_patch(
                    data["body"], "/ct/terms/" + termUid + "/names", "/ct/terms/names"
                )
                self.api.simple_patch(
                    {"codelistUid": codelist_uid, "newOrder": data["body"]["order"]},
                    "/ct/terms/" + termUid + "/order",
                    "/ct/terms/order",
                )
                # Approve Names
                self.api.simple_approve2(
                    "/ct/terms", f"/{termUid}/names/approve", label="Names"
                )

    @open_file()
    def handle_endpoint_level(self, csvfile):
        self.code_lists_uids = self.api.get_code_lists_uids()
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        for row in readCSV:
            # TODO check if already exists
            _class = "MDR_MIGRATION_ENDPOINT_LEVEL"
            data = endpoint_level[_class](row, headers)
            if (
                row[headers.index("CD_LIST_ID")]
                not in self.sponsor_codelist_legacy_name_map
            ):
                self.metrics.icrement(
                    data["path"] + "-Names Endpoint Level- SkippedASMissingCodelistUid"
                )
                continue
            codelist_name = self.sponsor_codelist_legacy_name_map[
                row[headers.index("CD_LIST_ID")]
            ]
            if codelist_name in self.code_lists_uids:
                data["body"]["codelistUid"] = self.code_lists_uids[codelist_name]
            else:
                self.metrics.icrement(
                    data["path"] + "-Names Visit Day Type - SkippedASMissingCodelistUid"
                )
                continue
            # Start a new version
            self.api.post_to_api(
                {"path": "/ct/terms/" + data["uid"] + "/names/new-version", "body": {}}
            )
            # path the names
            res = self.api.simple_patch(
                data["body"], "/ct/terms/" + data["uid"] + "/names", "/ct/terms/names"
            )
            # Approve
            if res is not None:
                # Approve Names
                if self.api.simple_approve2(
                    "/ct/terms", f"/{res['termUid']}/names/approve", label="Names"
                ):
                    # add the term to the sponsor list
                    codelist_uid = data["body"]["codelistUid"]
                    self.api.post_to_api(
                        {
                            "path": "/ct/codelists/" + codelist_uid + "/add-term",
                            "body": {
                                "termUid": res["termUid"],
                                "order": row[headers.index("CD_VAL_SORT_SEG")],
                            },
                        }
                    )
            else:
                self.api.simple_approve2(
                    "/ct/terms", f"/{data['uid']}/names/approve", label="Names"
                )

    @open_file()
    def handle_objective_level(self, csvfile):
        self.code_lists_uids = self.api.get_code_lists_uids()
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        for row in readCSV:
            # TODO check if already exists
            _class = "MDR_MIGRATION_OBJECTIVE_LEVEL"
            data = objective_level[_class](row, headers)
            if (
                row[headers.index("CD_LIST_ID")]
                not in self.sponsor_codelist_legacy_name_map
            ):
                self.log.warning(
                    f"Codelist '{row[headers.index('CD_LIST_ID')]} not found in legacy map, skipping'"
                )
                self.metrics.icrement(
                    data["path"] + "-Names Objective Level- SkippedASMissingCodelistUid"
                )
                continue
            codelist_name = self.sponsor_codelist_legacy_name_map[
                row[headers.index("CD_LIST_ID")]
            ]
            if codelist_name in self.code_lists_uids:
                data["body"]["codelistUid"] = self.code_lists_uids[codelist_name]
            else:
                self.log.warning(f"Codelist '{codelist_name} not found, skipping'")
                self.metrics.icrement(
                    data["path"]
                    + "-Names Objective Level - SkippedASMissingCodelistUid"
                )
                continue
            # Start a new version
            self.api.post_to_api(
                {"path": "/ct/terms/" + data["uid"] + "/names/new-version", "body": {}}
            )
            # path the names
            res = self.api.simple_patch(
                data["body"], "/ct/terms/" + data["uid"] + "/names", "/ct/terms/names"
            )
            # Approve
            if res is not None:
                # Approve Names
                if self.api.simple_approve2(
                    "/ct/terms", f"/{res['termUid']}/names/approve", label="Names"
                ):
                    # add the term to the sponsor list
                    codelist_uid = data["body"]["codelistUid"]
                    self.api.post_to_api(
                        {
                            "path": "/ct/codelists/" + codelist_uid + "/add-term",
                            "body": {
                                "termUid": res["termUid"],
                                "order": row[headers.index("CD_VAL_SORT_SEG")],
                            },
                        }
                    )

    @open_file_async()
    async def handle_epoch_type(self, csvfile, session):
        self.code_lists_uids = self.api.get_code_lists_uids()
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks = []
        for row in readCSV:

            codelist_name = None
            if (
                row[headers.index("CD_LIST_ID")]
                not in self.sponsor_codelist_legacy_name_map
            ):
                self.log.warning(
                    f"Codelist id '{row[headers.index('CD_LIST_ID')]}' not found in legacy map, skipping."
                )
                self.metrics.icrement(
                    "/ct/codelists/-Names Epoch Type - SkippedASMissingCodelistUid"
                )
                continue
            else:
                codelist_name = self.sponsor_codelist_legacy_name_map[
                    row[headers.index("CD_LIST_ID")]
                ]
            codelistUid = ""
            if codelist_name in self.code_lists_uids:
                codelistUid = self.code_lists_uids[codelist_name]
            else:
                self.log.warning(
                    f"Codelist '{codelist_name}' not found in provided list, skipping."
                )
                # self.metrics.icrement(data["path"] + "-Names Epoch Type - SkippedASMissingCodelistUid")
                continue
            data = {
                "codelist": row[headers.index("CD_LIST_ID")],
                "termName": row[headers.index("CD_VAL_LB")],
                "termUid": row[headers.index("CT_CD")],
                "body": {
                    "catalogueName": "SDTM CT",
                    "codelistUid": codelistUid,
                    "codeSubmissionValue": row[headers.index("CD_VAL")],
                    "nameSubmissionValue": row[headers.index("CD_VAL")],
                    "nciPreferredName": "UNK",
                    "definition": "",
                    "sponsorPreferredName": row[headers.index("CD_VAL_LB")],
                    "sponsorPreferredNameSentenceCase": row[
                        headers.index("CD_VAL_LB")
                    ].lower(),
                    "libraryName": "Sponsor",
                    "order": row[headers.index("CD_VAL_SORT_SEQ")],
                },
            }
            # TODO check if already exists
            self.log.info(
                f"Adding epoch type '{data['termName']}' to codelist '{data['codelist']}'"
            )
            api_tasks.append(self.process_epoc_type(data=data, session=session))
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_codelist_definitions(self, csvfile, session):
        # General handler for creating codelists in libraries.
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks = []
        for row in readCSV:
            new_codelist_name = row[headers.index("new_codelist_name")]
            try:
                idx = headers.index("extensible")
                extensible = map_boolean_exc(row[idx])
            except ValueError as e:
                self.log.warning(
                    f"Error parsing boolean at index {idx} in line \n{row}\nerror: {e}\nDefaulting to False"
                )
                extensible = False
            try:
                idx = headers.index("template_parameter")
                templateParameter = map_boolean_exc(row[idx])
            except ValueError as e:
                self.log.warning(
                    f"Error parsing boolean at index {idx} in line\n{row}\nerror: {e}\nDefaulting to False"
                )
                templateParameter = False
            data = {
                "path": "/ct/codelists",
                "body": {
                    "catalogueName": "SDTM CT",
                    "name": new_codelist_name,
                    "submissionValue": row[headers.index("submission_value")],
                    "nciPreferredName": row[headers.index("preferred_term")],
                    "definition": row[headers.index("definition")],
                    "extensible": extensible,
                    "sponsorPreferredName": row[headers.index("new_codelist_name")],
                    "templateParameter": templateParameter,
                    "libraryName": row[headers.index("library")],
                    "terms": [],
                },
            }
            # TODO Add check if we already have the code list
            self.log.info(
                f"Adding codelist name '{new_codelist_name}' to library '{data['body']['libraryName']}'"
            )
            api_tasks.append(
                self.post_codelist_approve_name_or_attribute(data=data, session=session)
            )
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_codelist_parameter_set(self, csvfile, session):
        # Mark codelist parameters as a template parameters
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks = []

        for row in readCSV:
            url = (
                "/ct/codelists/" + row[headers.index("CODELIST_CONCEPT_ID")] + "/names"
            )
            changeDescription = f"Marking {row[headers.index('DESCRIPTION')]} as TemplateParameter in the migration"
            data = {
                "get_path": url,
                "path": url + "/new-version",
                "patch_path": url,
                "approve_path": url + "/approve",
                "body": {
                    "templateParameter": True,
                    "changeDescription": changeDescription,
                },
            }
            # TODO check if already exists
            self.log.info(
                f"Adding codelist parameter set '{row[headers.index('CODELIST_CONCEPT_ID')]}' with description '{row[headers.index('DESCRIPTION')]}'"
            )
            api_tasks.append(
                self.process_codelist_parameter(data=data, session=session)
            )
        await asyncio.gather(*api_tasks)

    ############ helper functions ###########
    async def post_codelist_approve_name_or_attribute(
        self, data: dict, session: aiohttp.ClientSession
    ):
        status, response = await self.api.post_to_api_async(
            url=data["path"], body=data["body"], session=session
        )
        uid = response.get("codelistUid")
        if uid != None:
            # Give the backend a little time before approving, otherwise approve may fail.
            # Seems to be a problem only when running locally.
            # We do all these in parallel, this sleep should not affect the time it takes to run the import.
            time.sleep(0.05)
            status, result = await self.api.approve_async(
                "/ct/codelists/" + uid + "/names/approve", session=session
            )
            if status != 201:
                self.log.error(
                    f"Failed to approve name for codelist: {data['body']['name']}"
                )
                self.metrics.icrement("/ct/codelists/-NamesApproveError")
            else:
                self.log.info(f"Approved name for codelist: {data['body']['name']}")
                self.metrics.icrement("/ct/codelists/-NamesApprove")
            time.sleep(0.05)
            status, result = await self.api.approve_async(
                "/ct/codelists/" + uid + "/attributes/approve", session=session
            )
            if status != 201:
                self.log.error(
                    f"Failed to approve attributes for codelist: {data['body']['name']}"
                )
                self.metrics.icrement("/ct/codelists/-AttributesApproveError")
            else:
                self.log.info(
                    f"Approved attributes for codelist: {data['body']['name']}"
                )
                self.metrics.icrement("/ct/codelists/-AttributesApprove")
            return result
        else:
            self.log.info(
                f"Codelist {data['body']['name']} already exists, skipping approve."
            )
            return response

    async def process_codelist_parameter(
        self, data: dict, session: aiohttp.ClientSession
    ):
        get_result = {}
        async with session.get(
            API_BASE_URL + data["get_path"], headers=self.api.api_headers
        ) as response:
            status = response.status
            get_result = await response.json()
        if get_result is not None and get_result.get("templateParameter") is True:
            self.metrics.icrement("/ct/codelists-AlreadyIsTemplateParameter")
            return get_result
        status, post_result = await self.api.post_to_api_async(
            url=data["path"], body={}, session=session
        )
        patch_result = await self.api.patch_to_api_async(
            path=data["patch_path"], body=data["body"], session=session
        )
        status, result = await self.api.approve_async(
            data["approve_path"], session=session
        )
        if status != 201:
            self.metrics.icrement("/ct/codelists/-NamesApproveError")
        else:
            self.metrics.icrement("/ct/codelists/-NamesApprove")
        return result

    async def process_epoc_type(self, data: dict, session: aiohttp.ClientSession):
        self.ensure_cache()
        termName = data["termName"]
        # if termUid starts with C it means that we should take existing CDISC term and add it to the Epoch Type codelist
        if data["termUid"].startswith("C"):
            termUid = f"{data['termUid']}_{data['body']['codeSubmissionValue']}"
            codelist_uid = data["body"]["codelistUid"]
            result = await self.api.post_to_api_async(
                url="/ct/codelists/" + codelist_uid + "/add-term",
                body={"termUid": termUid, "order": data["body"]["order"]},
                session=session,
            )
            return result
        else:
            post_status, post_result = await self.api.post_to_api_async(
                url="/ct/terms", body=data["body"], session=session
            )
            if post_status == 201:
                self.cache.added_terms[termName] = post_result
                status, result = await self.api.approve_async(
                    "/ct/terms/" + post_result["termUid"] + "/names/approve",
                    session=session,
                )
                if status != 201:
                    self.metrics.icrement("/ct/terms-NamesApproveError")
                else:
                    self.metrics.icrement("/ct/terms-NamesApprove")
                status, result = await self.api.approve_async(
                    "/ct/terms/" + post_result["termUid"] + "/attributes/approve",
                    session=session,
                )
                if status != 201:
                    self.metrics.icrement("/ct/terms-AttributesApproveError")
                else:
                    self.metrics.icrement("/ct/terms-AttributesApprove")
                return result

    async def async_run(self):
        timeout = aiohttp.ClientTimeout(None)
        conn = aiohttp.TCPConnector(limit=4, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
            await self.handle_codelist_definitions(
                MDR_MIGRATION_SPONSOR_CODELIST_DEFINITIONS, session
            )
            await self.handle_codelist_parameter_set(
                MDR_MIGRATION_CODELIST_PARAMETER_SET, session
            )

            # we have to get all codelists when sponsor one will be migrated
            # otherwise sponsor defined terms won't know to which codelist they should connect
            await self.handle_epoch_type(MDR_MIGRATION_EPOCH_TYPE, session)

    def run(self):
        self.log.info("Importing standard codelists")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_run())
        self.handle_epoch_subtype(MDR_MIGRATION_EPOCH_SUB_TYPE)
        self.handle_epoch(MDR_MIGRATION_EPOCH)
        self.handle_endpoint_level(MDR_MIGRATION_ENDPOINT_LEVEL)
        self.handle_objective_level(MDR_MIGRATION_OBJECTIVE_LEVEL)
        self.log.info("Done importing standard codelists")


def main():
    metr = Metrics()
    migrator = StandardCodelistTerms1(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
