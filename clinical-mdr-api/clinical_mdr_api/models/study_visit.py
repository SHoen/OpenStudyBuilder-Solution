from datetime import datetime
from typing import Callable, Dict, List, Optional

from pydantic import Field, validator

from clinical_mdr_api.config import (
    DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
    DAY_UNIT_NAME,
    WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER,
    WEEK_UNIT_NAME,
)
from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domain.study_selection.study_epoch import StudyEpochEpoch
from clinical_mdr_api.domain.study_selection.study_visit import (
    StudyVisitContactMode,
    StudyVisitEpochAllocation,
    StudyVisitTimeReference,
    StudyVisitType,
    StudyVisitVO,
    VisitClass,
    VisitSubclass,
)
from clinical_mdr_api.models.utils import BaseModel


class StudyVisitCreateInput(BaseModel):
    study_epoch_uid: str = Field(alias="studyEpochUid")

    visitTypeUid: str = Field(source="has_visit_type.uid")
    timeReferenceUid: Optional[str]
    timeValue: Optional[int]
    timeUnitUid: Optional[str]

    visitSubLabelCodelistUid: Optional[str]
    visitSubLabelReference: Optional[str]

    legacyVisitId: Optional[str]
    legacyVisitTypeAlias: Optional[str]
    legacyName: Optional[str]
    legacySubName: Optional[str]

    consecutiveVisitGroup: Optional[str]

    show_visit: bool = Field(alias="showVisit")

    minVisitWindowValue: Optional[int] = -9999
    maxVisitWindowValue: Optional[int] = 9999
    visitWindowUnitUid: Optional[str]

    description: Optional[str]

    startRule: Optional[str]
    endRule: Optional[str]
    note: Optional[str]
    visitContactModeUid: str
    epochAllocationUid: Optional[str]
    visitClass: str
    visitSubclass: Optional[str]
    isGlobalAnchorVisit: bool


class StudyVisitEditInput(StudyVisitCreateInput):
    uid: str = Field(
        ...,
        title="Uid",
        description="Uid of the Visit",
    )


class TimeUnit(BaseModel):
    class Config:
        orm_mode = True

    name: Optional[str] = Field(
        None,
        description="Uid of visit unit",
        source="has_timepoint.has_latest_value.has_unit_definition.has_latest_value.name",
    )
    conversion_factor_to_master: Optional[float] = Field(
        None,
        description="Uid of visit unit",
        source="has_timepoint.has_latest_value.has_unit_definition.has_latest_value.conversion_factor_to_master",
    )
    from_timedelta: Optional[Callable] = Field(None, excludeFromOrm=True)

    @validator("from_timedelta", always=True)
    # pylint:disable=no-self-argument,unused-argument
    def validate_time_unit_obj(cls, value, values):
        if values.get("conversion_factor_to_master"):
            return lambda u, x: u.conversion_factor_to_master * x
        return None


class WindowTimeUnit(BaseModel):
    class Config:
        orm_mode = True

    name: Optional[str] = Field(
        None,
        description="Uid of visit unit",
        source="has_window_unit.has_latest_value.name",
    )
    conversion_factor_to_master: Optional[float] = Field(
        None,
        description="Uid of visit unit",
        source="has_window_unit.has_latest_value.conversion_factor_to_master",
    )
    from_timedelta: Optional[Callable] = Field(None, excludeFromOrm=True)

    @validator("from_timedelta", always=True)
    # pylint:disable=no-self-argument,unused-argument
    def validate_time_unit_obj(cls, value, values):
        if values.get("conversion_factor_to_master"):
            return lambda u, x: u.conversion_factor_to_master * x
        return None


class TimePoint(BaseModel):
    class Config:
        orm_mode = True

    uid: Optional[str] = Field(
        None,
        title="TimepointUid",
        description="Uid of timepoint",
        source="has_timepoint.uid",
    )

    time_unit_uid: Optional[str] = Field(
        None,
        title="TimeUnitUid",
        description="Uid of time unit",
        source="has_timepoint.has_latest_value.has_unit_definition.uid",
    )
    visit_timereference: Optional[StudyVisitTimeReference] = Field(
        None, source="has_timepoint.has_latest_value.has_time_reference.uid"
    )

    @validator("visit_timereference", pre=True)
    # pylint:disable=no-self-argument,unused-argument
    def instantiate_visit_timereference(cls, value, values):
        if value:
            return StudyVisitTimeReference[value]
        return None

    visit_value: Optional[int] = Field(
        None,
        title="TimepointValue",
        description="Value of timepoint",
        source="has_timepoint.has_latest_value.has_value.has_latest_value.value",
    )


