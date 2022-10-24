from typing import Callable, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domain.concepts.odms.alias import OdmAliasAR
from clinical_mdr_api.models.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.error import BatchErrorResponse


class OdmAlias(ConceptModel):
    context: str
    possibleActions: List[str]

    @classmethod
    def from_odm_alias_ar(cls, odm_alias_ar: OdmAliasAR) -> "OdmAlias":
        return cls(
            uid=odm_alias_ar._uid,
            name=odm_alias_ar.name,
            context=odm_alias_ar.concept_vo.context,
            libraryName=odm_alias_ar.library.name,
            startDate=odm_alias_ar.item_metadata.start_date,
            endDate=odm_alias_ar.item_metadata.end_date,
            status=odm_alias_ar.item_metadata.status.value,
            version=odm_alias_ar.item_metadata.version,
            changeDescription=odm_alias_ar.item_metadata.change_description,
            userInitials=odm_alias_ar.item_metadata.user_initials,
            possibleActions=sorted(
                [_.value for _ in odm_alias_ar.get_possible_actions()]
            ),
        )


class OdmAliasSimpleModel(BaseModel):
    @classmethod
    def from_odm_alias_uid(
        cls, uid: str, find_odm_alias_by_uid: Callable[[str], Optional[ConceptARBase]]
    ) -> Optional["OdmAliasSimpleModel"]:

        if uid is not None:
            odm_alias = find_odm_alias_by_uid(uid)

            if odm_alias is not None:
                simple_odm_alias_model = cls(
                    uid=uid,
                    name=odm_alias.concept_vo.name,
                    context=odm_alias.concept_vo.context,
                    version=odm_alias.item_metadata.version,
                )
            else:
                simple_odm_alias_model = cls(
                    uid=uid, name=None, context=None, version=None
                )
        else:
            simple_odm_alias_model = None
        return simple_odm_alias_model

    uid: str = Field(..., title="uid", description="")
    name: Optional[str] = Field(None, title="name", description="")
    context: Optional[str] = Field(None, title="context", description="")
    version: Optional[str] = Field(None, title="version", description="")


class OdmAliasPostInput(ConceptPostInput):
    context: str


class OdmAliasPatchInput(ConceptPatchInput):
    context: Optional[str]


class OdmAliasBatchPatchInput(OdmAliasPatchInput):
    uid: str


class OdmAliasBatchInput(BaseModel):
    method: str = Field(
        ..., title="method", description="HTTP method corresponding to operation type"
    )
    content: Union[OdmAliasBatchPatchInput, OdmAliasPostInput]


class OdmAliasBatchOutput(BaseModel):
    responseCode: int = Field(
        ...,
        title="responseCode",
        description="The HTTP response code related to input operation",
    )
    content: Union[OdmAlias, None, BatchErrorResponse]


class OdmAliasVersion(OdmAlias):
    """
    Class for storing OdmAlias and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )
