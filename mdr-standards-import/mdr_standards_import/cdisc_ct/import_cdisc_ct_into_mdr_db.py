import time
import re
from mdr_standards_import.cdisc_ct.utils import are_lists_equal, get_sentence_case_string

USER_INITIALS = None

def print_ignored_stats(tx, effective_date):
    result = tx.run(
        """
        MATCH (import:Import{effective_date: date($effective_date)})
        
        CALL { WITH import
            MATCH (import)-[:INCLUDES]->(package)
            WHERE (:Inconsistency)-[:AFFECTS_PACKAGE]->(package)
            RETURN count(package) AS num_packages
        } 
        
        CALL { WITH import
            MATCH (import)-[:INCLUDES]->(package)-[:CONTAINS]->(codelist)
            WHERE (:Inconsistency)-[:AFFECTS_CODELIST]->(codelist)
            RETURN count(DISTINCT codelist) AS num_codelists
        }
        
        CALL { WITH import
            MATCH (import)-[:INCLUDES]->(package)-[:CONTAINS_TERM]->(term)
            WHERE (:Inconsistency)-[:AFFECTS_TERM]->(term)
            RETURN count(DISTINCT term) AS num_terms
        }

        RETURN num_packages, num_codelists, num_terms
        """,
        effective_date=effective_date
    ).single()

    print(f"==  ! Unresolved inconsistencies will not be imported !")
    print(f"==  ! The following concepts will be ignored:")
    print(f"==     # packages: {result.get('num_packages', 'n/a')}")
    print(f"==    # codelists: {result.get('num_codelists', 'n/a')}")
    print(f"==        # terms: {result.get('num_terms', 'n/a')}")
    print(f"==")


def get_packages(tx, effective_date):
    packages_data = tx.run(
        """
        MATCH (:Import{effective_date: date($effective_date)})-[:INCLUDES]->(package)
        WHERE NOT (:Inconsistency)-[:AFFECTS_PACKAGE]->(package)
        RETURN
            package{uid: package.name, .name, .catalogue_name} AS package,
            [(package)-[:CONTAINS]->(codelist) | codelist{uid: codelist.concept_id, .concept_id}] AS codelists
        """,
        effective_date=effective_date
    ).data()

    # packages = []
    # for package_data in packages_data:
    #     packages.append(Package.from_node_record(package_data))
    
    return packages_data


def get_codelists(tx, effective_date):
    result = tx.run(
        """
        MATCH (:Import{effective_date: date($effective_date)})
            -[:INCLUDES]->(package)-[:CONTAINS]->(codelist)
        WHERE NOT (:Inconsistency)-[:AFFECTS_PACKAGE]->(package) AND
              NOT (:Inconsistency)-[:AFFECTS_CODELIST]->(codelist)
        WITH
            codelist,
            collect(DISTINCT package) AS packages
        CALL { WITH codelist
            MATCH (codelist)-[:CONTAINS]->(term)
            WHERE NOT (:Inconsistency)-[:AFFECTS_TERM]->(term)
            RETURN collect({
                term: term{
                    uid: term.concept_id + '_' + term.code_submission_value,
                    .concept_id, .code_submission_value, .name_submission_value, .preferred_term, .definition, .synonyms
                },
                packages: [(term)<-[:CONTAINS_TERM]-(package) | package]
            }) AS terms_data
        }
        RETURN
            codelist,
            terms_data,
            packages
        """,
        effective_date=effective_date
    )
    return result.data()


# TODO compare performance with merge_version_independent_data2 and pick the quicker one
def merge_version_independent_data1(tx, codelists_data):
    # for each codelist
    for data in codelists_data:
        codelist_concept_id = data['codelist']['concept_id']

        tx.run(
            """
            MATCH (library:Library{name: 'CDISC'})
            MERGE (cl_root:CTCodelistRoot{uid: $codelist_concept_id})
            MERGE (library)-[:CONTAINS_CODELIST]->(cl_root)
            MERGE (cl_root)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
            MERGE (cl_root)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)
            """,
            codelist_concept_id=codelist_concept_id
        )

        # for each package that contains the codelist
        for package in data['packages']:
            tx.run(
                """
                MATCH (cl_root:CTCodelistRoot{uid: $codelist_concept_id})
                MERGE (catalogue:CTCatalogue{name: $package.catalogue_name})
                MERGE (catalogue)-[:HAS_CODELIST]->(cl_root)

                MERGE (ct_package:CTPackage{uid: $package.name})
                MERGE (package_codelist:CTPackageCodelist{uid: $package.name + '_' + $codelist_concept_id})
                MERGE (ct_package)-[:CONTAINS_CODELIST]->(package_codelist)
                """,
                codelist_concept_id=codelist_concept_id,
                package=package
            )

    # for each codelist
    for data in codelists_data:
        codelist_concept_id = data['codelist']['concept_id']
        # for each term of the codelist
        for term_data in data['terms_data']:
            term_uid = term_data['term']['uid']
            tx.run(
                """
                MATCH (library:Library{name: 'CDISC'})
    
                MERGE (t_root:CTTermRoot{uid: $term_uid})
                MERGE (library)-[:CONTAINS_TERM]->(t_root)
                MERGE (t_root)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)
                MERGE (t_root)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)
                """,
                term_uid=term_uid
            )

            # for each package that contains the term
            for package in term_data['packages']:
                tx.run(
                    """
                    MERGE (package_codelist:CTPackageCodelist{uid: $package.name + '_' + $codelist_concept_id})
                    MERGE (package_term:CTPackageTerm{uid: $package.name + "_" + $term_uid})
                    MERGE (package_codelist)-[:CONTAINS_TERM]->(package_term)
                    """,
                    codelist_concept_id=codelist_concept_id,
                    term_uid=term_uid,
                    package=package
                )


def merge_version_independent_data2(tx, codelists_data):
    tx.run(
        """
        MERGE (library:Library{name: 'CDISC'})
        WITH library
        // for each codelist
        UNWIND $codelists_data AS data
            MERGE (cl_root:CTCodelistRoot{uid: data.codelist.concept_id})
            MERGE (library)-[:CONTAINS_CODELIST]->(cl_root)
            MERGE (cl_root)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)
            MERGE (cl_root)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)
            
            WITH library, data, cl_root
            // for each catalogue that has this codelist 
            FOREACH (package IN data.packages |
                MERGE (ct_package:CTPackage{uid: package.name})
                MERGE (catalogue:CTCatalogue{name: package.catalogue_name})
                MERGE (catalogue)-[:HAS_CODELIST]->(cl_root)
                MERGE (package_codelist:CTPackageCodelist{uid: package.name + '_' + data.codelist.concept_id})
                MERGE (ct_package)-[:CONTAINS_CODELIST]->(package_codelist)
            )
            
            WITH library, data, cl_root
            // for each term of the codelist
            //UNWIND data.terms AS term
            FOREACH (term_data IN data.terms_data |
                MERGE (t_root:CTTermRoot{uid: term_data.term.uid})
                SET t_root.concept_id = term_data.term.concept_id
                MERGE (library)-[:CONTAINS_TERM]->(t_root)
                MERGE (t_root)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)
                MERGE (t_root)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)
                FOREACH (package IN term_data.packages |
                    MERGE (package_codelist:CTPackageCodelist{uid: package.name + '_' + data.codelist.concept_id})
                    MERGE (package_term:CTPackageTerm{uid: package.name + "_" + term_data.term.uid})
                    MERGE (package_codelist)-[:CONTAINS_TERM]->(package_term)
                )
            )
        """,
        codelists_data=codelists_data,
        user_initials=USER_INITIALS
    )


def update_has_term_and_had_term_relationships(tx, codelists_data, effective_date):
    for codelist_data in codelists_data:
        codelist = codelist_data.get('codelist', None)

        new_term_uids = [terms_data["term"]["uid"] for terms_data in codelist_data["terms_data"]]
        result = tx.run(
            """
            MATCH (:CTCodelistRoot{uid: $codelist_uid})-[:HAS_TERM]->(term_root)
            RETURN DISTINCT term_root.uid AS uid
            """,
            codelist_uid=codelist["concept_id"]
        )
        existing_term_uids = list(result.value())

        term_uids_to_deactivate = [term_uid for term_uid in existing_term_uids if not term_uid in new_term_uids]
        tx.run(
            """
            MATCH (codelist_root:CTCodelistRoot{uid: $codelist_uid})-[has_term:HAS_TERM]->(term_root)
            WHERE term_root.uid IN $term_uids_to_deactivate

            CREATE (codelist_root)-[had_term:HAD_TERM]->(term_root)
            SET
                had_term.start_date = has_term.start_date,
                had_term.end_date = datetime($end_date),
                had_term.user_initials = has_term.user_initials
            DELETE has_term
            """,
            end_date=effective_date,
            codelist_uid=codelist["concept_id"],
            term_uids_to_deactivate=term_uids_to_deactivate
        )
        term_uids_to_add = [term_uid for term_uid in new_term_uids if not term_uid in existing_term_uids]
        tx.run(
            """
            MATCH (codelist_root:CTCodelistRoot{uid: $codelist_uid})
            MATCH (term_root:CTTermRoot)
            WHERE term_root.uid IN $new_term_uids

            CREATE (codelist_root)-[:HAS_TERM{
                start_date: datetime($start_date),
                user_initials: $user_initials
            }]->(term_root)
            """,
            start_date=effective_date,
            codelist_uid=codelist["concept_id"],
            new_term_uids=term_uids_to_add,
            user_initials=USER_INITIALS
        )
    # delete_contains_term_relationships(tx)


def delete_contains_term_relationships(tx):
    result = tx.run(
        """
        MATCH (library:Library{name: 'CDISC'})-[contains_term:CONTAINS_TERM]->(term_root)
        WHERE NOT (:CTCodelistRoot)-[:HAS_TERM]->(term_root)
        DELETE contains_term
        RETURN collect(term_root.uid) AS term_concept_ids_that_have_been_removed
        """
    ).single()

    return result.get('term_concept_ids_that_have_been_removed', [])



def merge_structure_nodes_and_relationships(tx, packages_data, codelists_data, effective_date):
    merge_catalogues_and_packages(tx, packages_data, effective_date)
    merge_version_independent_data2(tx, codelists_data)


def merge_catalogues_and_packages(tx, packages_data, effective_date):
    tx.run(
        """
        MERGE (library:Library{name: 'CDISC'})
        ON CREATE SET library.is_editable = false
        WITH library
        UNWIND $packages_data AS package_data
            MERGE (catalogue:CTCatalogue{name: package_data.package.catalogue_name})
            MERGE (library)-[:CONTAINS_CATALOGUE]->(catalogue)
            MERGE (package:CTPackage{uid: package_data.package.name})
            ON CREATE SET
                package.name = package_data.package.name,
                package.label = package_data.package.label,
                package.description = package_data.package.description,
                package.source = package_data.package.source,
                package.effective_date = date($effective_date),
                package.registration_status = package_data.package.registration_status,
                package.href = package_data.package.href,
                
                package.import_date = datetime(),
                package.user_initials = $user_initials
            MERGE (catalogue)-[:CONTAINS_PACKAGE]->(package)
        """,
        packages_data=packages_data,
        effective_date=effective_date,
        user_initials=USER_INITIALS
    )


# def retire_codelists(tx, packages: Sequence[Package]):
#     for package in packages:
#         codelist_concept_ids = [codelist.concept_id for codelist in package.codelists]
#         removed_codelist_concept_ids = \
#             delete_has_codelist_relationships(tx, package.catalogue_name, codelist_concept_ids)
#         print(f"      - Removed the following codelists from the catalogue='{package.catalogue_name}': {removed_codelist_concept_ids}")

#     codelist_concept_ids_for_retirement = get_codelists_for_retirement(tx)
#     for concept_id in codelist_concept_ids_for_retirement:
#         retire_codelist_attributes_value(tx, concept_id)
#         retire_codelist_name_value(tx, concept_id)
#     removed_codelist_concept_ids = delete_contains_codelist_relationships(tx, codelist_concept_ids_for_retirement)
#     print(f"      - Retired and removed the following codelists from the CDISC library: {removed_codelist_concept_ids}")
def retire_codelists(tx, packages_data):
    for package_data in packages_data:
        package = package_data.get('package')
        codelist_concept_ids = [codelist.get('concept_id') for codelist in package_data.get('codelists', [])]
        removed_codelist_concept_ids = \
            delete_has_codelist_relationships(tx, package.get('catalogue_name'), codelist_concept_ids)
        print(f"==    - Removed the following codelists from the catalogue='{package.get('catalogue_name')}': {removed_codelist_concept_ids}")

    codelist_concept_ids_for_retirement = get_codelists_for_retirement(tx)
    for concept_id in codelist_concept_ids_for_retirement:
        retire_codelist_attributes_value(tx, concept_id)
        retire_codelist_name_value(tx, concept_id)
    removed_codelist_concept_ids = delete_contains_codelist_relationships(tx, codelist_concept_ids_for_retirement)
    print(f"==    - Retired and removed the following codelists from the CDISC library: {removed_codelist_concept_ids}")