class StudyDay(BaseModel):
    class Config:
        orm_mode = True

    uid: Optional[str] = Field(
        None,
        title="Study day uid",
        description="The uid of study day",
        source="has_study_day.uid",
    )
    value: Optional[int] = Field(
        None,
        title="Study day value",
        description="The value of the study day",
        source="has_study_day.has_latest_value.value",
    )


class StudyDurationDays(BaseModel):
    class Config:
        orm_mode = True

    uid: Optional[str] = Field(
        None,
        title="Study duration days uid",
        description="The uid of study duration days",
        source="has_study_duration_days.uid",
    )
    value: Optional[int] = Field(
        None,
        title="Study duration days value",
        description="The value of the study duration days",
        source="has_study_duration_days.has_latest_value.value",
    )


class StudyWeek(BaseModel):
    class Config:
        orm_mode = True

    uid: Optional[str] = Field(
        None,
        title="Study week uid",
        description="The uid of study week",
        source="has_study_week.uid",
    )
    value: Optional[int] = Field(
        None,
        title="Study week value",
        description="The value of the study week",
        source="has_study_week.has_latest_value.value",
    )


class StudyDurationWeeks(BaseModel):
    class Config:
        orm_mode = True

    uid: Optional[str] = Field(
        None,
        title="Study duration weeks uid",
        description="The uid of study duration weeks",
        source="has_study_duration_weeks.uid",
    )
    value: Optional[int] = Field(
        None,
        title="Study duration weeks value",
        description="The value of the study duration weeks",
        source="has_study_duration_weeks.has_latest_value.value",
    )


class VisitName(BaseModel):
    class Config:
        orm_mode = True

    uid: Optional[str] = Field(
        None,
        title="Visit name uid",
        description="The uid of the visit name",
        source="has_visit_name.uid",
    )
    value: Optional[str] = Field(
        None,
        title="Visit name name",
        description="The name of the visit",
        source="has_visit_name.has_latest_value.name",
    )


class StudyEpochSimpleOGM(BaseModel):
    class Config:
        orm_mode = True

    uid: str = Field(
        ...,
        title="Visit name uid",
        description="The uid of the visit name",
        source="study_epoch_has_study_visit.uid",
    )
    study_uid: str = Field(
        ...,
        title="Study Uid",
        description="The uid of the study",
        source="has_after.audit_trail.uid",
    )
    epoch: "StudyEpochEpoch" = Field(
        ...,
        title="Visit name name",
        description="The name of the visit",
        source="study_epoch_has_study_visit.has_epoch.uid",
    )

    @validator("epoch", pre=True)
    # pylint:disable=no-self-argument,unused-argument
    def instantiate_epoch(cls, value, values):
        return StudyEpochEpoch[value]

    order: int = Field(
        ...,
        title="Study epoch order",
        description="The order of epoch",
        source="study_epoch_has_study_visit.order",
    )


