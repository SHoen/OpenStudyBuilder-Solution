from typing import Any, Optional, Sequence

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json, List

from clinical_mdr_api.models import (
    OdmForm,
    OdmFormActivityGroupPostInput,
    OdmFormItemGroupPostInput,
    OdmFormPatchInput,
    OdmFormPostInput,
    OdmFormWithRelationsPatchInput,
    OdmFormWithRelationsPostInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.odm_common_models import OdmXmlExtensionRelationPostInput
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.odm_forms import OdmFormService

router = APIRouter()

# Argument definitions
OdmFormUID = Path(None, description="The unique id of the ODM Form.")


@router.get(
    "",
    summary="Return every variable related to the selected status and version of the ODM Forms",
    description="",
    response_model=CustomPage[OdmForm],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_all_odm_forms(
    library: Optional[str] = Query(None),
    sortBy: Json = Query(None, description=_generic_descriptions.SORT_BY),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
):
    odm_form_service = OdmFormService()
    results = odm_form_service.get_all_concepts(
        library=library,
        sort_by=sortBy,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )
    return CustomPage.create(
        items=results.items, total=results.total_count, page=pageNumber, size=pageSize
    )


@router.get(
    "/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=List[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_values_for_header(
    libraryName: Optional[str] = Query(None),
    fieldName: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    searchString: Optional[str] = Query(
        "", description=_generic_descriptions.HEADER_SEARCH_STRING
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    resultCount: Optional[int] = Query(
        10, description=_generic_descriptions.HEADER_RESULT_COUNT
    ),
):
    odm_form_service = OdmFormService()
    return odm_form_service.get_distinct_values_for_header(
        library=libraryName,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}",
    summary="Get details on a specific ODM Form (in a specific version)",
    description="",
    response_model=OdmForm,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_odm_form(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.get_by_uid(uid=uid)


@router.get(
    "/{uid}/relationships",
    summary="Get UIDs of a specific ODM Form's relationships",
    description="",
    response_model=dict,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_active_relationships(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.get_active_relationships(uid=uid)


@router.get(
    "/{uid}/versions",
    summary="List version history for ODM Forms",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Forms.
 - The returned versions are ordered by startDate descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=List[OdmForm],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_odm_form_versions(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.get_version_history(uid=uid)


@router.post(
    "/select",
    summary="Creates a new Form in 'Draft' status with version 0.1",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {"description": "Created - The odm form was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_form(
    odm_form_create_input: OdmFormPostInput = Body(None, description="")
):
    odm_form_service = OdmFormService()
    return odm_form_service.create(concept_input=odm_form_create_input)


@router.post(
    "/create",
    summary="Creates an ODM Form with relationships",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {"description": "Created - The odm form was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_form_with_relations(
    odm_form_with_relations_post_input: OdmFormWithRelationsPostInput = Body(
        None, description=""
    )
):
    odm_form_service = OdmFormService()
    return odm_form_service.create_with_relations(
        concept_input=odm_form_with_relations_post_input
    )


@router.patch(
    "/{uid}/select",
    summary="Update odm form",
    description="",
    response_model=OdmForm,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in draft status.\n"
            "- The ODM Form had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit_odm_form(
    uid: str = OdmFormUID,
    odm_form_edit_input: OdmFormPatchInput = Body(None, description=""),
):
    odm_form_service = OdmFormService()
    return odm_form_service.edit_draft(uid=uid, concept_edit_input=odm_form_edit_input)


@router.patch(
    "/{uid}/update",
    summary="Updates an ODM Form with relationships",
    description="",
    response_model=OdmForm,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in draft status.\n"
            "- The ODM Form had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit_odm_form_with_relations(
    uid: str = OdmFormUID,
    odm_form_with_relations_patch_input: OdmFormWithRelationsPatchInput = Body(
        None, description=""
    ),
):
    odm_form_service = OdmFormService()
    return odm_form_service.update_with_relations(
        uid=uid, concept_edit_input=odm_form_with_relations_patch_input
    )


@router.post(
    "/{uid}/new-version",
    summary=" Create a new version of ODM Form",
    description="""
State before:
 - uid must exist and the ODM Form must be in status Final.

Business logic:
- The ODM Form is changed to a draft state.

State after:
 - ODM Form changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create ODM Forms.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Form is not in final status.\n"
            "- The ODM Form with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_form_version(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.create_new_version(uid=uid)


@router.post(
    "/{uid}/approve",
    summary="Approve draft version of ODM Form",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in draft status.\n"
            "- The library does not allow to approve ODM Form.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve_odm_form(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.approve(uid=uid)


@router.post(
    "/{uid}/inactivate",
    summary=" Inactivate final version of ODM Form",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate_odm_form(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.inactivate_final(uid=uid)


@router.post(
    "/{uid}/reactivate",
    summary="Reactivate retired version of a ODM Form",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Form with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate_odm_form(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    return odm_form_service.reactivate_retired(uid=uid)


@router.post(
    "/{uid}/add-activity-groups",
    summary="Adds activity groups to the ODM Form.",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {
            "description": "Created - The activity groups were successfully added to the ODM Form."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity groups with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def add_activity_groups_to_odm_form(
    uid: str = OdmFormUID,
    override: bool = Query(
        False,
        description="If true, all existing activity group relationships will be replaced with the provided activity group relationships.",
    ),
    odm_form_activity_group_post_input: Sequence[OdmFormActivityGroupPostInput] = Body(
        None, description=""
    ),
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_activity_groups(
        uid=uid,
        odm_form_activity_group_post_input=odm_form_activity_group_post_input,
        override=override,
    )


@router.post(
    "/{uid}/add-item-groups",
    summary="Adds item groups to the ODM Form.",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {
            "description": "Created - The item groups were successfully added to the ODM Form."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The item groups with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def add_item_groups_to_odm_form(
    uid: str = OdmFormUID,
    override: bool = Query(
        False,
        description="If true, all existing item group relationships will be replaced with the provided item group relationships.",
    ),
    odm_form_item_group_post_input: Sequence[OdmFormItemGroupPostInput] = Body(
        None, description=""
    ),
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_item_groups(
        uid=uid,
        odm_form_item_group_post_input=odm_form_item_group_post_input,
        override=override,
    )


@router.post(
    "/{uid}/add-xml-extension-tags",
    summary="Adds xml extension tags to the ODM Form.",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {
            "description": "Created - The xml extension tags were successfully added to the ODM Form."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The xml extension tags with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def add_xml_extension_tags_to_odm_form(
    uid: str = OdmFormUID,
    override: bool = Query(
        False,
        description="If true, all existing xml extension tag relationships will be replaced with the provided xml extension tag relationships.",
    ),
    odm_xml_extension_relation_post_input: Sequence[
        OdmXmlExtensionRelationPostInput
    ] = Body(None, description=""),
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_xml_extension_tags(
        uid=uid,
        odm_xml_extension_relation_post_input=odm_xml_extension_relation_post_input,
        override=override,
    )


@router.post(
    "/{uid}/add-xml-extension-attributes",
    summary="Adds xml extension attributes to the ODM Form.",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {
            "description": "Created - The xml extension attributes were successfully added to the ODM Form."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The xml extension attributes with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def add_xml_extension_attributes_to_odm_form(
    uid: str = OdmFormUID,
    override: bool = Query(
        False,
        description="""If true, all existing xml extension attribute relationships will
        be replaced with the provided xml extension attribute relationships.""",
    ),
    odm_xml_extension_relation_post_input: Sequence[
        OdmXmlExtensionRelationPostInput
    ] = Body(None, description=""),
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_xml_extension_attributes(
        uid=uid,
        odm_xml_extension_relation_post_input=odm_xml_extension_relation_post_input,
        override=override,
    )


@router.post(
    "/{uid}/add-xml-extension-tag-attributes",
    summary="Adds xml extension tag attributes to the ODM Form.",
    description="",
    response_model=OdmForm,
    status_code=201,
    responses={
        201: {
            "description": "Created - The xml extension tag attributes were successfully added to the ODM Form."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The xml extension tag attributes with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def add_xml_extension_tag_attributes_to_odm_form(
    uid: str = OdmFormUID,
    override: bool = Query(
        False,
        description="""If true, all existing xml extension tag attribute relationships
        will be replaced with the provided xml extension tag attribute relationships.""",
    ),
    odm_xml_extension_relation_post_input: Sequence[
        OdmXmlExtensionRelationPostInput
    ] = Body(None, description=""),
):
    odm_form_service = OdmFormService()
    return odm_form_service.add_xml_extension_tag_attributes(
        uid=uid,
        odm_xml_extension_relation_post_input=odm_xml_extension_relation_post_input,
        override=override,
    )


@router.delete(
    "/{uid}",
    summary="Delete draft version of ODM Form",
    description="",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The ODM Form was successfully deleted."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Form is not in draft status.\n"
            "- The ODM Form was already in final state or is in use.\n"
            "- The library does not allow to delete ODM Form.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Form with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_odm_form(uid: str = OdmFormUID):
    odm_form_service = OdmFormService()
    odm_form_service.soft_delete(uid=uid)
