from mdr_standards_import.cdisc_ct.entities.package import Package
from mdr_standards_import.cdisc_ct.entities.term import Term
from mdr_standards_import.cdisc_ct.entities.codelist import Codelist
from mdr_standards_import.cdisc_ct.entities.term_submission_value import TermSubmissionValue


def map_packages(packages: 'list[Package]', effective_date):
    packages_data = []
    for package in packages:
        packages_data.append({
            'effective_date': effective_date,
            'name': package.name,
            'catalogue_name': package.catalogue_name,
            'registration_status': package.registration_status,
            'label': package.label,
            'description': package.description,
            'source': package.source,
            'href': package.href,

            'codelists': map_codelists_of_package(package),
            'terms': tmap(package.get_terms())
        })
    return packages_data


def pmap(packages):
    data = []
    for package in packages:
        if package is None:
            continue
        data.append({
            'name': package.name,
        })
    return data


def map_codelists_of_package(package: Package):
    data = []
    for codelist in package.get_codelists():
        if codelist is None:
            continue
        itcids = package.get_term_concept_ids_for_codelist(
            codelist) if codelist.has_inconsistent_terms() else None
        data.append({
            'concept_id': codelist.concept_id,
            'inconsistent_term_concept_ids': itcids
        })
    return data


def map_codelists(codelists: 'list[Codelist]', effective_date):
    codelists_data = []
    for codelist in codelists:
        attributes = codelist.get_attributes()
        codelists_data.append({
            'effective_date': effective_date,
            'concept_id': codelist.concept_id,
            'name': attributes.name,
            'submission_value': attributes.submission_value,
            'preferred_term': attributes.preferred_term,
            'definition': attributes.definition,
            'extensible': attributes.extensible,
            'synonyms': attributes.synonyms,

            'terms': tmap(codelist.get_terms())
        })
    return codelists_data


def map_inconsistent_codelist_attributes(attributes):
    return {
        'name': attributes.name,
        'submission_value': attributes.submission_value,
        'preferred_term': attributes.preferred_term,
        'definition': attributes.definition,
        'extensible': attributes.extensible,
        'synonyms': attributes.synonyms,

        'package_names': [package.name for package in attributes.get_packages()]
    }


def map_inconsistent_term_attributes(attributes):
    return {
        'name_submission_value': attributes.name_submission_value,
        'preferred_term': attributes.preferred_term,
        'definition': attributes.definition,
        'synonyms': attributes.synonyms,

        'codelist_concept_ids': [codelist.concept_id for codelist in attributes.get_codelists()],
        'package_names': [package.name for package in attributes.get_packages()]
    }


def map_term_submission_value(tsv: TermSubmissionValue):
    return {
        'submission_value': tsv.get_value(),
        'codelist_concept_ids': [codelist.concept_id for codelist in tsv.get_codelists()],
        'package_names': [package.name for package in tsv.get_packages()]
    }


def tmap(terms):
    data = []
    for term in terms:
        if term is None:
            continue
        data.append({
            'concept_id': term.concept_id,
            'code_submission_value': term.code_submission_value
        })
    return data


def map_terms(terms: 'list[Term]', effective_date):
    terms_data = []
    for term in terms:
        attributes = term.get_attributes()
        terms_data.append({
            'effective_date': effective_date,
            'concept_id': term.concept_id,
            'code_submission_value': term.code_submission_value,
            'name_submission_value': attributes.name_submission_value,
            'preferred_term': attributes.preferred_term,
            'definition': attributes.definition,
            'synonyms': attributes.synonyms,
        })
    return terms_data
