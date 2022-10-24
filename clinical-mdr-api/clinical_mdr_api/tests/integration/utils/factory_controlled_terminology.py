from clinical_mdr_api.domain.controlled_terminology.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.domain.controlled_terminology.ct_codelist_name import (
    CTCodelistNameAR,
    CTCodelistNameVO,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import (
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_codelist_name_repository import (
    CTCodelistNameRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_term_attributes_repository import (
    CTTermAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_term_name_repository import (
    CTTermNameRepository,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.ct_codelist_attributes import CTCodelistAttributesService
from clinical_mdr_api.services.ct_codelist_name import CTCodelistNameService
from clinical_mdr_api.services.ct_term_attributes import CTTermAttributesService
from clinical_mdr_api.services.ct_term_name import CTTermNameService
from clinical_mdr_api.tests.unit.domain.controlled_terminology_aggregates.test_ct_codelist_attributes import (
    create_random_ct_codelist_attributes_vo,
)


def get_catalogue_name_library_name():
    catalogue_name = "catalogue"
    library_name = "Sponsor"
    return catalogue_name, library_name


def create_codelist(name, uid, catalogue, library):
    ct_codelist_attributes_ar = CTCodelistAttributesAR.from_input_values(
        generate_uid_callback=lambda: uid,
        ct_codelist_attributes_vo=create_random_ct_codelist_attributes_vo(
            catalogue=catalogue
        ),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=True
        ),
        author="TODO Initials",
    )
    CTCodelistAttributesRepository().save(ct_codelist_attributes_ar)
    item = CTCodelistAttributesService().approve(uid)
    ct_codelist_name_vo = CTCodelistNameVO.from_repository_values(
        catalogue_name=catalogue, name=name, is_template_parameter=False
    )
    ct_codelist: CTCodelistNameAR = CTCodelistNameAR.from_input_values(
        generate_uid_callback=lambda: ct_codelist_attributes_ar.uid,
        ct_codelist_name_vo=ct_codelist_name_vo,
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=True
        ),
        author="TODO",
    )
    CTCodelistNameRepository().save(ct_codelist)
    item = CTCodelistNameService().approve(uid)
    return item


def create_ct_term(
    codelist,
    name: str,
    uid: str,
    order,
    catalogue_name,
    library_name,
    code_submission_value="test",
    name_submission_value="test",
    preferred_term="test",
    definition="123",
):
    library = LibraryVO.from_repository_values(
        library_name=library_name, is_editable=True
    )
    ct_term_attributes_ar = CTTermAttributesAR.from_input_values(
        author="TOOD",
        ct_term_attributes_vo=CTTermAttributesVO.from_input_values(
            codelist_uid=codelist,
            catalogue_name=catalogue_name,
            code_submission_value=code_submission_value,
            name_submission_value=name_submission_value,
            preferred_term=preferred_term,
            definition=definition,
            codelist_exists_callback=lambda s: True,
            catalogue_exists_callback=lambda s: True,
            term_exists_by_name_callback=lambda s: False,
            term_exists_by_code_submission_value_callback=lambda s: False,
        ),
        library=library,
        generate_uid_callback=lambda: uid,
    )

    CTTermAttributesRepository().save(ct_term_attributes_ar)

    CTTermAttributesService().approve(uid)
    term_vo = CTTermNameVO.from_repository_values(
        codelist_uid=codelist,
        catalogue_name=catalogue_name,
        name=name,
        name_sentence_case=name.capitalize(),
        order=order,
    )
    ct_term = CTTermNameAR.from_input_values(
        generate_uid_callback=lambda: uid,
        ct_term_name_vo=term_vo,
        library=library,
        author="TODO Initials",
    )
    CTTermNameRepository().save(ct_term)
    CTTermNameService().approve(uid)
    return ct_term


def get_unit_uid_by_name(unit_name):
    unit_uid = MetaRepository().unit_definition_repository.find_uid_by_name(unit_name)
    return unit_uid