class StudyVisitOGM(BaseModel, StudyVisitVO):
    class Config:
        orm_mode = True

    uid: str = Field(..., title="Uid", description="Uid of the Visit", source="uid")

    consecutive_visit_group: Optional[str] = Field(
        None,
        title="Consecutive visit group",
        description="Consecutive visit group",
        source="consecutive_visit_group",
    )
    visit_window_min: Optional[int] = Field(
        None,
        title="Visit window min",
        description="Min value of visit window",
        source="visit_window_min",
    )
    visit_window_max: Optional[int] = Field(
        None,
        title="Visit window max",
        description="Max value of visit window",
        source="visit_window_max",
    )
    window_unit_uid: Optional[str] = Field(
        None,
        title="Window unit uid",
        description="Uid of window unit",
        source="has_window_unit.uid",
    )
    description: Optional[str] = Field(
        None,
        title="Description",
        description="Description",
        source="description",
    )
    start_rule: Optional[str] = Field(
        None,
        title="Start rule",
        description="The start rule of visit",
        source="start_rule",
    )
    end_rule: Optional[str] = Field(
        None, title="End rule", description="The end rule of visit", source="end_rule"
    )
    note: Optional[str] = Field(None, title="Note", description="Note", source="note")
    visit_contact_mode: StudyVisitContactMode = Field(
        ...,
        title="Visit contact mode",
        description="The contact mode of study visit",
        source="has_visit_contact_mode.uid",
    )

    @validator("visit_contact_mode", pre=True)
    # pylint:disable=no-self-argument,unused-argument
    def instantiate_visit_contact_mode(cls, value, values):
        return StudyVisitContactMode[value]

    epoch_allocation: Optional[StudyVisitEpochAllocation] = Field(
        None,
        title="Epoch allocation rule",
        description="Epoch allocation rule",
        source="has_epoch_allocation.uid",
    )

    @validator("epoch_allocation", pre=True)
    # pylint:disable=no-self-argument,unused-argument
    def instantiate_epoch_allocation(cls, value, values):
        if value:
            return StudyVisitEpochAllocation[value]
        return None

    visit_type: StudyVisitType = Field(
        ...,
        title="visitUnitUid",
        description="Uid of visit unit",
        source="has_visit_type.uid",
    )

    @validator("visit_type", pre=True)
    # pylint:disable=no-self-argument,unused-argument
    def instantiate_visit_type(cls, value, values):
        return StudyVisitType[value]

    author: str = Field(
        ...,
        title="User Initials",
        description="Initials of user that created last modification",
        source="has_after.user_initials",
    )
    start_date: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study visit was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="has_after.date",
    )
    status: StudyStatus = Field(
        ..., title="Status", description="Study visit status", source="status"
    )

    @validator("status", pre=True)
    # pylint:disable=no-self-argument,unused-argument
    def instantiate_study_status(cls, value, values):
        return StudyStatus[value]

    visit_class: VisitClass = Field(
        title="Visit class", description="Visit class", source="visit_class"
    )

    @validator("visit_class", pre=True)
    # pylint:disable=no-self-argument
    def instantiate_visit_class(cls, value):
        return VisitClass[value]

    visit_subclass: Optional[VisitSubclass] = Field(
        None,
        title="Visit subclass",
        description="Visit subclass",
        source="visit_subclass",
    )

    @validator("visit_subclass", pre=True)
    # pylint:disable=no-self-argument
    def instantiate_visit_subclass(cls, value):
        if value:
            return VisitSubclass[value]
        return None

    is_global_anchor_visit: bool = Field(
        ...,
        title="Is global anchor visit",
        description="Is global anchor visit",
        source="is_global_anchor_visit",
    )

    timepoint: Optional[TimePoint] = Field(None)
    study_day: Optional[StudyDay] = Field(None)
    study_week: Optional[StudyWeek] = Field(None)
    study_duration_days: Optional[StudyDurationDays] = Field(None)
    study_duration_weeks: Optional[StudyDurationWeeks] = Field(None)
    visit_name_sc: VisitName = Field(...)

    legacy_visit_id: Optional[str] = Field(
        ...,
        title="Legacy Visit Uid",
        description="The uid of legacy visit",
        source="legacy_visit_id",
    )
    legacy_visit_type_alias: Optional[str] = Field(
        ...,
        title="Legacy Visit type alias",
        description="Legacy Visit type alias",
        source="legacy_visit_type_alias",
    )
    legacy_name: Optional[str] = Field(
        ..., title="Legacy name", description="Legacy name", source="legacy_name"
    )
    legacy_sub_name: Optional[str] = Field(
        ...,
        title="Legacy sub name",
        description="Legacy sub name",
        source="legacy_sub_name",
    )

    visit_number: int = Field(
        ...,
        title="Visit number",
        description="The number of the study visit",
        source="visit_number",
    )
    visit_order: Optional[int] = Field(
        None, title="Visit order", description="The order of the study visit"
    )
    subvisit_number: Optional[int] = Field(
        None, title="Subvisit number", description="Subvisit number"
    )
    subvisit_anchor: Optional["StudyVisitOGM"]
    show_visit: bool = Field(
        ...,
        title="Show visit",
        description="Whether to show visit or not",
        source="show_visit",
    )
    time_unit_object: Optional[TimeUnit] = Field(...)
    window_unit_object: Optional[WindowTimeUnit] = Field(...)
    epoch_connector: StudyEpochSimpleOGM = Field(...)
    day_unit_object: TimeUnit = Field(...)

    @validator("day_unit_object", pre=True, always=True)
    # pylint:disable=no-self-argument,unused-argument
    def validate_day_unit_obj(cls, value, values):
        return TimeUnit(
            name=DAY_UNIT_NAME,
            conversion_factor_to_master=DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
            from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
        )

    week_unit_object: TimeUnit = Field(...)

    @validator("week_unit_object", pre=True, always=True)
    # pylint:disable=no-self-argument,unused-argument
    def validate_week_unit_obj(cls, value, values):
        return TimeUnit(
            name=WEEK_UNIT_NAME,
            conversion_factor_to_master=WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER,
            from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
        )

    anchor_visit: Optional["StudyVisitOGM"]
    is_deleted: bool = Field(
        ...,
        title="Is deleted",
        description="Whether visit is deleted or not",
        source="is_deleted",
    )

    visit_sub_label: Optional[str] = Field(
        ..., title="Status", description="Study visit status", source="visit_sub_label"
    )
    visit_sub_label_reference: Optional[str] = Field(
        None,
        title="Status",
        description="Study visit status",
        source="visit_sub_label_reference",
    )
    visit_sub_label_uid: Optional[str] = Field(
        ...,
        title="Status",
        description="Study visit status",
        source="visit_sub_label_uid",
    )