def delete_has_codelist_relationships(tx, catalogue_name, existing_codelist_concept_ids):
    result = tx.run(
        """
        MATCH (catalogue:CTCatalogue{name: $catalogue_name})-[has_codelist:HAS_CODELIST]->(codelist_root)
        WHERE NOT codelist_root.uid IN $codelist_concept_ids
        DELETE has_codelist
        RETURN collect(codelist_root.uid) AS codelist_concept_ids_that_have_been_removed
        """,
        catalogue_name=catalogue_name,
        codelist_concept_ids=existing_codelist_concept_ids,
    ).single()

    return result.get('codelist_concept_ids_that_have_been_removed', [])


def get_codelists_for_retirement(tx):
    result = tx.run(
        """
        MATCH (codelist_root:CTCodelistRoot)
        WHERE NOT ()-[:HAS_CODELIST]->(codelist_root)
        RETURN collect(codelist_root.uid) AS codelist_concept_ids_for_retirement
        """
    ).single()
    return result.get('codelist_concept_ids_for_retirement', [])


# TODO use the uid as the codelist identifier
def retire_codelist_attributes_value(tx, codelist_concept_id):
    tx.run(
        """
        MATCH (:CTCodelistRoot{uid: $concept_id})-[:HAS_ATTRIBUTES_ROOT]
            ->(cl_attributes_root)-[latest_final:LATEST_FINAL]->(cl_current_attributes_value)
            <-[:LATEST]-(cl_attributes_root)
        WITH cl_attributes_root, cl_current_attributes_value, latest_final, latest_final.version AS version
        MATCH (cl_attributes_root)-[has_version:HAS_VERSION]->(cl_current_attributes_value)
        SET has_version.end_date = datetime()
        DELETE latest_final
       
        WITH cl_attributes_root, cl_current_attributes_value, version LIMIT 1
        CREATE (cl_attributes_root)-[:LATEST_RETIRED{
            start_date: datetime(),
            status: 'Retired',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: 'The codelist was discontinued by CDISC.',
            user_initials: $user_initials
        }]->(cl_current_attributes_value)
        CREATE (cl_attributes_root)-[:HAS_VERSION{
            start_date: datetime(),
            status: 'Retired',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: 'The codelist was discontinued by CDISC.',
            user_initials: $user_initials
        }]->(cl_current_attributes_value)
        """,
        concept_id=codelist_concept_id,
        user_initials=USER_INITIALS,
    )


def retire_codelist_name_value(tx, codelist_concept_id):
    tx.run(
        """
        MATCH (:CTCodelistRoot{uid: $concept_id})-[:HAS_NAME_ROOT]
            ->(cl_name_root)-[latest_final:LATEST_FINAL]->(cl_current_name_value)
            <-[:LATEST]-(cl_name_root)
        WITH cl_name_root, cl_current_name_value, latest_final, latest_final.version AS version
        MATCH (cl_name_root)-[has_version:HAS_VERSION]->(cl_current_name_value)
        SET has_version.end_date = datetime()
        DELETE latest_final

        WITH cl_name_root, cl_current_name_value, version LIMIT 1
        CREATE (cl_name_root)-[:LATEST_RETIRED{
            start_date: datetime(),
            status: 'Retired',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: 'The codelist was discontinued by CDISC.',
            user_initials: $user_initials
        }]->(cl_current_name_value)
        CREATE (cl_name_root)-[:HAS_VERSION{
            start_date: datetime(),
            status: 'Retired',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: 'The codelist was discontinued by CDISC.',
            user_initials: $user_initials
        }]->(cl_current_name_value)
        """,
        concept_id=codelist_concept_id,
        user_initials=USER_INITIALS,
    )


def delete_contains_codelist_relationships(tx, codelist_concept_ids):
    result = tx.run(
        """
        MATCH (library:Library{name: 'CDISC'})-[contains_codelist:CONTAINS_CODELIST]->(codelist_root)
        WHERE codelist_root.uid IN $codelist_concept_ids
        DELETE contains_codelist
        RETURN collect(codelist_root.uid) AS codelist_concept_ids_that_have_been_removed
        """,
        codelist_concept_ids=codelist_concept_ids,
    ).single()

    return result.get('codelist_concept_ids_that_have_been_removed', [])


def retire_term(tx, concept_id, effective_date):
    reason = f"There are multiple submission values where each is dependent on the codelist. " \
             f"So we split this term and created multiple terms where the concept_id starts with '{concept_id}_' " \
             f"followed by the submission value."

    retire_term_attributes_value(tx, concept_id, effective_date, reason)
    retire_term_name_value(tx, concept_id, effective_date, reason)


def retire_term_attributes_value(tx, term_uid, effective_date, reason):
    tx.run(
        """
        MATCH (:CTTermRoot{uid: $term_uid})-[:HAS_ATTRIBUTES_ROOT]
            ->(attributes_root)-[latest_final:LATEST_FINAL]->(current_attributes_value)
            <-[:LATEST]-(attributes_root)
        WITH attributes_root, current_attributes_value, latest_final, latest_final.version AS version
        MATCH (attributes_root)-[has_version:HAS_VERSION]->(current_attributes_value)
        SET has_version.end_date = datetime($effective_date_string)
        DELETE latest_final

        WITH attributes_root, current_attributes_value, version LIMIT 1
        CREATE (attributes_root)-[:LATEST_RETIRED{
            start_date: datetime($effective_date_string),
            status: 'Retired',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: $change_description,
            user_initials: $user_initials
        }]->(current_attributes_value)
        CREATE (attributes_root)-[:HAS_VERSION{
            start_date: datetime($effective_date_string),
            status: 'Retired',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: $change_description,
            user_initials: $user_initials
        }]->(current_attributes_value)
        """,
        term_uid=term_uid,
        effective_date_string=effective_date,
        change_description=reason,
        user_initials=USER_INITIALS
    )


