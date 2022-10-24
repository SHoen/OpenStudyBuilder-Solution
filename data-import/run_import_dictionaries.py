import copy
import csv
from importers.metrics import Metrics

from importers.functions.parsers import map_boolean
from importers.functions.utils import load_env
from importers.importer import BaseImporter, open_file


# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#

# DICTIONARIES
MDR_MIGRATION_DICTIONARIES_CODELISTS_DEFINITIONS = load_env(
    "MDR_MIGRATION_DICTIONARIES_CODELISTS_DEFINITIONS"
)
MDR_MIGRATION_SNOMED = load_env("MDR_MIGRATION_SNOMED")
MDR_MIGRATION_MED_RT = load_env("MDR_MIGRATION_MED_RT")
MDR_MIGRATION_UNII = load_env("MDR_MIGRATION_UNII")
MDR_MIGRATION_UCUM = load_env("MDR_MIGRATION_UCUM")


# ---------------------------------------------------------------
# Dictionaries codelists and terms
# ---------------------------------------------------------------

# DICTIONARIES CODELISTS DEFINITION
DICTIONARY_CODELISTS_DEFINITION_MAPPER = {
    "DICTIONARY_CODELIST_DEFINITION": lambda row, headers: {
        "path": "/dictionaries/codelists",
        "body": {
            "name": row[headers.index("dictionary_codelist_name")],
            "templateParameter": map_boolean(row[headers.index("template_parameter")]),
            "libraryName": row[headers.index("library")],
        },
    }
}

# SNOMED DEFINITION
SNOMED_DEFINITION_MAPPER = {
    "SNOMED": lambda row, headers: {
        "path": "/dictionaries/terms",
        "body": {
            "dictionaryId": row[headers.index("concept_id")],
            "name": row[headers.index("Preferred synonym")],
            "nameSentenceCase": row[
                headers.index("Preferred synonym in sentence case")
            ],
            "abbreviation": row[headers.index("Abbreviation")],
            "definition": row[headers.index("Fully specified name")],
            "codelistUid": None,
            "libraryName": "SNOMED",
        },
    }
}
# PClass DEFINITION
MED_RT_DEFINITION_MAPPER = {
    "MED-RT": lambda row, headers: {
        "path": "/dictionaries/terms",
        "body": {
            "name": row[headers.index("pclass_ndf_rt_concept")],
            "nameSentenceCase": row[headers.index("pclass_ndf_rt_concept")].lower(),
            "dictionaryId": row[headers.index("PCLASS_NDF_RT_NUI")],
            "definition": row[headers.index("pclass_ndf_rt_concept")],
            "codelistUid": None,
            "libraryName": "MED-RT",
        },
    }
}
# UNII DEFINITION
UNII_DEFINITION_MAPPER = {
    "UNII": lambda row, headers: {
        "path": "/dictionaries/substances",
        "body": {
            "name": row[headers.index("CD_VAL_LB")],
            "nameSentenceCase": row[headers.index("CD_VAL_LB")].lower(),
            "dictionaryId": row[
                headers.index("CD_VAL")
            ],  # find out which field is dictionaryID
            "codelistUid": None,
            "libraryName": "UNII",
            "pclassUid": None,
        },
    }
}

# UCUM DEFINITION
UCUM_DEFINITION_MAPPER = {
    "UCUM": lambda row, headers: {
        "path": "/dictionaries/terms",
        "body": {
            "name": row[headers.index("UCUM_CODE")],
            "nameSentenceCase": row[headers.index("UCUM_CODE")].lower(),
            "definition": row[
                headers.index(
                    "Description of the Unit (using UCUM descriptions where they exist)"
                )
            ],
            "abbreviation": "",
            "dictionaryId": "UCUM",
            "codelistUid": None,
            "libraryName": "UCUM",
        },
    }
}


