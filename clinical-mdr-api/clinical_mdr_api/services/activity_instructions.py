from clinical_mdr_api import models
from clinical_mdr_api.domain.library.activity_instructions import ActivityInstructionAR
from clinical_mdr_api.domain_repositories.library.activity_instruction_repository import (
    ActivityInstructionRepository,
)
from clinical_mdr_api.domain_repositories.templates.activity_description_template_repository import (
    ActivityDescriptionTemplateRepository,
)
from clinical_mdr_api.services.generic_object_service import (
    GenericObjectService,  # type: ignore
)


class ActivityInstructionService(GenericObjectService[ActivityInstructionAR]):
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityInstructionAR
    ) -> models.ActivityInstruction:
        return models.ActivityInstruction.from_activity_instruction_ar(item_ar)

    aggregate_class = ActivityInstructionAR
    repository_interface = ActivityInstructionRepository
    template_repository_interface = ActivityDescriptionTemplateRepository
    templateUidProperty = "activityInstructionTemplateUid"
    templateNameProperty = "activityInstructionTemplate"
    version_class = models.ActivityInstructionVersion