def retire_term_name_value(tx, term_uid, effective_date, reason):
    tx.run(
        """
        MATCH (:CTTermRoot{uid: $term_uid})-[:HAS_NAME_ROOT]
            ->(name_root)-[latest_final:LATEST_FINAL]->(current_name_value)
            <-[:LATEST]-(name_root)
        WITH name_root, current_name_value, latest_final, latest_final.version AS version
        MATCH (name_root)-[has_version:HAS_VERSION]->(current_name_value)
        SET has_version.end_date = datetime($effective_date_string)
        DELETE latest_final

        WITH name_root, current_name_value, version LIMIT 1
        CREATE (name_root)-[:LATEST_RETIRED{
            start_date: datetime($effective_date_string),
            status: 'Retired',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: $change_description,
            user_initials: $user_initials
        }]->(current_name_value)
        CREATE (name_root)-[:HAS_VALUE{
            start_date: datetime($effective_date_string),
            status: 'Retired',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: $change_description,
            user_initials: $user_initials
        }]->(current_name_value)
        """,
        term_uid=term_uid,
        effective_date_string=effective_date,
        change_description=reason,
        user_initials=USER_INITIALS
    )


def update_attributes(tx, codelists_data, effective_date):
    for codelist_data in codelists_data:
        codelist = codelist_data.get('codelist', None)
        terms_data = codelist_data.get('terms_data', {})
        packages = codelist_data.get('packages', None)

        result = tx.run(
            """
            MATCH (:CTCodelistRoot{uid: $codelist.concept_id})-[:HAS_ATTRIBUTES_ROOT]->()-[:LATEST]->(cl_attributes_value)
            RETURN cl_attributes_value
            """,
            codelist=codelist
        )
        record = result.single()

        if record is None:
            create_initial_codelist_attributes_value(tx, effective_date, codelist, packages)
            create_initial_codelist_name(tx, codelist, codelist.get("name", None), 'Initial import from CDISC')
        else:
            value = record["cl_attributes_value"]

            if not (value.get("name", None) == codelist.get("name", None) and
                    value.get("submission_value", None) == codelist.get("submission_value", None) and
                    value.get("preferred_term", None) == codelist.get("preferred_term", None) and
                    value.get("definition", None) == codelist.get("definition", None) and
                    value.get("extensible", None) == codelist.get("extensible", None) and
                    are_lists_equal(value.get("synonyms", None), codelist.get("synonyms", None))
            ):
                create_new_version_codelist_attributes_value(tx, effective_date, codelist, packages)
            else:
                use_existing_codelist_attributes_value(tx, codelist, packages)

        merge_term_values(tx, codelist, effective_date, terms_data)


def create_initial_codelist_attributes_value(tx, effective_date_string, codelist, packages):
    tx.run(
        """
        MATCH (:CTCodelistRoot{uid: $codelist.concept_id})-[:HAS_ATTRIBUTES_ROOT]->(cl_attributes_root)
        CREATE (cl_attributes_value: CTCodelistAttributesValue)
        SET
            cl_attributes_value.name = $codelist.name,
            cl_attributes_value.submission_value = $codelist.submission_value,
            cl_attributes_value.preferred_term = $codelist.preferred_term,
            cl_attributes_value.definition = $codelist.definition,
            cl_attributes_value.extensible = coalesce(toBoolean($codelist.extensible), false),
            cl_attributes_value.synonyms = $codelist.synonyms
        CREATE (cl_attributes_root)-[:LATEST]->(cl_attributes_value)
        CREATE (cl_attributes_root)-[:LATEST_FINAL{
            start_date: datetime($effective_date_string),
            status: 'Final',
            version: '1.0',
            change_description: 'Imported from CDISC',
            user_initials: $user_initials
        }]->(cl_attributes_value)
        CREATE (cl_attributes_root)-[:HAS_VERSION{
            start_date: datetime($effective_date_string),
            status: 'Final',
            version: '1.0',
            change_description: 'Imported from CDISC',
            user_initials: $user_initials
        }]->(cl_attributes_value)

        WITH cl_attributes_value
        FOREACH (package IN $packages |
            MERGE (package_codelist:CTPackageCodelist{uid: package.name + "_" + $codelist.concept_id})
            CREATE (package_codelist)-[:CONTAINS_ATTRIBUTES]->(cl_attributes_value)
        )
        """,
        effective_date_string=effective_date_string,
        codelist=codelist,
        packages=packages,
        user_initials=USER_INITIALS
    )


def create_initial_codelist_name(tx, codelist, name, change_description):
    tx.run(
        """
        MATCH (codelist_root:CTCodelistRoot{uid: $codelist_uid})-[:HAS_NAME_ROOT]->(name_root)
        WHERE NOT (name_root)-[:LATEST]->()
        CREATE (name_root)-[:LATEST]->(name_value:CTCodelistNameValue)
        SET
            name_value.name = $name
        CREATE (name_root)-[:LATEST_FINAL{
            start_date: datetime(),
            status: 'Final',
            version: '1.0',
            change_description: $change_description,
            user_initials: $user_initials
        }]->(name_value)
        CREATE (name_root)-[:HAS_VERSION{
            start_date: datetime(),
            status: 'Final',
            version: '1.0',
            change_description: $change_description,
            user_initials: $user_initials
        }]->(name_value)
        """,
        codelist_uid=codelist['concept_id'],
        name=name,
        user_initials=USER_INITIALS,
        change_description=change_description
    ).consume()


