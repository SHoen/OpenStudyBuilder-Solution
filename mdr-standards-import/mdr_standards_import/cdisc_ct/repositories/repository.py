from mdr_standards_import.cdisc_ct.entities.codelist import Codelist
from mdr_standards_import.cdisc_ct.entities.ct_import import CTImport
from mdr_standards_import.cdisc_ct.entities.inconsistency import Inconsistency
from mdr_standards_import.cdisc_ct.entities.package import Package
from mdr_standards_import.cdisc_ct.exceptions.effective_date_exists import EffectiveDateExists
from mdr_standards_import.cdisc_ct.repositories.mapping import map_codelists, map_inconsistent_codelist_attributes, map_inconsistent_term_attributes, map_term_submission_value, map_packages, map_terms
from mdr_standards_import.cdisc_ct.entities.term import Term


def create_indexes_if_not_existent(tx):
    for querystring in [
        "CREATE INDEX index_codelist_concept_id IF NOT EXISTS FOR (n:Codelist) ON (n.concept_id)",
        "CREATE INDEX index_term_concept_id IF NOT EXISTS FOR (n:Term) ON (n.concept_id)",
        "CREATE CONSTRAINT constraint_import_effective_date IF NOT EXISTS ON (n:Import) ASSERT (n.effective_date) IS NODE KEY",
        "CREATE CONSTRAINT constraint_package_uid IF NOT EXISTS ON (n:Package) ASSERT (n.name) IS NODE KEY",
        "CREATE CONSTRAINT constraint_codelist_uid IF NOT EXISTS ON (n:Codelist) ASSERT (n.effective_date, n.concept_id) IS NODE KEY",
        "CREATE CONSTRAINT constraint_term_uid IF NOT EXISTS ON (n:Term) ASSERT (n.effective_date, n.concept_id, n.code_submission_value) IS NODE KEY",
    ]:
        tx.run(querystring)


def await_indexes(tx):
    tx.run("CALL db.awaitIndexes(5000)")


def create_import_node(tx, ct_import: CTImport):
    """
    Creates the `Import` node for the specified <effective_date> if it doesn't exist.

    Returns the internal Neo4j id of the created node on success.
    Returns False if the node was not created. Reasons might include: the node was already existent, db error.
    """

    if _does_import_node_exists(tx, ct_import):
        raise EffectiveDateExists

    result = tx.run(
        """
        CREATE (import:Import{
            effective_date: date($effective_date),
            user_initials: $user_initials
        })
        SET
            import:Running,
            import.import_date_time = datetime($import_date_time)
        RETURN id(import) AS import_id
        """,
        effective_date=ct_import.effective_date,
        user_initials=ct_import.user_initials,
        import_date_time=ct_import.import_date_time
    ).single()

    import_id = result.get("import_id", None)
    if import_id is None:
        raise Exception
    return import_id


def _does_import_node_exists(tx, ct_import: CTImport):
    result = tx.run(
        """
        MATCH (import:Import{effective_date: date($effective_date)})
        WITH import LIMIT 1
        RETURN count(import) = 1 AS does_import_exist
        """,
        effective_date=ct_import.effective_date,
    ).single()

    return result is not None and result['does_import_exist'] == True


def create_ct_import(ct_import: CTImport, session):
    effective_date = ct_import.effective_date

    packages_data = map_packages(
        ct_import.get_packages(), ct_import.effective_date)

    codelists_data = map_codelists(
        ct_import.get_codelists(), ct_import.effective_date)
    terms_data = map_terms(ct_import.get_terms(), ct_import.effective_date)

    with session.begin_transaction() as tx:
        _create_packages(tx, effective_date, packages_data)
        _create_codelists(tx, effective_date, codelists_data)
        tx.commit()

    with session.begin_transaction() as tx:
        _create_terms(tx, effective_date, terms_data)
        tx.commit()

    with session.begin_transaction() as tx:
        _create_package_contains_codelist(tx, effective_date, packages_data)
        _create_codelist_contains_term(tx, effective_date, codelists_data)
        _create_package_contains_term(tx, effective_date, packages_data)
        tx.commit()

    with session.begin_transaction() as tx:
        _create_inconsistent_attributes_for_codelists(
            tx, ct_import.get_codelists(), effective_date)
        _create_inconsistent_attributes_and_submission_values_for_terms(
            tx, ct_import.get_terms(), effective_date)

    with session.begin_transaction() as tx:
        for inconsistency in ct_import.get_inconsistencies():
            _create_inconsistency(tx, inconsistency, effective_date)
        tx.commit()


def _create_packages(tx, effective_date, packages_data):
    tx.run(
        """
        MATCH (import:Import{effective_date: date($effective_date)})
        UNWIND $packages AS p
            CREATE (package:Package{
                name: p.name
            })
            SET
                package.catalogue_name = p.catalogue_name,
                package.registration_status = p.registration_status,
                package.label = p.label,
                package.description = p.description,
                package.source = p.source,
                package.href = p.href
            CREATE (import)-[:INCLUDES]->(package)
        """,
        effective_date=effective_date,
        packages=packages_data
    )


