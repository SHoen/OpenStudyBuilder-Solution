from importers.metrics import Metrics
import asyncio
import aiohttp
from os import environ
import csv
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
MDR_MIGRATION_ARM_TYPE = load_env("MDR_MIGRATION_ARM_TYPE")
MDR_MIGRATION_CRITERIA_CATEGORY = load_env("MDR_MIGRATION_CRITERIA_CATEGORY")
MDR_MIGRATION_CRITERIA_SUB_CATEGORY = load_env("MDR_MIGRATION_CRITERIA_SUB_CATEGORY")
MDR_MIGRATION_CRITERIA_TYPE = load_env("MDR_MIGRATION_CRITERIA_TYPE")
MDR_MIGRATION_COMPOUND_DISPENSED_IN = load_env("MDR_MIGRATION_COMPOUND_DISPENSED_IN")
MDR_MIGRATION_DEVICE = load_env("MDR_MIGRATION_DEVICE")
MDR_MIGRATION_ELEMENT_TYPE = load_env("MDR_MIGRATION_ELEMENT_TYPE")
MDR_MIGRATION_ELEMENT_SUBTYPE = load_env("MDR_MIGRATION_ELEMENT_SUBTYPE")
MDR_MIGRATION_ENDPOINT_CATEGORY = load_env("MDR_MIGRATION_ENDPOINT_CATEGORY")
MDR_MIGRATION_ENDPOINT_SUB_CATEGORY = load_env("MDR_MIGRATION_ENDPOINT_SUB_CATEGORY")
MDR_MIGRATION_ENDPOINT_SUB_LEVEL = load_env("MDR_MIGRATION_ENDPOINT_SUB_LEVEL")
MDR_MIGRATION_FLOWCHART_GROUP = load_env("MDR_MIGRATION_FLOWCHART_GROUP")
MDR_MIGRATION_NULL_FLAVOR = load_env("MDR_MIGRATION_NULL_FLAVOR")
MDR_MIGRATION_OBJECTIVE_CATEGORY = load_env("MDR_MIGRATION_OBJECTIVE_CATEGORY")
MDR_MIGRATION_OPERATOR = load_env("MDR_MIGRATION_OPERATOR")
MDR_MIGRATION_THERAPY_AREA = load_env("MDR_MIGRATION_THERAPY_AREA")
MDR_MIGRATION_TIME_REFERENCE = load_env("MDR_MIGRATION_TIME_REFERENCE")
MDR_MIGRATION_TYPE_OF_TREATMENT = load_env("MDR_MIGRATION_TYPE_OF_TREATMENT")
MDR_MIGRATION_UNIT_DIF = load_env("MDR_MIGRATION_UNIT_DIF")
MDR_MIGRATION_UNIT_DIMENSION = load_env("MDR_MIGRATION_UNIT_DIMENSION")
MDR_MIGRATION_UNIT_SUBSETS = load_env("MDR_MIGRATION_UNIT_SUBSETS")
MDR_MIGRATION_VISIT_CONTACT_MODE = load_env("MDR_MIGRATION_VISIT_CONTACT_MODE")
MDR_MIGRATION_VISIT_SUB_LABEL = load_env("MDR_MIGRATION_VISIT_SUB_LABEL")
MDR_MIGRATION_VISIT_TYPE = load_env("MDR_MIGRATION_VISIT_TYPE")
MDR_MIGRATION_DATATYPE = load_env("MDR_MIGRATION_DATATYPE")
MDR_MIGRATION_LANGUAGE = load_env("MDR_MIGRATION_LANGUAGE")
MDR_MIGRATION_EPOCH_ALLOCATION = load_env("MDR_MIGRATION_EPOCH_ALLOCATION")
MDR_MIGRATION_FREQUENCY = load_env("MDR_MIGRATION_FREQUENCY")
MDR_MIGRATION_TRIAL_TYPE = load_env("MDR_MIGRATION_TRIAL_TYPE")
MDR_MIGRATION_DATA_COLLECTION_MODE = load_env("MDR_MIGRATION_DATA_COLLECTION_MODE")
MDR_MIGRATION_CONFIRMATORY_PURPOSE = load_env("MDR_MIGRATION_CONFIRMATORY_PURPOSE")
MDR_MIGRATION_NONCONFIRMATORY_PURPOSE = load_env("MDR_MIGRATION_NONCONFIRMATORY_PURPOSE")
MDR_MIGRATION_TRIAL_BLINDING_SCHEMA = load_env("MDR_MIGRATION_TRIAL_BLINDING_SCHEMA")