class StudyVisitOGMVer(StudyVisitOGM):
    pass


class SimpleStudyVisit(BaseModel):
    class Config:
        orm_mode = True

    uid: str = Field(..., title="Uid", description="Uid of the visit", source="uid")
    visitName: str = Field(
        ...,
        title="Visit name",
        description="Name of the visit",
        source="has_visit_name.has_latest_value.name",
    )
    visitTypeName: str = Field(
        ...,
        title="Visit type name",
        description="Name of the visit type",
        source="has_visit_type.has_name_root.has_latest_value.name",
    )


class StudyVisit(StudyVisitEditInput):
    class Config:
        allow_population_by_field_name = True
        orm_mode = True

    studyUid: str
    studyEpochName: str
    # studyEpochName can be calculated from uid
    epochUid: str = Field(
        ...,
        title="The uid of the study epoch",
        description="The uid of the study epoch",
    )

    order: int

    visitTypeName: str

    timeReferenceUid: Optional[str]
    timeReferenceName: Optional[str]
    timeValue: Optional[int]
    timeUnitUid: Optional[str]
    timeUnitName: Optional[str]
    visitContactModeUid: str
    visitContactModeName: str
    epochAllocationUid: Optional[str]
    epochAllocationName: Optional[str]

    durationTime: Optional[float]
    durationTimeUnit: Optional[str]

    studyDayNumber: Optional[int]
    studyDurationDaysLabel: Optional[str]
    studyDayLabel: Optional[str]
    studyWeekNumber: Optional[int]
    studyDurationWeeksLabel: Optional[str]
    studyWeekLabel: Optional[str]

    visit_number: int = Field(alias="visitNumber")
    visitSubNumber: int

    unique_visit_number: int = Field(alias="uniqueVisitNumber")
    visitSubName: str
    visit_sub_label: Optional[str] = Field(alias="visitSubLabel")

    visitName: str
    visitShortName: str

    visitWindowUnitName: Optional[str]
    visitClass: str
    visitSubclass: Optional[str]
    isGlobalAnchorVisit: bool
    status: str = Field(..., title="Status", description="Study Visit status")
    startDate: str = Field(
        ..., title="Creation Date", description="Study Visit creation date"
    )
    userInitials: str = Field(
        ...,
        title="User Initials",
        description="Initials of user that created last modification",
    )
    possibleActions: List[str] = Field(
        ..., title="Possible actions", description="List of actions to perform on item"
    )
    studyActivityCount: Optional[int] = Field(
        None, description="Count of Study Activities assigned to Study Visit"
    )


class StudyVisitVersion(StudyVisit):
    changes: Dict


class AllowedVisitTypesForEpochType(BaseModel):
    visit_type_uid: str = Field(
        ..., title="visit type uid", description="Visit Type Term uid"
    )
    visit_type_name: str = Field(
        ..., title="visit type name", description="Visit type Term name"
    )


class AllowedTimeReferences(BaseModel):
    timeReferenceUid: str
    timeReferenceName: str