def _create_codelists(tx, effective_date, codelists_data):
    tx.run(
        """
        UNWIND $codelists AS c
            CREATE (codelist:Codelist{
                effective_date: date($effective_date),
                concept_id: c.concept_id
            })
            SET 
                codelist.name = c.name,
                codelist.submission_value = c.submission_value,
                codelist.preferred_term = c.preferred_term,
                codelist.definition = c.definition,
                codelist.extensible = c.extensible,
                codelist.synonyms = c.synonyms
        """,
        codelists=codelists_data,
        effective_date=effective_date
    )


def _create_inconsistent_attributes_for_codelists(tx, codelists: 'list[Codelist]', effective_date: str):
    for codelist in codelists:
        if not codelist.has_consistent_attributes():
            for attributes in codelist.get_inconsistent_attributes_set():
                tx.run(
                    """
                    MATCH (codelist:Codelist{effective_date:date($effective_date), concept_id: $concept_id})
                    CREATE (codelist)-[:HAS]->(ia:InconsistentAttributes)
                    SET
                        ia.name = $attributes_data.name,
                        ia.submission_value = $attributes_data.submission_value,
                        ia.preferred_term = $attributes_data.preferred_term,
                        ia.definition = $attributes_data.definition,
                        ia.extensible = $attributes_data.extensible,
                        ia.synonyms = $attributes_data.synonyms
                    WITH ia
                    MATCH (package:Package) WHERE package.name IN $attributes_data.package_names
                    CREATE (ia)-[:ARE_DEFINED_IN]->(package)
                    """,
                    effective_date=effective_date,
                    concept_id=codelist.concept_id,
                    attributes_data=map_inconsistent_codelist_attributes(
                        attributes)
                )


def _create_inconsistent_attributes_and_submission_values_for_terms(tx, terms: 'list[Term]', effective_date: str):
    for term in terms:
        if not term.has_consistent_attributes():
            _create_inconsistent_attributes_for_term(tx, term, effective_date)
        if not term.has_consistent_submission_values():
            _create_inconsistent_submission_values_for_term(
                tx, term, effective_date)


def _create_inconsistent_attributes_for_term(tx, term: Term, effective_date: str):
    for attributes in term.get_inconsistent_attributes_set():
        attributes_data = map_inconsistent_term_attributes(attributes)
        result = tx.run(
            """
            MATCH (term:Term{
                effective_date: date($effective_date),
                concept_id: $concept_id,
                code_submission_value: $code_submission_value
            })
            CREATE (term)-[:HAS]->(ia:InconsistentAttributes)
            SET
                ia.name_submission_value = $attributes_data.name_submission_value,
                ia.preferred_term = $attributes_data.preferred_term,
                ia.definition = $attributes_data.definition,
                ia.synonyms = $attributes_data.synonyms
            RETURN id(ia) AS inconsistent_attributes_id
            """,
            effective_date=effective_date,
            concept_id=term.concept_id,
            code_submission_value=term.code_submission_value,
            attributes_data=attributes_data
        ).single()
        inconsistent_attributes_id = result.get(
            'inconsistent_attributes_id')

        tx.run(
            """
            MATCH (ia) WHERE id(ia) = $inconsistent_attributes_id
            MATCH (codelist:Codelist) WHERE codelist.concept_id IN $codelist_concept_ids
            CREATE (ia)-[:ARE_DEFINED_IN]->(codelist)
            """,
            inconsistent_attributes_id=inconsistent_attributes_id,
            codelist_concept_ids=attributes_data.get(
                'codelist_concept_ids', [])
        )

        tx.run(
            """
            MATCH (ia) WHERE id(ia) = $inconsistent_attributes_id
            MATCH (package:Package) WHERE package.name IN $package_names
            CREATE (ia)-[:ARE_DEFINED_IN]->(package)
            """,
            inconsistent_attributes_id=inconsistent_attributes_id,
            package_names=attributes_data.get('package_names', [])
        )


def _create_inconsistent_submission_values_for_term(tx, term: Term, effective_date: str):
    for tsv in term.get_term_submission_values():
        sv_data = map_term_submission_value(tsv)
        result = tx.run(
            """
            MATCH (term:Term{
                effective_date: date($effective_date),
                concept_id: $concept_id,
                code_submission_value: $code_submission_value
            })
            CREATE (term)-[:HAS]->(sv:InconsistentSubmissionValue)
            SET
                sv.submission_value = $sv_data.submission_value   
            RETURN id(sv) AS sv_id
            """,
            effective_date=effective_date,
            concept_id=term.concept_id,
            code_submission_value=term.code_submission_value,
            sv_data=sv_data
        ).single()
        sv_id = result.get('sv_id')

        tx.run(
            """
            MATCH (sv) WHERE id(sv) = $sv_id
            MATCH (codelist:Codelist) WHERE codelist.concept_id IN $codelist_concept_ids
            CREATE (sv)-[:IS_DEFINED_IN]->(codelist)
            """,
            sv_id=sv_id,
            codelist_concept_ids=sv_data.get('codelist_concept_ids', [])
        )

        tx.run(
            """
            MATCH (sv) WHERE id(sv) = $sv_id
            MATCH (package:Package) WHERE package.name IN $package_names
            CREATE (sv)-[:IS_DEFINED_IN_PACKAGE]->(package)
            """,
            sv_id=sv_id,
            package_names=sv_data.get('package_names', [])
        )