def create_new_version_codelist_attributes_value(tx, effective_date_string, codelist, packages):
    tx.run(
        """
        MATCH (:CTCodelistRoot{uid: $codelist.concept_id})-[:HAS_ATTRIBUTES_ROOT]
            ->(cl_attributes_root)-[latest_final:LATEST_FINAL]->(cl_old_attributes_value)
            <-[latest:LATEST]-(cl_attributes_root)
        WITH cl_attributes_root, cl_old_attributes_value, latest, latest_final, latest_final.version AS version
        MATCH (cl_attributes_root)-[has_version:HAS_VERSION]->(cl_old_attributes_value)
        SET has_version.end_date = datetime($effective_date_string)
        DELETE latest, latest_final

        WITH cl_attributes_root, version LIMIT 1
        CREATE (cl_new_attributes_value:CTCodelistAttributesValue)
        SET
            cl_new_attributes_value.name = $codelist.name,
            cl_new_attributes_value.submission_value = $codelist.submission_value,
            cl_new_attributes_value.preferred_term = $codelist.preferred_term,
            cl_new_attributes_value.definition = $codelist.definition,
            cl_new_attributes_value.extensible = coalesce(toBoolean($codelist.extensible), false),
            cl_new_attributes_value.synonyms = $codelist.synonyms
        CREATE (cl_attributes_root)-[:LATEST_FINAL{
            start_date: datetime($effective_date_string),
            status: 'Final',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: 'Imported from CDISC',
            user_initials: $user_initials
        }]->(cl_new_attributes_value)
        CREATE (cl_attributes_root)-[:HAS_VERSION{
            start_date: datetime($effective_date_string),
            status: 'Final',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: 'Imported from CDISC',
            user_initials: $user_initials
        }]->(cl_new_attributes_value)
        CREATE (cl_attributes_root)-[:LATEST]->(cl_new_attributes_value)

        WITH cl_new_attributes_value
        FOREACH (package IN $packages |
            MERGE (package_codelist:CTPackageCodelist{uid: package.name + "_" + $codelist.concept_id})
            CREATE (package_codelist)-[:CONTAINS_ATTRIBUTES]->(cl_new_attributes_value)
        )
        """,
        effective_date_string=effective_date_string,
        codelist=codelist,
        packages=packages,
        user_initials=USER_INITIALS
    )


def use_existing_codelist_attributes_value(tx, codelist, packages):
    tx.run(
        """
        MATCH (:CTCodelistRoot{uid: $codelist.concept_id})-[:HAS_ATTRIBUTES_ROOT]->()-[:LATEST]->(cl_attributes_value)
        WITH cl_attributes_value
        UNWIND $packages AS package
            MATCH (package_codelist:CTPackageCodelist{uid: package.name + "_" + $codelist.concept_id})
            MERGE (package_codelist)-[:CONTAINS_ATTRIBUTES]->(cl_attributes_value)
        """,
        codelist=codelist,
        packages=packages
    )


def merge_term_values(tx, codelist, effective_date_string, terms_data):
    for term_data in terms_data:
        term = term_data.get('term', None)
        packages = term_data.get('packages', None)

        result = tx.run(
            """
            MATCH (:CTTermRoot{uid: $term.uid})-[:HAS_ATTRIBUTES_ROOT]->()-[:LATEST]->(t_attributes_value)
            RETURN t_attributes_value
            """,
            term=term
        )
        record = result.single()

        if record is None:
            create_initial_term_attributes_value(tx, effective_date_string, term, packages)
            create_initial_term_names(tx, term, sponsor_specific_parse_term_name(codelist, term), 'Initial import from CDISC')
        else:
            value = record["t_attributes_value"]

            if not (
                    value.get("code_submission_value", None) == term.get("code_submission_value", None) and
                    value.get("name_submission_value", None) == term.get("name_submission_value", None) and
                    value.get("preferred_term", None) == term.get("preferred_term", None) and
                    value.get("definition", None) == term.get("definition", None) and
                    are_lists_equal(value.get("synonyms", None), term.get("synonyms", None)) and
                    value.get("concept_id", None) == term.get("concept_id", None)
            ):
                create_new_version_term_attributes_value(tx, effective_date_string, term, packages)
            else:
                use_existing_term_attributes_value(tx, term, packages)

def create_initial_term_attributes_value(tx, effective_date_string, term, packages):
    tx.run(
        """
        MATCH (:CTTermRoot{uid: $term.uid})-[:HAS_ATTRIBUTES_ROOT]->(t_attributes_root)
        CREATE (t_attributes_value: CTTermAttributesValue)
        SET
            t_attributes_value.code_submission_value = $term.code_submission_value,
            t_attributes_value.name_submission_value = $term.name_submission_value,
            t_attributes_value.preferred_term = $term.preferred_term,
            t_attributes_value.definition = $term.definition,
            t_attributes_value.synonyms = $term.synonyms,
            t_attributes_value.concept_id = $term.concept_id
        CREATE (t_attributes_root)-[:LATEST]->(t_attributes_value)
        CREATE (t_attributes_root)-[:LATEST_FINAL{
            start_date: datetime($effective_date_string),
            status: 'Final',
            version: '1.0',
            change_description: 'Imported from CDISC',
            user_initials: $user_initials
        }]->(t_attributes_value)
        CREATE (t_attributes_root)-[:HAS_VERSION{
            start_date: datetime($effective_date_string),
            status: 'Final',
            version: '1.0',
            change_description: 'Imported from CDISC',
            user_initials: $user_initials
        }]->(t_attributes_value)

        WITH t_attributes_value
        FOREACH (package IN $packages |
            MERGE (package_term:CTPackageTerm{uid: package.name + "_" + $term.uid})
            CREATE (package_term)-[:CONTAINS_ATTRIBUTES]->(t_attributes_value)
        )
        """,
        effective_date_string=effective_date_string,
        term=term,
        packages=packages,
        user_initials=USER_INITIALS
    )


def create_initial_term_names(tx, term, name, change_description):
    tx.run(
        """
        MATCH (term_root:CTTermRoot{uid: $term_uid})-[:HAS_NAME_ROOT]->(name_root)
        WHERE NOT (name_root)-[:LATEST]->()
        CREATE (name_root)-[:LATEST]->(name_value:CTTermNameValue)
        SET
            name_value.name = $name,
            name_value.name_sentence_case = $name_sentence_case
        CREATE (name_root)-[:LATEST_FINAL{
            start_date: datetime(),
            status: 'Final',
            version: '1.0',
            change_description: $change_description,
            user_initials: $user_initials
        }]->(name_value)
        CREATE (name_root)-[:HAS_VERSION{
            start_date: datetime(),
            status: 'Final',
            version: '1.0',
            change_description: $change_description,
            user_initials: $user_initials
        }]->(name_value)
        """,
        term_uid=term['uid'],
        name=name,
        name_sentence_case=get_sentence_case_string(name),
        user_initials=USER_INITIALS,
        change_description=change_description
    ).consume()


