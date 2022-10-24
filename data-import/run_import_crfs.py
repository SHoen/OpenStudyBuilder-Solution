from importers.importer import BaseImporter, open_file
from importers.metrics import Metrics
import csv
from importers.functions.parsers import (
    map_boolean,
    map_boolean_exc,
    update_uid_list_dict,
)
from importers.functions.utils import load_env

import json

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
API_BASE_URL = load_env("API_BASE_URL")
MDR_MIGRATION_ODM_TEMPLATES = load_env("MDR_MIGRATION_ODM_TEMPLATES")
MDR_MIGRATION_ODM_FORMS = load_env("MDR_MIGRATION_ODM_FORMS")
MDR_MIGRATION_ODM_ITEMGROUPS = load_env("MDR_MIGRATION_ODM_ITEMGROUPS")
MDR_MIGRATION_ODM_ITEMS = load_env("MDR_MIGRATION_ODM_ITEMS")
MDR_MIGRATION_ODM_ALIAS = load_env("MDR_MIGRATION_ODM_ALIAS")

# library,oid,name,effectivedate,retireddate
odm_template = lambda data: {
    "path": "/concepts/odms/templates",
    "body": {
        "name": data["name"],
        "libraryName": data["library"],
        "oid": data["oid"],
        "effectiveDate": data["effectivedate"],
        "retiredDate": data["retireddate"],
        "description": f"description for {data['name']}",
    },
}

# library,uid,context,name
odm_alias = lambda data: {
   "path": "/concepts/odms/aliases",
   "body": {
       "name": data["name"],
       "libraryName": data["library"],
       "context": data["context"]
   }
}

# library,oid,name,prompt,repeating,language,description,instruction
odm_form = lambda data, alias_uids: {
    "path": "/concepts/odms/forms/create",
    "body": {
        "name": data["name"],
        "libraryName": data["library"],
        "oid": data["oid"],
        "repeating": "yes" if data["repeating"].lower() == "true" else "no",
        "descriptions": [
            {
                "name": data["name"],
                "libraryName": data["library"],
                "language": data["language"],
                "description": data["description"],
                "instruction": data["instruction"],
                "sponsorInstruction": "",
            }
        ],
        "aliasUids": alias_uids,
    },
}
# not used:
#        "sdtmVersion": "string",
#        "scopeUid": "string",

# library,oid,name,prompt,repeating,isreferencedata,sasdatasetname,domain,origin,purpose,comment,language,description,instruction
odm_itemgroup = lambda data, alias_uids, domain_uids: {
    "path": "/concepts/odms/item-groups/create",
    "body": {
        "name": data["name"],
        "libraryName": data["library"],
        "oid": data["oid"],
        "repeating": "yes" if data["repeating"].lower() == "true" else "no",
        "isReferenceData": "yes" if data["isreferencedata"].lower() == "true" else "no",
        "sasDatasetName": data["sasdatasetname"],
        "origin": data["origin"],
        "purpose": data["purpose"],
        "locked": "no",
        "comment": data["comment"],
        "descriptions": [
            {
                "name": data["name"],
                "libraryName": data["library"],
                "language": data["language"],
                "description": data["description"],
                "instruction": data["instruction"],
                "sponsorInstruction": "",
            },
        ],
        "aliasUids": alias_uids,
        "sdtmDomainUids": domain_uids,
    },
}

# library,oid,name,prompt,datatype,length,significantdigits,codelist,term,unit,sasfieldname,sdsvarname,origin,comment,language,description,instruction
odm_item = lambda data, alias_uids, units, terms: {
    "path": "/concepts/odms/items/create",
    "body": {
        "name": data["name"],
        "libraryName": data["library"],
        "oid": data["oid"],
        "datatype": data["datatype"],
        "prompt": data["prompt"],
        "length": int(data["length"]),
        "significantDigits": int(data["significantdigits"]),
        "sasFieldName": data["sasfieldname"],
        "sdsVarName": data["sdsvarname"],
        "origin": data["origin"],
        "comment": data["comment"],
        "allowsMultiChoice": False,
        "descriptions": [
            {
                "name": "string",
                "libraryName": data["library"],
                "language": data["language"],
                "description": data["description"],
                "instruction": data["instruction"],
                "sponsorInstruction": "",
            },
        ],
        "aliasUids": alias_uids,
        "codelistUid": data["codelist"] if data["codelist"] != "" else None,
        "unitDefinitions": units,
        "terms": terms,
    },
}


