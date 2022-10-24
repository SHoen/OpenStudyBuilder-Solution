from typing import Any, Optional, Sequence

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json, List

from clinical_mdr_api.models import (
    OdmItem,
    OdmItemActivityPostInput,
    OdmItemPatchInput,
    OdmItemPostInput,
    OdmItemWithRelationsPatchInput,
    OdmItemWithRelationsPostInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.odm_common_models import OdmXmlExtensionRelationPostInput
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.odm_items import OdmItemService

router = APIRouter()

# Argument definitions
OdmItemUID = Path(None, description="The unique id of the ODM Item.")


@router.get(
    "",
    summary="Return every variable related to the selected status and version of the ODM Items",
    description="",
    response_model=CustomPage[OdmItem],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_all_odm_items(
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
    odm_item_service = OdmItemService()
    results = odm_item_service.get_all_concepts(
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
    odm_item_service = OdmItemService()
    return odm_item_service.get_distinct_values_for_header(
        library=libraryName,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}",
    summary="Get details on a specific ODM Item (in a specific version)",
    description="",
    response_model=OdmItem,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_odm_item(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.get_by_uid(uid=uid)


@router.get(
    "/{uid}/relationships",
    summary="Get UIDs of a specific ODM Item's relationships",
    description="",
    response_model=dict,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_active_relationships(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.get_active_relationships(uid=uid)


@router.get(
    "/{uid}/versions",
    summary="List version history for ODM Items",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Items.
 - The returned versions are ordered by startDate descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=List[OdmItem],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_odm_item_versions(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.get_version_history(uid=uid)


@router.post(
    "/select",
    summary="Creates a new Item in 'Draft' status with version 0.1",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {"description": "Created - The odm item was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_item(
    odm_item_create_input: OdmItemPostInput = Body(None, description="")
):
    odm_item_service = OdmItemService()
    return odm_item_service.create(concept_input=odm_item_create_input)


@router.post(
    "/create",
    summary="Creates an ODM Item with relationships",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {"description": "Created - The odm item was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_item_with_relations(
    odm_item_with_relations_post_input: OdmItemWithRelationsPostInput = Body(
        None, description=""
    )
):
    odm_item_service = OdmItemService()
    return odm_item_service.create_with_relations(
        concept_input=odm_item_with_relations_post_input
    )


@router.patch(
    "/{uid}/select",
    summary="Update odm item",
    description="",
    response_model=OdmItem,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in draft status.\n"
            "- The ODM Item had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit_odm_item(
    uid: str = OdmItemUID,
    odm_item_edit_input: OdmItemPatchInput = Body(None, description=""),
):
    odm_item_service = OdmItemService()
    return odm_item_service.edit_draft(uid=uid, concept_edit_input=odm_item_edit_input)


@router.patch(
    "/{uid}/update",
    summary="Updates an ODM Item with relationships",
    description="",
    response_model=OdmItem,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in draft status.\n"
            "- The ODM Item had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit_odm_item_with_relations(
    uid: str = OdmItemUID,
    odm_item_with_relations_patch_input: OdmItemWithRelationsPatchInput = Body(
        None, description=""
    ),
):
    odm_item_service = OdmItemService()
    return odm_item_service.update_with_relations(
        uid=uid, concept_edit_input=odm_item_with_relations_patch_input
    )


@router.post(
    "/{uid}/new-version",
    summary=" Create a new version of ODM Item",
    description="""
State before:
 - uid must exist and the ODM Item must be in status Final.

Business logic:
- The ODM Item is changed to a draft state.

State after:
 - ODM Item changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create ODM Items.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Item is not in final status.\n"
            "- The ODM Item with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_item_version(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.create_new_version(uid=uid)


@router.post(
    "/{uid}/approve",
    summary="Approve draft version of ODM Item",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in draft status.\n"
            "- The library does not allow to approve ODM Item.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve_odm_item(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.approve(uid=uid)


@router.post(
    "/{uid}/inactivate",
    summary=" Inactivate final version of ODM Item",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate_odm_item(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.inactivate_final(uid=uid)


@router.post(
    "/{uid}/reactivate",
    summary="Reactivate retired version of a ODM Item",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Item with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate_odm_item(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    return odm_item_service.reactivate_retired(uid=uid)


@router.post(
    "/{uid}/add-activities",
    summary="Adds activities to the ODM Item.",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {
            "description": "Created - The activities were successfully added to the ODM Item."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activities with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def add_activities_to_odm_item(
    uid: str = OdmItemUID,
    override: bool = Query(
        False,
        description="If true, all existing activity relationships will be replaced with the provided activity relationships.",
    ),
    odm_item_activity_post_input: Sequence[OdmItemActivityPostInput] = Body(
        None, description=""
    ),
):
    odm_item_service = OdmItemService()
    return odm_item_service.add_activities(
        uid=uid,
        odm_item_activity_post_input=odm_item_activity_post_input,
        override=override,
    )


@router.post(
    "/{uid}/add-xml-extension-tags",
    summary="Adds xml extension tags to the ODM Item.",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {
            "description": "Created - The xml extension tags were successfully added to the ODM Item."
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
def add_xml_extension_tags_to_odm_item(
    uid: str = OdmItemUID,
    override: bool = Query(
        False,
        description="If true, all existing xml extension tag relationships will be replaced with the provided xml extension tag relationships.",
    ),
    odm_xml_extension_relation_post_input: Sequence[
        OdmXmlExtensionRelationPostInput
    ] = Body(None, description=""),
):
    odm_item_service = OdmItemService()
    return odm_item_service.add_xml_extension_tags(
        uid=uid,
        odm_xml_extension_relation_post_input=odm_xml_extension_relation_post_input,
        override=override,
    )


@router.post(
    "/{uid}/add-xml-extension-attributes",
    summary="Adds xml extension attributes to the ODM Item.",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {
            "description": "Created - The xml extension attributes were successfully added to the ODM Item."
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
def add_xml_extension_attributes_to_odm_item(
    uid: str = OdmItemUID,
    override: bool = Query(
        False,
        description="""If true, all existing xml extension attribute relationships will
        be replaced with the provided xml extension attribute relationships.""",
    ),
    odm_xml_extension_relation_post_input: Sequence[
        OdmXmlExtensionRelationPostInput
    ] = Body(None, description=""),
):
    odm_item_service = OdmItemService()
    return odm_item_service.add_xml_extension_attributes(
        uid=uid,
        odm_xml_extension_relation_post_input=odm_xml_extension_relation_post_input,
        override=override,
    )


@router.post(
    "/{uid}/add-xml-extension-tag-attributes",
    summary="Adds xml extension tag attributes to the ODM Item.",
    description="",
    response_model=OdmItem,
    status_code=201,
    responses={
        201: {
            "description": "Created - The xml extension tag attributes were successfully added to the ODM Item."
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
def add_xml_extension_tag_attributes_to_odm_item(
    uid: str = OdmItemUID,
    override: bool = Query(
        False,
        description="""If true, all existing xml extension tag attribute relationships will
        be replaced with the provided xml extension tag attribute relationships.""",
    ),
    odm_xml_extension_relation_post_input: Sequence[
        OdmXmlExtensionRelationPostInput
    ] = Body(None, description=""),
):
    odm_item_service = OdmItemService()
    return odm_item_service.add_xml_extension_tag_attributes(
        uid=uid,
        odm_xml_extension_relation_post_input=odm_xml_extension_relation_post_input,
        override=override,
    )


@router.delete(
    "/{uid}",
    summary="Delete draft version of ODM Item",
    description="",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The ODM Item was successfully deleted."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Item is not in draft status.\n"
            "- The ODM Item was already in final state or is in use.\n"
            "- The library does not allow to delete ODM Item.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Item with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_odm_item(uid: str = OdmItemUID):
    odm_item_service = OdmItemService()
    odm_item_service.soft_delete(uid=uid)