def create_new_version_term_attributes_value(tx, effective_date_string, term, packages):
    tx.run(
        """
        MATCH (:CTTermRoot{uid: $term.uid})-[:HAS_ATTRIBUTES_ROOT]
            ->(t_attributes_root)-[latest_final:LATEST_FINAL]->(t_old_attributes_value)
            <-[latest:LATEST]-(t_attributes_root)
        WITH t_attributes_root, t_old_attributes_value, latest, latest_final, latest_final.version AS version
        MATCH (t_attributes_root)-[has_version:HAS_VERSION]->(t_old_attributes_value)
        SET has_version.end_date = datetime($effective_date_string)
        DELETE latest, latest_final

        WITH t_attributes_root, version LIMIT 1
        CREATE (t_new_attributes_value:CTTermAttributesValue)
        SET
            t_new_attributes_value.code_submission_value = $term.code_submission_value,
            t_new_attributes_value.name_submission_value = $term.name_submission_value,
            t_new_attributes_value.preferred_term = $term.preferred_term,
            t_new_attributes_value.definition = $term.definition,
            t_new_attributes_value.synonyms = $term.synonyms,
            t_new_attributes_value.concept_id = $term.concept_id
        CREATE (t_attributes_root)-[:LATEST_FINAL{
            start_date: datetime($effective_date_string),
            status: 'Final',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: 'Imported from CDISC',
            user_initials: $user_initials
        }]->(t_new_attributes_value)
        CREATE (t_attributes_root)-[:HAS_VERSION{
            start_date: datetime($effective_date_string),
            status: 'Final',
            version: toString(coalesce(toInteger(split(version, '.')[0]), 0) + 1) + '.0',
            change_description: 'Imported from CDISC',
            user_initials: $user_initials
        }]->(t_new_attributes_value)
        CREATE (t_attributes_root)-[:LATEST]->(t_new_attributes_value)

        WITH t_new_attributes_value
        FOREACH (package IN $packages |
            MERGE (package_term:CTPackageTerm{uid: package.name + "_" + $term.uid})
            CREATE (package_term)-[:CONTAINS_ATTRIBUTES]->(t_new_attributes_value)
        )
        """,
        effective_date_string=effective_date_string,
        term=term,
        packages=packages,
        user_initials=USER_INITIALS
    )


def use_existing_term_attributes_value(tx, term, packages):
    tx.run(
        """
        MATCH (:CTTermRoot{uid: $term.uid})-[:HAS_ATTRIBUTES_ROOT]->()-[:LATEST]->(t_attributes_value)
        WITH t_attributes_value
        UNWIND $packages AS package
            MATCH (package_term:CTPackageTerm{uid: package.name + "_" + $term.uid})
            MERGE (package_term)-[:CONTAINS_ATTRIBUTES]->(t_attributes_value)
        """,
        term=term,
        packages=packages
    )
    
def create_ct_stats_update_job(tx):
    codelists_stats_query = """
    CALL apoc.periodic.repeat("codelists_stats", "MATCH (pack:CTPackage)--(cat:CTCatalogue)
    WITH cat, pack
    ORDER BY pack.effective_date
    WITH cat, collect(pack) AS packages
    UNWIND range(0,size(packages)-2) AS i
    WITH cat, packages, packages[i] AS p1, packages[i+1] AS p2
    WITH p1, p2
    CALL
    {
        WITH p1, p2
        // Compute change counters
        MATCH (p1)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->(codelist_attr_val1:CTCodelistAttributesValue)<-[old_versions]-(:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(old_codelist_root)
        WITH old_codelist_root, codelist_attr_val1, max(old_versions.start_date) AS latest_date
        WITH collect(apoc.map.fromValues([old_codelist_root.uid, {
            value_node:codelist_attr_val1,
            change_date: latest_date}])) AS old_items
    
        MATCH (p2)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->(codelist_attr_val2:CTCodelistAttributesValue)<-[new_versions]-(:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(new_codelist_root)
        WITH old_items, new_codelist_root, codelist_attr_val2, max(new_versions.start_date) AS latest_date
        WITH old_items, collect(apoc.map.fromValues([new_codelist_root.uid, {
            value_node:codelist_attr_val2,
            change_date: latest_date}])) AS new_items
    
        // From pattern comprehensions we get list of maps, where each map represents data for specific codelist or term.
        // The following section merge list of maps coming from pattern comprehensions into one map.
        // The created maps store codelist uids or term uids as a keys and attributes values as a map values.
        WITH old_items, new_items,
            apoc.map.mergeList(old_items) AS old_items_map,
            apoc.map.mergeList(new_items) AS new_items_map
            
        // The following section creates arrays with codelist uids or terms uids 
        WITH old_items_map, new_items_map,
            keys(old_items_map) AS old_items_uids,
            keys(new_items_map) AS new_items_uids
    
        // In the following section the comparison of uid arrays is made to identify if given codelist or term:
        // was added, deleted, or is not moved in new package
        WITH old_items_map, new_items_map, old_items_uids, new_items_uids,
            apoc.coll.subtract(new_items_uids, old_items_uids) AS added_items,
            apoc.coll.subtract(old_items_uids, new_items_uids) AS deleted_items,
            apoc.coll.intersection(old_items_uids, new_items_uids) AS common_items
    
        // The following section unwinds list with uids of added items to filter out added items from the map that contains
        // all elements from new package
        WITH old_items_map, new_items_map, added_items, deleted_items, common_items
        
        UNWIND
        CASE WHEN added_items=[] THEN [NULL]
        ELSE added_items
        END AS added_item
    
        WITH old_items_map, new_items_map,
        CASE WHEN added_items <> [] THEN
        collect(apoc.map.merge(apoc.map.fromValues(['uid',added_item]), new_items_map[added_item])) 
        ELSE collect(added_item) 
        END AS added_items, 
        deleted_items, common_items
    
        // The following section unwinds list with uids of deleted items to filter out deleted items from the map that contains
        // all elements from old package
        UNWIND 
        CASE WHEN deleted_items=[] THEN [NULL]
        ELSE deleted_items
        END as deleted_item
    
        WITH old_items_map, new_items_map, added_items, 
        CASE WHEN deleted_items <> [] THEN 
            collect(apoc.map.merge(apoc.map.fromValues(['uid', deleted_item]), old_items_map[deleted_item]))
            ELSE collect(deleted_item) END 
        AS deleted_items, 
        common_items
    
        // The following section unwinds list with uids of items that are present in old package and new package
        // to filter out common items from the map that contains all elements from new package.
        UNWIND 
        CASE WHEN common_items=[] THEN [NULL]
            ELSE common_items
            END
        AS common_item
    
        // The following section makes the comparison of nodes that are present in both packages
        WITH old_items_map, new_items_map, added_items, deleted_items, common_items, common_item,
        CASE WHEN old_items_map[common_item] <> new_items_map[common_item] THEN
        apoc.map.fromValues([
            'uid', common_item, 
            'value_node', apoc.diff.nodes(old_items_map[common_item].value_node, new_items_map[common_item].value_node),
            'change_date', new_items_map[common_item].change_date,
            'is_change_of_codelist', true
            ])
        END AS diff
    
        WITH collect(diff) as items_diffs, added_items, deleted_items
        WITH size(added_items) as added, size(deleted_items) as deleted, size(items_diffs) as updated
        RETURN added, deleted, updated
    }
    
    MERGE (p1)-[rel:NEXT_PACKAGE]->(p2)
    SET rel.added_codelists=added, rel.deleted_codelists=deleted, rel.updated_codelists=updated
    RETURN p1, p2, added, deleted, updated", 86400)
    """
    
    terms_stats_query = """
    CALL apoc.periodic.repeat("terms_stats", "CALL apoc.periodic.iterate('
    MATCH (pack:CTPackage)--(cat:CTCatalogue)
    WITH cat, pack
    ORDER BY pack.effective_date
    WITH cat, collect(pack) AS packages
    RETURN cat, packages',
    '
    UNWIND range(0,size(packages)-2) AS i
    WITH cat, packages, packages[i] AS p1, packages[i+1] AS p2
    WITH p1, p2
    CALL
    {
        WITH p1, p2
        // Compute change counters
        MATCH (p1)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_TERM]->(:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(term_attr_val1)<-[old_versions]-(:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(old_term_root)
        WITH old_term_root,
            [(codelist_root)-[:HAS_TERM]->(old_term_root) | codelist_root.uid] AS codelists,
            term_attr_val1,
            max(old_versions.start_date) AS latest_date
            
        WITH collect(apoc.map.fromValues([old_term_root.uid, {
            value_node:term_attr_val1,
            codelists: codelists,
            change_date: latest_date}])) AS old_items
    
        MATCH (p2)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_TERM]->(:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(term_attr_val2)<-[new_versions]-(:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(new_term_root)
        WITH old_items,
            new_term_root,
            [(codelist_root)-[:HAS_TERM]->(new_term_root) | codelist_root.uid] AS codelists,
            term_attr_val2,
            max(new_versions.start_date) AS latest_date
    
        WITH old_items, collect(apoc.map.fromValues([new_term_root.uid, {
            value_node: term_attr_val2,
            codelists: codelists,
            change_date: latest_date}])) AS new_items
    
        // From pattern comprehensions we get list of maps, where each map represents data for specific codelist or term.
        // The following section merge list of maps coming from pattern comprehensions into one map.
        // The created maps store codelist uids or term uids as a keys and attributes values as a map values.
        WITH old_items, new_items,
            apoc.map.mergeList(old_items) AS old_items_map,
            apoc.map.mergeList(new_items) AS new_items_map
    
        // The following section creates arrays with codelist uids or terms uids
        WITH old_items_map, new_items_map,
            keys(old_items_map) AS old_items_uids,
            keys(new_items_map) AS new_items_uids
    
        // In the following section the comparison of uid arrays is made to identify if given codelist or term:
        // was added, deleted, or is not moved in new package
        WITH old_items_map, new_items_map, old_items_uids, new_items_uids,
            apoc.coll.subtract(new_items_uids, old_items_uids) AS added_items,
            apoc.coll.subtract(old_items_uids, new_items_uids) AS removed_items,
            apoc.coll.intersection(old_items_uids, new_items_uids) AS common_items
    
        // The following section unwinds list with uids of added items to filter out added items from the map that contains
        // all elements from new package
        WITH old_items_map, new_items_map, added_items, removed_items, common_items
        UNWIND
        CASE WHEN added_items=[] THEN [NULL]
        ELSE added_items
        END AS added_item
        
        WITH old_items_map, new_items_map,
        CASE WHEN added_items <> [] THEN
        collect(apoc.map.merge(apoc.map.fromValues([\\"uid\\",added_item]), new_items_map[added_item]))
        ELSE collect(added_item)
        END AS added_items,
        removed_items, common_items
    
        // The following section unwinds list with uids of removed items to filter out removed items from the map that contains
        // all elements from old package
        UNWIND
        CASE WHEN removed_items=[] THEN [NULL]
        ELSE removed_items
        END as removed_item
    
        WITH old_items_map, new_items_map, added_items,
        CASE WHEN removed_items <> [] THEN
            collect(apoc.map.merge(apoc.map.fromValues([\\"uid\\", removed_item]), old_items_map[removed_item]))
            ELSE collect(removed_item) END
        AS removed_items,
        common_items
    
        // The following section unwinds list with uids of items that are present in old package and new package
        // to filter out common items from the map that contains all elements from new package.
        UNWIND
        CASE WHEN common_items=[] THEN [NULL]
            ELSE common_items
            END
        AS common_item
    
        // The following section makes the comparison of nodes that are present in both packages
        WITH old_items_map, new_items_map, added_items, removed_items, common_items, common_item,
        CASE WHEN old_items_map[common_item] <> new_items_map[common_item] THEN
        apoc.map.fromValues([
            \\"uid\\", common_item,
            \\"value_node\\", apoc.diff.nodes(old_items_map[common_item].value_node, new_items_map[common_item].value_node),
            \\"change_date\\", new_items_map[common_item].change_date,
            \\"codelists\\", new_items_map[common_item].codelists
            ])
        END AS diff
    
        WITH collect(diff) as items_diffs, added_items, removed_items
    
        WITH size(added_items) as added, size(removed_items) as deleted, size(items_diffs) as updated
    
        RETURN added, deleted, updated
    }
    
    MERGE (p1)-[rel:NEXT_PACKAGE]->(p2)
    SET rel.added_terms=added, rel.deleted_terms=deleted, rel.updated_terms=updated, rel.last_refresh=datetime()
    ',
    {batchSize:1})", 86400)
    """
    
    tx.run("CALL apoc.periodic.cancel('codelists_stats')")
    tx.run("CALL apoc.periodic.cancel('terms_stats')")
    tx.run(codelists_stats_query)
    tx.run(terms_stats_query)