def _create_terms(tx, effective_date, terms_data):
    tx.run(
        """
        UNWIND $terms AS t
            CREATE (term:Term{
                effective_date: date($effective_date),
                concept_id: t.concept_id,
                code_submission_value: t.code_submission_value
            })
            SET
                term.name_submission_value = t.name_submission_value,
                term.preferred_term = t.preferred_term,
                term.definition = t.definition,
                term.synonyms = t.synonyms
        """,
        terms=terms_data,
        effective_date=effective_date
    )


def _create_package_contains_codelist(tx, effective_date, packages_data):
    tx.run(
        """
        UNWIND $packages AS p
            MATCH (package:Package{name: p.name})
            UNWIND p.codelists AS c
                MATCH (codelist:Codelist{effective_date:date($effective_date), concept_id: c.concept_id})
                CREATE (package)-[contains:CONTAINS]->(codelist)
                SET contains.inconsistent_term_concept_ids=c.inconsistent_term_concept_ids
        """,
        packages=packages_data,
        effective_date=effective_date
    )


def _create_package_contains_term(tx, effective_date, packages_data):
    tx.run(
        """
        UNWIND $packages AS p
            MATCH (package:Package{name: p.name})
            UNWIND p.terms AS t
                MATCH (term:Term{
                    effective_date:date($effective_date),
                    concept_id: t.concept_id,
                    code_submission_value: t.code_submission_value
                })
                CREATE (package)-[:CONTAINS_TERM]->(term)
        """,
        packages=packages_data,
        effective_date=effective_date
    )


def _create_codelist_contains_term(tx, effective_date, codelists_data):
    tx.run(
        """
        UNWIND $codelists AS c
            MATCH (codelist:Codelist{effective_date: date($effective_date), concept_id: c.concept_id})
            UNWIND c.terms AS t
                MATCH (term:Term{effective_date: date($effective_date), concept_id: t.concept_id, code_submission_value: t.code_submission_value})
                CREATE (codelist)-[:CONTAINS]->(term)
        """,
        codelists=codelists_data,
        effective_date=effective_date
    )


def _create_inconsistency(tx, inconsistency: Inconsistency, effective_date):
    label = 'ResolvedInconsistency' if inconsistency.is_resolved() else 'Inconsistency'

    result = tx.run(
        """
        MATCH (import:Import{effective_date: date($effective_date)})
        CREATE (import)-[:HAS]->(log:""" + label + """)
        SET
            log.date_time = datetime($date),
            log.tagline = $tagline,
            log.message = $message,
            log.comment = $comment,
            log.user_initials = $user_initials
        RETURN id(log) AS inconsistency_id
        """,
        effective_date=effective_date,
        date=inconsistency.date_time,
        tagline=inconsistency.tagline,
        message=inconsistency.message,
        comment=inconsistency.comment,
        user_initials=inconsistency.user_initials
    ).single()
    inconsistency_id = result.get('inconsistency_id')
    if inconsistency.affected_package is not None:
        _create_affects_package(
            inconsistency_id, inconsistency.affected_package, tx)
    if inconsistency.affected_codelist is not None:
        _create_affects_codelist(
            inconsistency_id, inconsistency.affected_codelist, effective_date, tx)
    if inconsistency.affected_term is not None:
        _create_affects_term(
            inconsistency_id, inconsistency.affected_term, effective_date, tx)


def _create_affects_package(inconsistency_id: int, package: Package, tx):
    tx.run(
        """
        MATCH (log) WHERE id(log) = $inconsistency_id
        MATCH (package:Package{name: $package_name})
        CREATE (log)-[:AFFECTS_PACKAGE]->(package)
        """,
        inconsistency_id=inconsistency_id,
        package_name=package.name
    )


def _create_affects_codelist(inconsistency_id: int, codelist: Codelist, effective_date: str, tx):
    tx.run(
        """
        MATCH (log) WHERE id(log) = $inconsistency_id
        MATCH (codelist:Codelist{effective_date:date($effective_date), concept_id: $codelist_concept_id})
        CREATE (log)-[:AFFECTS_CODELIST]->(codelist)
        """,
        inconsistency_id=inconsistency_id,
        effective_date=effective_date,
        codelist_concept_id=codelist.concept_id
    )


def _create_affects_term(inconsistency_id: int, term: Term, effective_date: str, tx):
    tx.run(
        """
        MATCH (log) WHERE id(log) = $inconsistency_id
        MATCH (term:Term{
            effective_date:date($effective_date),
            concept_id: $term_concept_id,
            code_submission_value: $code_submission_value
            })
        CREATE (log)-[:AFFECTS_TERM]->(term)
        """,
        inconsistency_id=inconsistency_id,
        effective_date=effective_date,
        code_submission_value=term.code_submission_value,
        term_concept_id=term.concept_id
    )
