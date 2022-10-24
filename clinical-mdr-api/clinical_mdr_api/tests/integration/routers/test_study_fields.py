import csv
import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.config import DEFAULT_STUDY_FIELD_CONFIG_FILE
from clinical_mdr_api.models.configuration import CTConfigPostInput
from clinical_mdr_api.models.utils import camel_case_data
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.configuration import CTConfigService
from clinical_mdr_api.services.libraries import create as create_library
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_FIELD_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.unit.domain.study_definition_aggregate.test_study_metadata import (
    initialize_ct_data_map,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class StudyFieldsTest(api.APITest):
    TEST_DB_NAME = "studyfieldstest"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_STUDY_FIELD_CYPHER)
        # create library
        create_library("Sponsor", True)
        # create catalogue
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
        for _, value in initialize_ct_data_map.items():
            if isinstance(value, list):
                for uid, name in value:
                    db.cypher_query(
                        """
                    MATCH (library:Library {name:"CDISC"})
                    MATCH (codelist_root {uid:"CTCodelist_000001"})
                    CREATE (library)-[:CONTAINS_TERM]->(term_root:CTTermRoot {uid: $uid})-[:HAS_NAME_ROOT]->
                    (term_ver_root:CTTermNameRoot)-[:LATEST]->(term_ver_value:CTTermNameValue {
                    name: $name,
                    name_sentence_case: $name
                    })
                    CREATE (term_ver_root)-[:LATEST_FINAL {
                    version:1.0,
                    status:"Final",
                    change_description:"test",
                    user_initials:"test",
                    start_date:datetime()}]->(term_ver_value)
                    CREATE (codelist_root)-[:HAS_TERM]->(term_root)
                    """,
                        {"uid": uid, "name": name},
                    )
            else:
                db.cypher_query(
                    """
                MATCH (library:Library {name:"CDISC"})
                MATCH (codelist_root {uid:"CTCodelist_000001"})
                CREATE (library)-[:CONTAINS_TERM]->(term_root:CTTermRoot {uid: $uid})-[:HAS_NAME_ROOT]->
                (term_ver_root:CTTermNameRoot)-[:LATEST]->(term_ver_value:CTTermNameValue {
                name: $name,
                name_sentence_case: $name})
                CREATE (term_ver_root)-[:LATEST_FINAL {
                version:1.0,
                status:"Final",
                change_description:"test",
                user_initials:"test",
                start_date:datetime()}]->(term_ver_value)
                CREATE (codelist_root)-[:HAS_TERM]->(term_root)
                """,
                    {"uid": value[0], "name": value[1]},
                )
        config_service = CTConfigService(
            user_id="TEST_IMPORT", meta_repository=MetaRepository()
        )
        with open(DEFAULT_STUDY_FIELD_CONFIG_FILE, encoding="UTF-8") as f:
            r = csv.DictReader(f)
            for line in r:
                data = camel_case_data(line)
                if data.get("configuredCodelistUid") != "":
                    db.cypher_query(
                        """
                            MERGE (lib:Library {name:"CDISC", is_editable:false})
                            MERGE (catalogue:CTCatalogue {name:"SDTM"})
                            CREATE (codelist:CTCodelistRoot {uid: $uid})-[:HAS_NAME_ROOT]->(codelist_ver_root:CTCodelistNameRoot)-
                            [:LATEST]->(codelist_ver_value:CTCodelistNameValue {name: $uid + 'name'})
                            CREATE (codelist_ver_root)-[lf:LATEST_FINAL]->(codelist_ver_value)
                            set lf.change_description = "Approved version"
                            set lf.start_date = datetime("2020-06-26T00:00:00")
                            set lf.status = "Final"
                            set lf.user_initials = "TODO initials"
                            set lf.version = '1.0'
                            MERGE (lib)-[:CONTAINS_CODELIST]->(codelist)
                            MERGE (catalogue)-[:HAS_CODELIST]->(codelist)""",
                        {"uid": data.get("configuredCodelistUid")},
                    )
                input_data = CTConfigPostInput(**data)
                config_service.post(input_data)

        catalogue_name = "catalogue"
        library_name = "Sponsor"
        codelist = create_codelist(
            name="time",  # "Hours",
            uid="C66781",  # "CTCodelist_00004-HOUR",
            catalogue=catalogue_name,
            library=library_name,
        )
        hour_term = create_ct_term(
            codelist=codelist.codelistUid,
            name="hours",  # "Hours",
            uid="hours001",  # "Hours_001",
            order=1,
            catalogue_name=catalogue_name,
            library_name=library_name,
        )
        subset_codelist = create_codelist(
            name="Unit Subset",
            uid="UnitSubsetCuid",
            catalogue=catalogue_name,
            library=library_name,
        )
        study_time_subset = create_ct_term(
            codelist=subset_codelist.codelistUid,
            name="Study Time",
            uid="StudyTimeSuid",
            order=1,
            catalogue_name=catalogue_name,
            library_name=library_name,
        )
        TestUtils.create_unit_definition(
            name="hours",
            libraryName="Sponsor",
            ctUnits=[hour_term.uid],
            unitSubsets=[study_time_subset.uid],
        )
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_fields.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "time",
            "date",
            "versionTimestamp",
            "userInitials",
            "uid",
            "studyUid",
        ]


class StudyFieldsNegativeTest(api.APITest):
    TEST_DB_NAME = "studyfields"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_STUDY_FIELD_CYPHER)
        for _, value in initialize_ct_data_map.items():
            if isinstance(value, list):
                for uid, name in value:
                    db.cypher_query(
                        """CREATE (:CTTermRoot {uid: $uid})-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->
                                (:CTTermNameValue {name: $name})""",
                        {"uid": uid, "name": name},
                    )
            else:
                db.cypher_query(
                    """CREATE (:CTTermRoot {uid: $uid})-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->
                            (:CTTermNameValue {name: $value})""",
                    {"uid": value[0], "value": value[1]},
                )
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_fields_negative.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "time",
            "date",
            "versionTimestamp",
            "userInitials",
            "uid",
            "studyUid",
        ]