##########################################################################
# Update this part of the code to apply sponsor-specific transformations #
##########################################################################
def sponsor_specific_parse_term_name(codelist, term):
    """Sponsor specific parsing of term name

    Args:
        codelist (dict): Codelist data
        term (dict): Term data

    Returns:
        str: Parsed term name - including sponsor specific transformations
    """
    newname = term['preferred_term']
    # Clean by removing any trailing space or newline
    newname = newname.strip(" \n")

    if codelist["concept_id"] == "C99077":
        # Study type codelist

        # Remove "Study" from end
        newname =  re.sub(r' Study$', '', newname)

    elif codelist["concept_id"] == "C66736":
        # Trial type codelist

        # Remove "Study" or "Trial" from end
        newname =  re.sub(r' (Study|Trial)$', '', newname)

    elif codelist["concept_id"] == "C66785":
        # Control type codelist

        # Remove "Control" from end
        newname =  re.sub(r' Control$', '', newname)

    elif codelist["concept_id"] == "C66735":
        # Trial Blinding Schema codelist

        # Remove "Study" from end
        newname =  re.sub(r' Study$', '', newname)

    elif codelist["concept_id"] == "C99076":
        # Intervention Model Response codelist

        # Remove "Study" from end
        newname =  re.sub(r' Study$', '', newname)

    elif codelist["concept_id"] in ("C66729", "C78420", "C78425"):
        # Main codelist:
        # - Route of Administration, C66729
        # Subsets:
        # - Concomitant Medication Route of Administration, C78420
        # - Exposure Route of Administration, C78425

        # Remove "Route of Administration" at start or end.
        # When at the end, allow both a space and a dash in front.
        newname = re.sub(r'((\s|-)Route of Administration$|^Route of Administration )', '', newname)

        # If starting with "Administration via" then we use the code submission value
        if newname.startswith("Administration via"):
            newname = term['code_submission_value'].title()

    elif codelist["concept_id"] in ("C66726", "C78418", "C78426"):
        # Main codelist:
        # - Pharmaceutical Dosage Form, C66726
        # Subsets
        # - Concomitant Medication Dose Form, C78418
        # - Exposure Dose Form, C78426

        # Remove "Dosage Form" at start or end or middle
        newname =  re.sub(r'^Dosage Form for', 'For', newname)
        newname =  re.sub(r'(\sDosage Form($|(?=\s))|^Dosage Form\s)', '', newname)

    elif codelist["concept_id"] in ("C71620", "C78417", "C78422", "C78428", "C78427", "C78429", "C78421", "C78423", "C78430"):
        # Main codelist:
        # - Unit, C71620
        # Subsets:
        # - Concomitant Medication Dose Units, C78417
        # - ECG Original Units, C78422
        # - Total Volume Administration Unit, C78428
        # - Unit for the Duration of Treatment Interruption, C78427
        # - Unit of Measure for Flow Rate, C78429
        # - Unit of Drug Dispensed or Returned, C78421
        # - Units for Exposure, C78423
        # - Units for Planned Exposure, C78430

        # Use code submission value as name
        newname = term["code_submission_value"]

    elif codelist["concept_id"] in ("C71113", "C78419", "C78745"):
        # Main codelist:
        # - Frequency, C71113
        # Subsets:
        # - Concomitant Medication Dosing Frequency per Interval, C78419
        # - Exposure Dosing Frequency per Interval, C78745

        # Clean by removing any trailing period
        # Seen (so far) only for C139178: "Every Night." in sdtmct json-files from before 2019-09-27.
        newname = newname.strip(".")

        # Special cases
        if newname == "Infrequent":
            newname = "Occasional"
        if newname == "Every Evening" and term["code_submission_value"] == "QPM":
            newname = "Every Day"

        # Replace "Per Day/Month" with "Daily/Monthly"
        newname =  re.sub(r' Per Day$', ' Daily', newname)
        newname =  re.sub(r' Per Month$', ' Monthly', newname)

    # Print changes as codelist;oldname;newname (easy to copy-paste into excel)
    #if newname != term['preferred_term']:
    #    print(f"{codelist['concept_id']};{term['preferred_term']};{newname}")

    return newname


def import_from_cdisc_ct_db_into_mdr(effective_date, cdisc_ct_neo4j_driver, cdisc_ct_db_name, mdr_neo4j_driver,
                                      mdr_db_name, user_initials):
    global USER_INITIALS
    USER_INITIALS = user_initials

    start_time = time.time()

    if effective_date is None:
        print(f"WARNING: No effective date specified. Not importing anything.")
        return

    with cdisc_ct_neo4j_driver.session(database=cdisc_ct_db_name) as session:
        with session.begin_transaction() as tx:
            print_ignored_stats(tx, effective_date)
            tx.commit()

        # read from the CDISC CT DB
        packages_data = session.read_transaction(get_packages, effective_date)
        codelists_data = session.read_transaction(get_codelists, effective_date)

        session.close()

    with mdr_neo4j_driver.session(database=mdr_db_name) as session:
        # write to the clinical MDR db

        print(f"==  * Retiring codelists.")
        # session.write_transaction(retire_codelists, packages_data)

        print(f"==  * Merging structure nodes and relationships.")
        session.write_transaction(merge_structure_nodes_and_relationships, packages_data, codelists_data, effective_date)

        print(f"==  * Updating HAS_TERM and HAD_TERM relationships.")
        session.write_transaction(update_has_term_and_had_term_relationships, codelists_data, effective_date)

        print(f"==  * Updating attributes.")
        session.write_transaction(update_attributes, codelists_data, effective_date)
         
        print(f"==  * Creating CT stats update job.")
        session.write_transaction(create_ct_stats_update_job)    

        session.close()
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"== Duration: {round(elapsed_time, 1)} seconds")
    print(f"============================================")