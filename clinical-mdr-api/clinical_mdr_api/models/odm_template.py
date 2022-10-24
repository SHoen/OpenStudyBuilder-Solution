from datetime import date
from typing import Callable, Dict, List, Optional, Sequence

from pydantic import BaseModel, Field

from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domain.concepts.odms.form import OdmFormRefVO
from clinical_mdr_api.domain.concepts.odms.template import OdmTemplateAR
from clinical_mdr_api.models.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.odm_form import OdmFormRefModel


class OdmTemplate(ConceptModel):
    oid: Optional[str]
    effectiveDate: Optional[date]
    retiredDate: Optional[date]
    description: Optional[str]
    forms: Optional[Sequence[OdmFormRefModel]]
    possibleActions: List[str]

    @classmethod
    def from_odm_template_ar(
        cls,
        odm_template_ar: OdmTemplateAR,
        find_odm_form_by_uid_with_template_relation: Callable[
            [str, str], Optional[OdmFormRefVO]
        ],
    ) -> "OdmTemplate":
        return cls(
            uid=odm_template_ar._uid,
            name=odm_template_ar.concept_vo.name,
            oid=odm_template_ar.concept_vo.oid,
            effectiveDate=odm_template_ar.concept_vo.effective_date,
            retiredDate=odm_template_ar.concept_vo.retired_date,
            description=odm_template_ar.concept_vo.description,
            libraryName=odm_template_ar.library.name,
            startDate=odm_template_ar.item_metadata.start_date,
            endDate=odm_template_ar.item_metadata.end_date,
            status=odm_template_ar.item_metadata.status.value,
            version=odm_template_ar.item_metadata.version,
            changeDescription=odm_template_ar.item_metadata.change_description,
            userInitials=odm_template_ar.item_metadata.user_initials,
            forms=sorted(
                [
                    OdmFormRefModel.from_odm_form_uid(
                        uid=form_uid,
                        template_uid=odm_template_ar._uid,
                        find_odm_form_by_uid_with_template_relation=find_odm_form_by_uid_with_template_relation,
                    )
                    for form_uid in odm_template_ar.concept_vo.form_uids
                ],
                key=lambda item: item.orderNumber,
            ),
            possibleActions=sorted(
                [_.value for _ in odm_template_ar.get_possible_actions()]
            ),
        )


class OdmTemplateSimpleModel(BaseModel):
    @classmethod
    def from_odm_template_uid(
        cls,
        uid: str,
        find_odm_template_by_uid: Callable[[str], Optional[ConceptARBase]],
    ) -> Optional["OdmTemplateSimpleModel"]:

        if uid is not None:
            odm_template = find_odm_template_by_uid(uid)

            if odm_template is not None:
                simple_odm_template_model = cls(
                    uid=uid,
                    name=odm_template.concept_vo.name,
                )
            else:
                simple_odm_template_model = cls(
                    uid=uid,
                    name=None,
                )
        else:
            simple_odm_template_model = None
        return simple_odm_template_model

    uid: str = Field(..., title="uid", description="")
    name: Optional[str] = Field(None, title="name", description="")


class OdmTemplatePostInput(ConceptPostInput):
    oid: Optional[str]
    effectiveDate: Optional[date]
    retiredDate: Optional[date]
    description: Optional[str]


class OdmTemplatePatchInput(ConceptPatchInput):
    oid: Optional[str]
    effectiveDate: Optional[date]
    retiredDate: Optional[date]
    description: Optional[str]


class OdmTemplateFormPostInput(BaseModel):
    uid: str
    orderNumber: int
    mandatory: str
    locked: str = "No"
    collectionExceptionConditionOid: Optional[str]


class OdmTemplateVersion(OdmTemplate):
    """
    Class for storing OdmTemplates and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the timeframe (e.g. name, startDate, ..)."
        ),
    )
