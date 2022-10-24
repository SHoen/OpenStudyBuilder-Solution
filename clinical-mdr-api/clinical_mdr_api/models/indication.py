from datetime import datetime
from typing import Optional

from pydantic import Field

from clinical_mdr_api.models.template_parameter_value import TemplateParameterValue
from clinical_mdr_api.models.utils import BaseModel


class Indication(TemplateParameterValue):
    uid: str = Field(
        ...,
        title="uid",
        description="The unique id of the indication value.",
    )

    name: Optional[str] = Field(
        ...,
        title="name",
        description="The name or the actual value. E.g. 'Sickle Cell Disease', 'Obesity', ...",
    )

    snomedConceptId: Optional[str] = Field(
        ...,
        title="snomedConceptId",
        description="The SNOMED identifier of the indication value. E.g. 26929004",
    )

    snomedConceptName: Optional[str] = Field(
        ...,
        title="snomedConceptName",
        description="The SNOMED name of the indication value, e.g. 'Sickling disorder due to hemoglobin S (disorder)'",
    )

    startDate: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the (version of the) indication was created. "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )
    endDate: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the version of the indication was closed (and a new one was created). "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )
    status: Optional[str] = Field(
        None,
        description="The status in which the (version of the) indication is in. "
        "Possible values are: 'Final', 'Draft' or 'Retired'.",
    )
    version: Optional[str] = Field(
        None,
        description="The version number of the (version of the) indication. "
        "The format is: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...",
    )
    changeDescription: Optional[str] = Field(
        None,
        description="A short description about what has changed compared to the previous version.",
    )
    userInitials: Optional[str] = Field(
        None,
        description="The initials of the user that triggered the change of the indication.",
    )

    type: Optional[str] = Field(title="type", description="type of template parameter")


class IndicationCreateInput(BaseModel):
    name: str = Field(
        ...,
        description="The name or the actual value. E.g. 'Sickle Cell Disease', 'Obesity', ...",
    )

    libraryName: Optional[str] = Field(
        "Sponsor",
        description="If specified: The name of the library to which the indication will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'isEditable' property of the library needs to be true.",
    )

    snomedConceptId: str = Field(
        ...,
        title="snomedConceptId",
        description="The SNOMED identifier of the indication value. E.g. 26929004",
    )

    snomedConceptName: str = Field(
        ...,
        title="snomedConceptName",
        description="The SNOMED name of the indication value, e.g. 'Sickling disorder due to hemoglobin S (disorder)'",
    )