class Dictionaries(BaseImporter):
    logging_name = "dictionaries"

    # Create the libraries
    def create_libraries(self):
        libs = self.api.get_libraries()
        new_libs = ["Sponsor", "SNOMED", "MED-RT", "UNII", "UCUM", "User Defined"]
        for lib in new_libs:
            self.log.info(f"Create library {lib}")
            if lib not in libs:
                self.create_library(lib)
            else:
                self.log.info(f"Library {lib} already exists")

    # Create a new library
    def create_library(self, new_lib):

        self.api.create_library({"name": new_lib, "isEditable": True})

    # Migrate codelist definitions
    @open_file()
    def dictionaries_codelists_definitions(self, textfile):
        csv_data = csv.reader(textfile, delimiter=",")
        headers = next(csv_data)
        # TODO why only check against SMOMED?
        all_dictionary_codelist_names = self.api.get_all_identifiers(
            self.api.get_all_from_api("/dictionaries/codelists/SNOMED"),
            identifier="name",
        )
        for row in csv_data:
            _class = "DICTIONARY_CODELIST_DEFINITION"
            data = DICTIONARY_CODELISTS_DEFINITION_MAPPER[_class](row, headers)
            if data["body"]["name"] not in all_dictionary_codelist_names:
                self.log.info(f"Add codelist '{data['body']['name']}'")
                res = self.api.post_to_api(data)
                if res is not None:
                    # Approve dictionary codelist
                    self.api.simple_approve2(
                        data["path"], f"/{res['codelistUid']}/approve", label="Names"
                    )
            else:
                self.log.info(f"Codelist '{data['body']['name']}' already exists")
                self.metrics.icrement(data["path"] + "--AlreadyExists")

    # Migrate data for one library
    def migrate_simple_dictionary_term(
        self, library, file_env_variable, mappings, codelist_name, encoding="utf-8"
    ):
        with open(file_env_variable, encoding=encoding, errors="ignore") as csvfile:
            csv_data = csv.reader(csvfile, delimiter=",")
            headers = next(csv_data)
            all_dictionary_codelist = self.api.get_all_identifiers(
                self.api.get_all_from_api(f"/dictionaries/codelists/{library}"),
                identifier="name",
                value="codelistUid",
            )

            if codelist_name in all_dictionary_codelist:
                dictionary_codelist_uid = all_dictionary_codelist[codelist_name]
            else:
                self.log.error(
                    f"Codelist '{codelist_name}' does not exist, skipping file '{file_env_variable}'"
                )
                self.metrics.icrement("/dictionaries/codelists" + "--CodelistNotExists")
                return

            all_dictionary_terms_names = self.api.get_all_identifiers(
                self.api.get_all_from_api(
                    f"/dictionaries/terms?codelist_uid={dictionary_codelist_uid}"
                ),
                identifier="name",
            )

            for row in csv_data:
                _class = library
                data = mappings[_class](row, headers)

                # some of the records in pclass file are containing data
                # for two separate pclass items which are separated by |
                if "|" in data["body"]["name"]:
                    multiple_rows = []
                    dictionary_names = data["body"]["name"].split("|")
                    dictionary_name_sentence_cases = data["body"][
                        "nameSentenceCase"
                    ].split("|")
                    dictionary_ids = data["body"]["dictionaryId"].split("|")
                    dictionary_definitions = data["body"]["definition"].split("|")
                    for name, nsc, dict_id, defin in zip(
                        dictionary_names,
                        dictionary_name_sentence_cases,
                        dictionary_ids,
                        dictionary_definitions,
                    ):
                        data = copy.deepcopy(data)
                        data["body"]["name"] = name
                        data["body"]["nameSentenceCase"] = nsc
                        data["body"]["dictionaryId"] = dict_id
                        data["body"]["definition"] = defin
                        multiple_rows.append(data)
                # the '|' was not spotted, migrate just simple records
                else:
                    multiple_rows = [data]
                for data in multiple_rows:
                    if data["body"]["name"] not in all_dictionary_terms_names:
                        self.log.info(
                            f"Add item '{data['body']['name']}' to codelist '{codelist_name}'"
                        )
                        data["body"]["codelistUid"] = dictionary_codelist_uid
                        res = self.api.post_to_api(data)
                        if res is not None:
                            # Approve dictionary term
                            self.api.simple_approve2(
                                data["path"],
                                f"/{res['termUid']}/approve",
                                label="Names",
                            )
                    else:
                        self.log.info(
                            f"Item '{data['body']['name']}' already exists in codelist '{codelist_name}'"
                        )
                        self.metrics.icrement(data["path"] + "--AlreadyExists")

    def migrate_substances(
        self, library, file_env_variable, mappings, codelist_name, encoding="utf-8"
    ):
        pclass_codelists = self.api.get_all_from_api("/dictionaries/codelists/MED-RT")
        all_pclass_terms = {}
        for pclass_codelist in pclass_codelists:
            all_pclass_terms.update(
                self.api.get_all_identifiers(
                    self.api.get_all_from_api(
                        "/dictionaries/terms",
                        params={"codelist_uid": pclass_codelist["codelistUid"]},
                    ),
                    "name",
                    "termUid",
                )
            )
        with open(file_env_variable, encoding=encoding, errors="ignore") as csvfile:
            readCSV = csv.reader(csvfile, delimiter=",")
            headers = next(readCSV)
            all_dictionary_codelist = self.api.get_all_identifiers(
                self.api.get_all_from_api(f"/dictionaries/codelists/{library}"),
                identifier="name",
                value="codelistUid",
            )

            if codelist_name in all_dictionary_codelist:
                dictionary_codelist_uid = all_dictionary_codelist[codelist_name]
            else:
                self.log.error(
                    "Codelist {codelist_name} not found, skipping import of {file_env_variable}"
                )
                self.metrics.icrement("/dictionaries/codelists" + "--CodelistNotExists")
                return

            all_substance_terms_names = self.api.get_all_identifiers(
                self.api.get_all_from_api(
                    f"/dictionaries/terms?codelist_uid={dictionary_codelist_uid}"
                ),
                identifier="name",
            )

            for row in readCSV:
                _class = library
                data = mappings[_class](row, headers)

                if data["body"]["name"] not in all_substance_terms_names:
                    data["body"]["codelistUid"] = dictionary_codelist_uid

                    if row[headers.index("PCLASS_NDF_RT_CONCEPT")] != "":
                        pclass_term_uid = all_pclass_terms.get(
                            row[headers.index("PCLASS_NDF_RT_CONCEPT")]
                        )
                        if pclass_term_uid:
                            data["body"]["pclassUid"] = pclass_term_uid
                    self.log.info(
                        f"Adding item '{data['body']['name']}' to codelist '{codelist_name}'"
                    )
                    res = self.api.post_to_api(data)
                    if res is not None:
                        # Approve dictionary term
                        if self.api.simple_approve(
                            "/dictionaries/terms/" + res["termUid"] + "/approve"
                        ):
                            self.metrics.icrement(data["path"] + "--Approve")
                        else:
                            self.metrics.icrement(data["path"] + "--ApproveError")
                else:
                    self.log.info(
                        f"Item '{data['body']['name']}' already exists in codelist '{codelist_name}', skipping"
                    )
                    self.metrics.icrement(data["path"] + "--AlreadyExists")

    def run(self):
        self.log.info("Migrating dictionaries")
        self.create_libraries()
        self.dictionaries_codelists_definitions(
            MDR_MIGRATION_DICTIONARIES_CODELISTS_DEFINITIONS
        )

        self.migrate_simple_dictionary_term(
            library="SNOMED",
            file_env_variable=MDR_MIGRATION_SNOMED,
            mappings=SNOMED_DEFINITION_MAPPER,
            codelist_name="DiseaseDisorder",
        )
        self.migrate_simple_dictionary_term(
            library="MED-RT",
            file_env_variable=MDR_MIGRATION_MED_RT,
            mappings=MED_RT_DEFINITION_MAPPER,
            codelist_name="PClass",
        )
        self.migrate_simple_dictionary_term(
            library="UCUM",
            file_env_variable=MDR_MIGRATION_UCUM,
            mappings=UCUM_DEFINITION_MAPPER,
            codelist_name="UCUM",
            encoding="iso-8859-1",
        )
        self.migrate_substances(
            library="UNII",
            file_env_variable=MDR_MIGRATION_UNII,
            mappings=UNII_DEFINITION_MAPPER,
            codelist_name="UNII",
        )
        self.log.info("Done migrating dictionaries")


def main():
    metr = Metrics()
    migrator = Dictionaries(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
