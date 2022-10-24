from typing import Callable, Dict, List, Optional, Sequence, Union

from pydantic import Field

from clinical_mdr_api.domain.concepts.odms.alias import OdmAliasAR
from clinical_mdr_api.domain.concepts.odms.description import OdmDescriptionAR
from clinical_mdr_api.domain.concepts.odms.formal_expression import (
    OdmFormalExpressionAR,
)
from clinical_mdr_api.domain.concepts.odms.method import OdmMethodAR
from clinical_mdr_api.models.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.odm_alias import OdmAliasSimpleModel
from clinical_mdr_api.models.odm_description import (
    OdmDescriptionBatchPatchInput,
    OdmDescriptionPostInput,
    OdmDescriptionSimpleModel,
)
from clinical_mdr_api.models.odm_formal_expression import (
    OdmFormalExpressionBatchPatchInput,
    OdmFormalExpressionPostInput,
    OdmFormalExpressionSimpleModel,
)


class OdmMethod(ConceptModel):
    oid: Optional[str]
    type: Optional[str]
    formalExpressions: Optional[Sequence[OdmFormalExpressionSimpleModel]]
    descriptions: Sequence[OdmDescriptionSimpleModel]
    aliases: Optional[Sequence[OdmAliasSimpleModel]]
    possibleActions: List[str]

    @classmethod
    def from_odm_method_ar(
        cls,
        odm_method_ar: OdmMethodAR,
        find_odm_formal_expression_by_uid: Callable[
            [str], Optional[OdmFormalExpressionAR]
        ],
        find_odm_description_by_uid: Callable[[str], Optional[OdmDescriptionAR]],
        find_odm_alias_by_uid: Callable[[str], Optional[OdmAliasAR]],
    ) -> "OdmMethod":
        return cls(
            uid=odm_method_ar._uid,
            oid=odm_method_ar.concept_vo.oid,
            name=odm_method_ar.concept_vo.name,
            type=odm_method_ar.concept_vo.method_type,
            libraryName=odm_method_ar.library.name,
            startDate=odm_method_ar.item_metadata.start_date,
            endDate=odm_method_ar.item_metadata.end_date,
            status=odm_method_ar.item_metadata.status.value,
            version=odm_method_ar.item_metadata.version,
            changeDescription=odm_method_ar.item_metadata.change_description,
            userInitials=odm_method_ar.item_metadata.user_initials,
            formalExpressions=sorted(
                [
                    OdmFormalExpressionSimpleModel.from_odm_formal_expression_uid(
                        uid=formal_expression_uid,
                        find_odm_formal_expression_by_uid=find_odm_formal_expression_by_uid,
                    )
                    for formal_expression_uid in odm_method_ar.concept_vo.formal_expression_uids
                ],
                key=lambda item: item.expression,
            ),
            descriptions=sorted(
                [
                    OdmDescriptionSimpleModel.from_odm_description_uid(
                        uid=description_uid,
                        find_odm_description_by_uid=find_odm_description_by_uid,
                    )
                    for description_uid in odm_method_ar.concept_vo.description_uids
                ],
                key=lambda item: item.name,
            ),
            aliases=sorted(
                [
                    OdmAliasSimpleModel.from_odm_alias_uid(
                        uid=alias_uid,
                        find_odm_alias_by_uid=find_odm_alias_by_uid,
                    )
                    for alias_uid in odm_method_ar.concept_vo.alias_uids
                ],
                key=lambda item: item.name,
            ),
            possibleActions=sorted(
                [_.value for _ in odm_method_ar.get_possible_actions()]
            ),
        )


class OdmMethodPostInput(ConceptPostInput):
    oid: Optional[str]
    type: Optional[str]
    formalExpressionUids: Sequence[str]
    descriptionUids: Sequence[str]
    aliasUids: Sequence[str]


class OdmMethodWithRelationsPostInput(ConceptPostInput):
    oid: Optional[str]
    type: Optional[str]
    formalExpressions: Sequence[Union[OdmFormalExpressionPostInput, str]]
    descriptions: Sequence[Union[OdmDescriptionPostInput, str]]
    aliasUids: Sequence[str]


class OdmMethodPatchInput(ConceptPatchInput):
    oid: Optional[str]
    type: Optional[str]
    formalExpressionUids: Sequence[str]
    descriptionUids: Sequence[str]
    aliasUids: Sequence[str]


class OdmMethodWithRelationsPatchInput(ConceptPatchInput):
    oid: Optional[str]
    type: Optional[str]
    formalExpressions: Sequence[
        Union[OdmFormalExpressionBatchPatchInput, OdmFormalExpressionPostInput]
    ]
    descriptions: Sequence[
        Union[OdmDescriptionBatchPatchInput, OdmDescriptionPostInput]
    ]
    aliasUids: Sequence[str]


class OdmMethodVersion(OdmMethod):
    """
    Class for storing OdmMethod and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )
