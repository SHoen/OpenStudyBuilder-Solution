from clinical_mdr_api.domain.concepts.simple_concepts.text_value import (
    TextValueAR,
    TextValueVO,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.text_value_repository import (
    TextValueRepository,
)
from clinical_mdr_api.models.concept import TextValue, TextValueInput
from clinical_mdr_api.services.concepts.simple_concepts.simple_concept_generic import (
    SimpleConceptGenericService,
)


class TextValueService(SimpleConceptGenericService[TextValueAR]):

    aggregate_class = TextValueAR
    value_object_class = TextValueVO
    repository_interface = TextValueRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: TextValueAR
    ) -> TextValue:
        return TextValue.from_concept_ar(text_value=item_ar)

    def _create_aggregate_root(
        self, concept_input: TextValueInput, library
    ) -> TextValueAR:
        return self.aggregate_class.from_input_values(
            author=self.user_initials,
            simple_concept_vo=self.value_object_class.from_repository_values(
                name=concept_input.name,
                name_sentence_case=concept_input.nameSentenceCase,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                is_template_parameter=concept_input.templateParameter,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            find_uid_by_name_callback=self.repository.find_uid_by_name,
        )

    def _edit_aggregate(
        self, item: TextValueAR, concept_edit_input: TextValueInput
    ) -> TextValueAR:
        raise AttributeError(
            "_edit_aggregate function is not defined for TextValueService"
        )