class Crfs(BaseImporter):
    logging_name = "crfs"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)

    def _fetch_codelist_terms(self, codelists, codelist):
        if codelist not in codelists:
            new_codelist = {}
            terms = self.api.get_all_from_api(f"/ct/terms/attributes?codelist_uid={codelist}")
            for term in terms:
                new_codelist[term["conceptId"]] = term["termUid"]
                codelists[codelist] = new_codelist

    @open_file()
    def handle_odm_templates(self, csvfile):
        csvdata = csv.DictReader(csvfile)

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(f'Adding odm template {row["name"]}')
            data = odm_template(row)

            # Create template, and leave in draft state (no approve)
            # TODO check if it exists before posting?
            res = self.api.post_to_api(data)

    @open_file()
    def handle_odm_forms(self, csvfile):
        csvdata = csv.DictReader(csvfile)

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(f'Adding odm form {row["name"]}')
            data = odm_form(row, [])

            # Create template, and leave in draft state (no approve)
            # TODO check if it exists before posting?
            self.api.post_to_api(data)

    @open_file()
    def handle_odm_itemgroups(self, csvfile):
        csvdata = csv.DictReader(csvfile)
        domain_list = self.api.get_all_from_api(
            "/ct/terms?codelist_name=SDTM Domain Abbreviation"
        )
        all_sdtm_domains = {}
        for item in domain_list:
            all_sdtm_domains[item["attributes"]["codeSubmissionValue"]] = item[
                "termUid"
            ]

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(f'Adding odm item group {row["name"]}')

            # Look up sdtm domain
            domain = row["domain"].split("_")[1]
            domain_uid = all_sdtm_domains.get(domain)
            if domain is not None:
                domains = [domain_uid]
            else:
                domains = []
                self.log.warning(f"Unable to find domain {row['domain']}")

            data = odm_itemgroup(row, [], domains)

            # Create template, and leave in draft state (no approve)
            # TODO check if it exists before posting?
            self.api.post_to_api(data)

    @open_file()
    def handle_odm_items(self, csvfile):
        csvdata = csv.DictReader(csvfile)
        codelists = {}

        all_units = self.api.get_all_identifiers(
            self.api.get_all_from_api("/concepts/unit-definitions"),
            identifier="name",
            value="uid",
        )

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(f'Adding odm item {row["name"]}')

            codelist = row["codelist"]
            term_dicts = []
            if codelist != "":
                self._fetch_codelist_terms(codelists, codelist)
                terms = row["term"]
                if terms != "":
                    for term in terms.split("|"):
                        term = term.strip().split("_")[0]
                        term_uid = codelists.get(codelist, {}).get(term)
                        if term_uid is not None:
                            term_dict = {
                                "uid": term_uid,
                                "mandatory": True,
                                "order": len(term_dicts) + 1
                            }
                            term_dicts.append(term_dict)
                        else:
                            self.log.warning(f"Unable to find term {term} in codelist {codelist}")
            
            units = []
            unit = row["unit"]
            if unit != "":
                unit_uid = all_units.get(unit)
                if unit_uid is not None:
                    unit_dict = {
                        "uid": unit_uid,
                        "mandatory": True
                    }
                    units.append(unit_dict)
                else:
                    self.log.warning(f"Unable to find unit {unit}")


            data = odm_item(row, [], units, term_dicts)

            # Create template, and leave in draft state (no approve)
            # TODO check if it exists before posting?
            self.api.post_to_api(data)

    @open_file()
    def handle_odm_aliases(self, csvfile):
        csvdata = csv.DictReader(csvfile)

        for row in csvdata:
            if len(row) == 0:
                continue
            self.log.info(f'Adding odm alias {row["name"]}')
            data = odm_alias(row)

            # Create alias, and leave in draft state (no approve)
            # TODO check if it exists before posting?
            res = self.api.post_to_api(data)

    def run(self):
        self.log.info("Importing CRFs")
        self.handle_odm_templates(MDR_MIGRATION_ODM_TEMPLATES)
        self.handle_odm_forms(MDR_MIGRATION_ODM_FORMS)
        self.handle_odm_itemgroups(MDR_MIGRATION_ODM_ITEMGROUPS)
        self.handle_odm_items(MDR_MIGRATION_ODM_ITEMS)
        self.handle_odm_aliases(MDR_MIGRATION_ODM_ALIAS)
        self.log.info("Done importing CRFs")


def main():
    metr = Metrics()
    migrator = Crfs(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
