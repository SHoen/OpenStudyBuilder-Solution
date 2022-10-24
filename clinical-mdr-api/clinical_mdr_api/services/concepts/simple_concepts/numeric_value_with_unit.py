from clinical_mdr_api.domain.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitAR,
    NumericValueWithUnitVO,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.numeric_value_with_unit_repository import (
    NumericValueWithUnitRepository,
)
from clinical_mdr_api.models.concept import (
    NumericValueWithUnit,
    NumericValueWithUnitInput,
    SimpleConceptInput,
)
from clinical_mdr_api.services.concepts.simple_concepts.simple_concept_generic import (
    SimpleConceptGenericService,
)


class NumericValueWithUnitService(SimpleConceptGenericService[NumericValueWithUnitAR]):

    aggregate_class = NumericValueWithUnitAR
    value_object_class = NumericValueWithUnitVO
    repository_interface = NumericValueWithUnitRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: NumericValueWithUnitAR
    ) -> NumericValueWithUnit:
        return NumericValueWithUnit.from_concept_ar(numeric_value=item_ar)

    def _create_aggregate_root(
        self, concept_input: NumericValueWithUnitInput, library
    ) -> NumericValueWithUnitAR:
        return self.aggregate_class.from_input_values(
            author=self.user_initials,
            simple_concept_vo=self.value_object_class.from_input_values(
                value=concept_input.value,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                is_template_parameter=concept_input.templateParameter,
                unit_definition_uid=concept_input.unitDefinitionUid,
                find_unit_definition_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            find_uid_by_value_and_unit_callback=self._repos.numeric_value_with_unit_repository.find_uid_by_value_and_unit,
        )

    def _edit_aggregate(
        self, item: NumericValueWithUnitAR, concept_edit_input: SimpleConceptInput
    ) -> NumericValueWithUnitAR:
        raise AttributeError(
            "_edit_aggregate function is not defined for NumericValueWithUnitService"
        )
