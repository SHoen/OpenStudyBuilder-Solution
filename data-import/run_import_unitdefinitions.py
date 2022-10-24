from importers.metrics import Metrics
import asyncio
import aiohttp
from os import environ
import csv
import json
from typing import Optional, Sequence, Any
from aiohttp_trace import request_tracer

from importers.functions.utils import create_logger, load_env
from importers.importer import BaseImporter, open_file, open_file_async
from importers.functions.parsers import map_boolean, pass_float

logger = create_logger("legacy_mdr_migrations")

metrics = Metrics()

API_HEADERS = {"Accept": "application/json"}

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")

# SPONSOR DEFINED CODELISTS
MDR_MIGRATION_UNIT_DIF = load_env("MDR_MIGRATION_UNIT_DIF")
MDR_MIGRATION_UNIT_DIMENSION = load_env("MDR_MIGRATION_UNIT_DIMENSION")
MDR_MIGRATION_SPONSOR_CODELIST_DEFINITIONS = load_env(
    "MDR_MIGRATION_SPONSOR_CODELIST_DEFINITIONS"
)
MDR_MIGRATION_SPONSOR_UNITS = load_env("MDR_MIGRATION_SPONSOR_UNITS")


# Finishing touches for standard codelists in sponsor library
class Units(BaseImporter):
    logging_name = "unitdefinitions"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)
        self.sponsor_codelist_legacy_name_map = {}
        self.init_legacy_map(MDR_MIGRATION_SPONSOR_CODELIST_DEFINITIONS)

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

    @open_file_async()
    async def handle_unit_dimension(self, file, code_lists_uids, session):
        self.ensure_cache()
        readCSV = csv.reader(file, delimiter=",")
        headers = next(readCSV)
        api_tasks = []
        for row in readCSV:
            codelist_name = None
            if (
                row[headers.index("CD_LIST_ID")]
                not in self.sponsor_codelist_legacy_name_map
            ):
                self.log.warning(
                    f"Codelist '{row[headers.index('CD_LIST_ID')]}' does not exist, skipping row"
                )
                continue
            else:
                codelist_name = self.sponsor_codelist_legacy_name_map[
                    row[headers.index("CD_LIST_ID")]
                ]
            codelistUid = ""
            if codelist_name in code_lists_uids:
                codelistUid = code_lists_uids[codelist_name]
            else:
                self.log.warning(
                    f"Codelist '{codelist_name}' does not exist, skipping row."
                )
                continue
            data = {
                "termName": row[headers.index("CD_VAL_LB")],
                "body": {
                    "codelistUid": codelistUid,
                    "catalogueName": "SDTM CT",
                    "codeSubmissionValue": row[headers.index("CD_VAL")],
                    "nciPreferredName": "UNK",
                    "definition": row[headers.index("description")],
                    "sponsorPreferredName": row[headers.index("CD_VAL_LB")],
                    "sponsorPreferredNameSentenceCase": row[headers.index("CD_VAL_LB")],
                    "libraryName": "Sponsor",
                    "order": row[headers.index("CD_VAL_SORT_SEQ")],
                },
            }
            # TODO check if already exists
            api_tasks.append(self.process_units(data=data, session=session))
        await asyncio.gather(*api_tasks)

    async def process_units(self, data: dict, session: aiohttp.ClientSession):
        termName = data["termName"]
        self.log.info(f"Adding unit dimension {termName}")
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
        else:
            termUid = None
            if termName in self.cache.added_terms:
                termUid = self.cache.added_terms[termName]["termUid"]
            elif (
                data["body"]["codeSubmissionValue"]
                in self.cache.all_terms_code_submission_values
            ):
                termUid = self.cache.all_terms_code_submission_values[
                    data["body"]["codeSubmissionValue"]
                ]
            if termUid:
                codelist_uid = data["body"]["codelistUid"]
                result = await self.api.post_to_api_async(
                    url="/ct/codelists/" + codelist_uid + "/add-term",
                    body={"termUid": termUid, "order": data["body"]["order"]},
                    session=session,
                )
                return result

    @open_file_async()
    async def handle_unit_definitions(self, csvfile, session):
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks = []
        existing_rows = self.api.get_all_identifiers(
            self.api.get_all_from_api("/concepts/unit-definitions"),
            identifier="name",
            value="uid",
        )
        ucum_codelists = self.api.get_all_from_api("/dictionaries/codelists/UCUM")
        all_ucum_terms = {}
        for ucum_codelist in ucum_codelists:
            all_ucum_terms.update(
                self.api.get_all_identifiers(
                    self.api.get_all_from_api(
                        "/dictionaries/terms",
                        params={"codelist_uid": ucum_codelist["codelistUid"]},
                    ),
                    "name",
                    "termUid",
                )
            )
        all_unit_dimension_terms = self.api.get_all_identifiers(
            self.api.get_all_from_api(
                "/ct/terms/attributes?codelist_name=Unit Dimension"
            ),
            identifier="codeSubmissionValue",
            value="termUid",
        )
        all_unit_subset_terms = self.api.get_all_identifiers(
            self.api.get_all_from_api("/ct/terms/names?codelist_name=Unit Subset"),
            identifier="sponsorPreferredName",
            value="termUid",
        )
        age_unit_subset_uid = all_unit_subset_terms["Age Unit"]
        dose_unit_subset_uid = all_unit_subset_terms["Dose Unit"]
        study_time_subset_uid = all_unit_subset_terms["Study Time"]
        time_unit_subset_uid = all_unit_subset_terms["Time Unit"]
        strength_unit_subset_uid = all_unit_subset_terms["Strength Unit"]
        for row in readCSV:
            name = row[headers.index("UNIT")]

            ucumUid = all_ucum_terms.get(row[headers.index("UCUM name")])

            unitDimensionUid = all_unit_dimension_terms.get(
                row[headers.index("UNIT_DIMENSION")]
            )


            ctUnits = []
            # Link to CDISC units
            # TODO look up via submission value instead of "guessing" uid?
            if row[headers.index("CT_CD")] != "":
                if row[headers.index("CT_SUBMVAL")] not in ("", "0"):
                    # Guess uid, we know it should be  Cnnnnn_{submission value}
                    ctUnits.append(
                        row[headers.index("CT_CD")]
                        + "_"
                        + row[headers.index("CT_SUBMVAL")]
                    )
                if row[headers.index("CT_SUBMVAL_2")] not in ("", "0"):
                    ctUnits.append(
                        row[headers.index("CT_CD")]
                        + "_"
                        + row[headers.index("CT_SUBMVAL_2")]
                    )
            # Link to sponsor defined units
            if row[headers.index("SPDEF_SUBMVAL")] != "":
                submval =  row[headers.index("SPDEF_SUBMVAL")]
                filt = {"attributes.codeSubmissionValue": {"v": [submval], "op": "eq"}}
                unitdefs = self.api.get_all_from_api(
                    f"/ct/terms?codelist_name=Unit&filters={json.dumps(filt)}"
                )
                #print(json.dumps(unitdefs, indent=2))
                unitUids = [v["termUid"] for v in unitdefs]
                #print(json.dumps(unitUids, indent=2))
                ctUnits.extend(unitUids)

            unitSubsets = []
            if row[headers.index("AGE_UNIT_SUBSET")] == "Y":
                unitSubsets.append(age_unit_subset_uid)
            if row[headers.index("DOSE_UNIT_SUBSET")] == "Y":
                unitSubsets.append(dose_unit_subset_uid)
            if row[headers.index("STUDY_TIME_UNIT_SUBSET")] == "Y":
                unitSubsets.append(study_time_subset_uid)
            if row[headers.index("TIME_UNIT_SUBSET")] == "Y":
                unitSubsets.append(time_unit_subset_uid)
            if row[headers.index("STRENGTH_UNIT_SUBSET")] == "Y":
                unitSubsets.append(strength_unit_subset_uid)

            # Mark as template parameter if part of any subset
            # templateParameter = len(unitSubsets) > 0
            # All units are template parameters!
            templateParameter = True

            data = {
                "path": "/concepts/unit-definitions",
                "approve_path": "/concepts/unit-definitions",
                "body": {
                    "name": name,
                    "libraryName": "Sponsor",
                    "ctUnits": ctUnits,
                    "unitSubsets": unitSubsets,
                    "convertibleUnit": map_boolean(
                        row[headers.index("CONVERTIBLE_UNIT")]
                    ),
                    "displayUnit": map_boolean(row[headers.index("DISPLAY_UNIT")]),
                    "masterUnit": map_boolean(row[headers.index("MASTER_UNIT")]),
                    "siUnit": map_boolean(row[headers.index("SI_UNIT")]),
                    "usConventionalUnit": map_boolean(
                        row[headers.index("US_CONVENTIONAL_UNIT")]
                    ),
                    "legacyCode": row[headers.index("UNIT")],
                    "molecularWeightConvExpon": pass_float(
                        row[headers.index("MOLECULAR_WEIGHT_CONV_EXPON")]
                    ),
                    "conversionFactorToMaster": pass_float(
                        row[headers.index("CONVERTION_FACTOR_TO_MASTER")]
                    ),
                    "unitDimension": unitDimensionUid,
                    "definition": row[headers.index("description")],
                    "order": row[headers.index("CD_VAL_SORT_SEQ")],
                    "ucum": ucumUid,
                    "comment": row[headers.index("Comment")],
                    "templateParameter": templateParameter,
                },
            }
            if existing_rows.get(name):
                self.log.info(
                    f"Skipping existing unit '{name}' with ct codes: {ctUnits}"
                )
            elif row[headers.index("Migrate Y/N")] not in ("Y", "y"):
                self.log.info(f"Unit '{name}' is not marked for migration, skipping")
            else:
                self.log.info(
                    f"Adding unit '{name}' with ct codes: {ctUnits}, part of subsets: {unitSubsets}"
                )
                api_tasks.append(
                    self.api.post_then_approve(data=data, session=session, approve=True)
                )

        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_sponsor_units(self, csvfile, code_lists_uids, session):
        self.ensure_cache()
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks = []

        # existing_rows = self.api.get_all_identifiers(
        #     self.api.get_all_from_api(f"/ct/terms/names?codelist_name=Unit"),
        #     identifier="sponsorPreferredName",
        #     value="codelistUid",
        # )

        # existing_code_subm_values = self.api.get_all_identifiers(
        #     self.api.get_all_from_api(
        #         "/ct/terms/attributes?codelist_name=Unit"
        #     ),
        #     identifier="codeSubmissionValue",
        #     value="termUid",
        # )

        for row in readCSV:
            data = {
                "path": "/ct/terms",
                "codelist": "UNIT",
                "body": {
                    "catalogueName": "SDTM CT",
                    "codeSubmissionValue": row[headers.index("SPDEF_SUBMVAL")],
                    "nciPreferredName": row[headers.index("NCI_PREFERRED_NAME")],
                    "definition": row[headers.index("DEFINITION")],
                    "sponsorPreferredName": row[headers.index("SPDEF_SUBMVAL")],
                    "sponsorPreferredNameSentenceCase": row[headers.index("SPDEF_SUBMVAL")],
                    "libraryName": "Sponsor",
                    "order": None
                },
            }

            data["body"]["codelistUid"] = code_lists_uids["Unit"]
            # if not existing_rows.get(data["body"]["sponsorPreferredName"]):
            #print(json.dumps(data, indent=2))
            api_tasks.append(
                self.process_simple_term_migration(data=data, session=session)
            )
        await asyncio.gather(*api_tasks)

    async def async_run(self):
        code_lists_uids = self.api.get_code_lists_uids()
        timeout = aiohttp.ClientTimeout(None)
        conn = aiohttp.TCPConnector(limit=4, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
            await self.handle_unit_dimension(
                MDR_MIGRATION_UNIT_DIMENSION, code_lists_uids, session
            )
            await self.handle_sponsor_units(
                MDR_MIGRATION_SPONSOR_UNITS,
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.handle_unit_definitions(MDR_MIGRATION_UNIT_DIF, session)

    def run(self):
        self.log.info("Importing unit definitions")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_run())
        self.log.info("Done importing unit definitions")


def main():
    metr = Metrics()
    migrator = Units(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
