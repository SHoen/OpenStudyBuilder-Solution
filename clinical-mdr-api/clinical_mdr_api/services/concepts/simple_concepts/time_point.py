from clinical_mdr_api.domain.concepts.simple_concepts.time_point import (
    TimePointAR,
    TimePointVO,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.time_point_repository import (
    TimePointRepository,
)
from clinical_mdr_api.models.concept import (
    SimpleConceptInput,
    TimePoint,
    TimePointInput,
)
from clinical_mdr_api.services.concepts.simple_concepts.simple_concept_generic import (
    SimpleConceptGenericService,
)


class TimePointService(SimpleConceptGenericService[TimePointAR]):

    aggregate_class = TimePointAR
    repository_interface = TimePointRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: TimePointAR
    ) -> TimePoint:
        return TimePoint.from_concept_ar(time_point=item_ar)

    def _create_aggregate_root(
        self, concept_input: TimePointInput, library
    ) -> TimePointAR:
        return TimePointAR.from_input_values(
            author=self.user_initials,
            simple_concept_vo=TimePointVO.from_input_values(
                name_sentence_case=concept_input.nameSentenceCase,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                is_template_parameter=concept_input.templateParameter,
                numeric_value_uid=concept_input.numericValueUid,
                unit_definition_uid=concept_input.unitDefinitionUid,
                time_reference_uid=concept_input.timeReferenceUid,
                find_numeric_value_by_uid=self._repos.numeric_value_repository.find_by_uid_2,
                find_unit_definition_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                find_time_reference_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            find_uid_by_name_callback=self.repository.find_uid_by_name,
        )

    def _edit_aggregate(
        self, item: TimePointAR, concept_edit_input: SimpleConceptInput
    ) -> TimePointAR:
        raise AttributeError(
            "_edit_aggregate function is not defined for NumericValueService"
        )