# Import terms to standard codelists in sponsor library
class StandardCodelistTerms2(BaseImporter):
    logging_name = "standard_codelistterms2"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)

    @open_file_async()
    async def migrate_term(self, csvfile, codelist_name, code_lists_uids, session):
        self.ensure_cache()
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks = []

        existing_rows = self.api.get_all_identifiers(
            self.api.get_all_from_api(f"/ct/terms/names?codelist_name={codelist_name}"),
            identifier="sponsorPreferredName",
            value="codelistUid",
        )

        if codelist_name == self.visit_type_codelist_name:
            all_epoch_type_code_subm_values = self.api.get_all_identifiers(
                self.api.get_all_from_api(
                    "/ct/terms/attributes?codelist_name=Epoch Type"
                ),
                identifier="codeSubmissionValue",
                value="termUid",
            )
        if codelist_name == self.element_subtype_codelist_name:
            all_element_type_code_subm_values = self.api.get_all_identifiers(
                self.api.get_all_from_api(
                    "/ct/terms/attributes?codelist_name=Element Type"
                ),
                identifier="codeSubmissionValue",
                value="termUid",
            )
        for row in readCSV:
            data = {
                "path": "/ct/terms",
                "codelist": row[headers.index("CT_CD_LIST_SUBMVAL")],
                "body": {
                    "catalogueName": "SDTM CT",
                    "codeSubmissionValue": row[headers.index("CT_SUBMVAL")],
                    "nameSubmissionValue": row[headers.index("CT_SUBMVAL")],
                    "nciPreferredName": "UNK",
                    "definition": row[headers.index("DEFINITION")],
                    "sponsorPreferredName": row[headers.index("CT_NAME")],
                    "sponsorPreferredNameSentenceCase": row[
                        headers.index("NAME_SENTENSE_CASE")
                    ],
                    "libraryName": "Sponsor",
                    "order": row[headers.index("ORDER")]
                    if row[headers.index("ORDER")] != ""
                    else None,
                },
            }
            if codelist_name == self.visit_type_codelist_name:
                linked_epoch_types = row[headers.index("EPOCHS")].split(",")
                valid_epoch_uids = []
                for epoch_type in linked_epoch_types:
                    if epoch_type in all_epoch_type_code_subm_values:
                        valid_epoch_uids.append(
                            all_epoch_type_code_subm_values[epoch_type]
                        )
                data["validEpochUids"] = valid_epoch_uids
            if codelist_name == self.element_subtype_codelist_name:
                element_type_subm_value = row[headers.index("GEN_ELEM_TYPE")]
                if element_type_subm_value in all_element_type_code_subm_values:
                    data["elementTypeUid"] = all_element_type_code_subm_values[
                        element_type_subm_value
                    ]

            if codelist_name in code_lists_uids:
                data["body"]["codelistUid"] = code_lists_uids[codelist_name]
            else:
                metrics.icrement(
                    data["path"]
                    + f"-Names {codelist_name} - SkippedASMissingCodelistUid"
                )
                continue
            # if not existing_rows.get(data["body"]["sponsorPreferredName"]):
            api_tasks.append(
                self.process_simple_term_migration(data=data, session=session)
            )
        await asyncio.gather(*api_tasks)

    async def async_run(self):
        # we have to get all codelists when sponsor one will be migrated
        # otherwise sponsor defined terms won't know to which codelist they should connect
        code_lists_uids = self.api.get_code_lists_uids()
        timeout = aiohttp.ClientTimeout(None)
        conn = aiohttp.TCPConnector(limit=4, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
            await self.migrate_term(
                MDR_MIGRATION_VISIT_SUB_LABEL,
                codelist_name="Visit Sub Label",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_CRITERIA_TYPE,
                codelist_name="Criteria Type",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_CRITERIA_CATEGORY,
                codelist_name="Criteria Category",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_CRITERIA_SUB_CATEGORY,
                codelist_name="Criteria Sub Category",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_ENDPOINT_CATEGORY,
                codelist_name="Endpoint Category",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_ENDPOINT_SUB_CATEGORY,
                codelist_name="Endpoint Sub Category",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_ENDPOINT_SUB_LEVEL,
                codelist_name="Endpoint Sub Level",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_OBJECTIVE_CATEGORY,
                codelist_name="Objective Category",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_OPERATOR,
                codelist_name="Operator",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_FLOWCHART_GROUP,
                codelist_name="Flowchart Group",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_VISIT_CONTACT_MODE,
                codelist_name="Visit Contact Mode",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_ARM_TYPE,
                codelist_name="Arm Type",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_UNIT_SUBSETS,
                codelist_name="Unit Subset",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_NULL_FLAVOR,
                codelist_name="Null Flavor",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_THERAPY_AREA,
                codelist_name="Therapeutic area",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_TIME_REFERENCE,
                codelist_name="Time Point Reference",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_TYPE_OF_TREATMENT,
                codelist_name="Type of Treatment",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_COMPOUND_DISPENSED_IN,
                codelist_name="Compound Dispensed In",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_DEVICE,
                codelist_name="Delivery Device",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_ELEMENT_TYPE,
                codelist_name="Element Type",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_ELEMENT_SUBTYPE,
                codelist_name="Element Sub Type",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_LANGUAGE,
                codelist_name="Language",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_DATATYPE,
                codelist_name="Data type",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            # Migration of Visit Types have to go after epoch type as we link the Visit Type term to the specific
            # Epoch to allow using Visit Types only valid for specific Epoch Type context
            await self.migrate_term(
                MDR_MIGRATION_VISIT_TYPE,
                codelist_name=self.visit_type_codelist_name,
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_EPOCH_ALLOCATION,
                codelist_name="Epoch Allocation",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_FREQUENCY,
                codelist_name="Frequency",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_TRIAL_TYPE,
                codelist_name="Trial Type",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_DATA_COLLECTION_MODE,
                codelist_name="Data Collection Mode",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_CONFIRMATORY_PURPOSE,
                codelist_name="Confirmatory Purpose",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_NONCONFIRMATORY_PURPOSE,
                codelist_name="Non-confirmatory Purpose",
                code_lists_uids=code_lists_uids,
                session=session,
            )
            await self.migrate_term(
                MDR_MIGRATION_TRIAL_BLINDING_SCHEMA,
                codelist_name="Trial Blinding Schema",
                code_lists_uids=code_lists_uids,
                session=session,
            )

    def run(self):
        self.log.info("Migrating sponsor terms")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_run())
        self.log.info("Done migrating sponsor terms")


def main():
    metr = Metrics()
    migrator = StandardCodelistTerms2(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
