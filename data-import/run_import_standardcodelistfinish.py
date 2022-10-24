from importers.metrics import Metrics
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
MDR_MIGRATION_DOSAGE_FORM = load_env("MDR_MIGRATION_DOSAGE_FORM")

dosage_form = {
    "MDR_MIGRATION_DOSAGE_FORM": lambda row, headers: {
        "path": "/ct/terms",
        "uid": row[headers.index("CT_CD")],
        "body": {
            "sponsorPreferredName": row[headers.index("CD_VAL_LB")],
            "sponsorPreferredNameSentenceCase": row[headers.index("CD_VAL_LB_LC")],
            "changeDescription": "Migration",
        },
    }
}

# Finishing touches for standard codelists in sponsor library
class StandardCodelistFinish(BaseImporter):
    logging_name = "standard_codelists_finish"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)

    @open_file()
    def dosage_form(self, csvfile):
        # Add sponsor preferred names to dosage forms
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        for row in readCSV:
            # TODO check if already exists
            _class = "MDR_MIGRATION_DOSAGE_FORM"
            data = dosage_form[_class](row, headers)
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
                self.api.simple_approve2(
                    "/ct/terms", f"/{res['termUid']}/names/approve", label="Names"
                )

    def run(self):
        self.log.info("Finalizing sponsor library")
        self.dosage_form(MDR_MIGRATION_DOSAGE_FORM)
        self.log.info("Done finalizing sponsor library")


def main():
    metr = Metrics()
    migrator = StandardCodelistFinish(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
