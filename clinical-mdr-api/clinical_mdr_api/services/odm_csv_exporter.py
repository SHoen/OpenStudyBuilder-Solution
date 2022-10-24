from clinical_mdr_api.domain.concepts.utils import TargetType
from clinical_mdr_api.domain_repositories.concepts.odms.metadata_repository import (
    MetadataRepository,
)


class OdmCsvExporterService:
    repo: MetadataRepository
    target_uid: str
    target_type: TargetType

    def __init__(
        self,
        target_uid: str,
        target_type: TargetType,
    ):
        self.target_uid = target_uid
        self.target_type = target_type
        self.repo = MetadataRepository()

    def get_odm_csv(self):
        if self.target_type == TargetType.TEMPLATE:
            return self.repo.get_odm_template(self.target_uid)
        if self.target_type == TargetType.FORM:
            return self.repo.get_odm_form(self.target_uid)
        if self.target_type == TargetType.ITEM_GROUP:
            return self.repo.get_odm_item_group(self.target_uid)
        if self.target_type == TargetType.ITEM:
            return self.repo.get_odm_item(self.target_uid)

        raise NotImplementedError(
            "Method for handling this target type is not implemented."
        )
