"""System models."""

from clinical_mdr_api.models.utils import BaseModel


class SystemInformation(BaseModel):
    api_version: str
    db_version: str
    db_name: str
    build_id: str
    commit_id: str
