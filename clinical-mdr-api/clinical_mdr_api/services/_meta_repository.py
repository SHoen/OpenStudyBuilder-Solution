from typing import Any, Callable, Mapping, MutableMapping

from clinical_mdr_api.domain_repositories.brand.brand_repository import BrandRepository
from clinical_mdr_api.domain_repositories.clinical_programme.clinical_programme_repository import (
    ClinicalProgrammeRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.activity_group_repository import (
    ActivityGroupRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.activity_repository import (
    ActivityRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.activity_sub_group_repository import (
    ActivitySubGroupRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.categoric_finding_repository import (
    CategoricFindingRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.compound_dosing_repository import (
    CompoundDosingRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.event_repository import (
    EventRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.laboratory_activity_repository import (
    LaboratoryActivityRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.numeric_finding_repository import (
    NumericFindingRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.rating_scale_repository import (
    RatingScaleRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.reminder_repository import (
    ReminderRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.special_purpose_repository import (
    SpecialPurposeRepository,
)
from clinical_mdr_api.domain_repositories.concepts.activities.textual_finding_repository import (
    TextualFindingRepository,
)
from clinical_mdr_api.domain_repositories.concepts.compound_alias_repository import (
    CompoundAliasRepository,
)
from clinical_mdr_api.domain_repositories.concepts.compound_repository import (
    CompoundRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.alias_repository import (
    AliasRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.condition_repository import (
    ConditionRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.description_repository import (
    DescriptionRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.form_repository import (
    FormRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.formal_expression_repository import (
    FormalExpressionRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.item_group_repository import (
    ItemGroupRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.item_repository import (
    ItemRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.method_repository import (
    MethodRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.template_repository import (
    TemplateRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.xml_extension_attribute_repository import (
    XmlExtensionAttributeRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.xml_extension_repository import (
    XmlExtensionRepository,
)
from clinical_mdr_api.domain_repositories.concepts.odms.xml_extension_tag_repository import (
    XmlExtensionTagRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.lag_time_repository import (
    LagTimeRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.numeric_value_repository import (
    NumericValueRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.numeric_value_with_unit_repository import (
    NumericValueWithUnitRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.study_day_repository import (
    StudyDayRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.study_duration_days_repository import (
    StudyDurationDaysRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.study_duration_weeks_repository import (
    StudyDurationWeeksRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.study_week_repository import (
    StudyWeekRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.text_value_repository import (
    TextValueRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.time_point_repository import (
    TimePointRepository,
)
from clinical_mdr_api.domain_repositories.concepts.simple_concepts.visit_name_repository import (
    VisitNameRepository,
)
from clinical_mdr_api.domain_repositories.concepts.unit_definition.unit_definition_repository import (
    UnitDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.configuration.configuration_repository import (
    CTConfigRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_catalogue_repository import (
    CTCatalogueRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_codelist_aggregated_repository import (
    CTCodelistAggregatedRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_codelist_name_repository import (
    CTCodelistNameRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_package_repository import (
    CTPackageRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_term_aggregated_repository import (
    CTTermAggregatedRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_term_attributes_repository import (
    CTTermAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_term_name_repository import (
    CTTermNameRepository,
)
from clinical_mdr_api.domain_repositories.dictionaries.dictionary_codelist_repository import (
    DictionaryCodelistGenericRepository,
)
from clinical_mdr_api.domain_repositories.dictionaries.dictionary_term_repository import (
    DictionaryTermGenericRepository,
)
from clinical_mdr_api.domain_repositories.dictionaries.dictionary_term_substance_repository import (
    DictionaryTermSubstanceRepository,
)
from clinical_mdr_api.domain_repositories.library.criteria_repository import (
    CriteriaRepository,
)
from clinical_mdr_api.domain_repositories.library.endpoint_repository import (
    EndpointRepository,
)
from clinical_mdr_api.domain_repositories.library.library_repository import (
    LibraryRepository,
)
from clinical_mdr_api.domain_repositories.library.objective_repository import (
    ObjectiveRepository,
)
from clinical_mdr_api.domain_repositories.library.template_parameters_repository import (
    TemplateParameterRepository,
)
from clinical_mdr_api.domain_repositories.library.timeframe_repository import (
    TimeframeRepository,
)
from clinical_mdr_api.domain_repositories.project.project_repository import (
    ProjectRepository,
)

# noinspection PyProtectedMember
from clinical_mdr_api.domain_repositories.simple_dictionaries._simple_terminology_item_repository import (
    SimpleTerminologyItemRepository,
)
from clinical_mdr_api.domain_repositories.study_definition.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.study_definition.study_definition_repository_impl import (
    StudyDefinitionRepositoryImpl,
)

# noinspection PyProtectedMember
from clinical_mdr_api.domain_repositories.study_definition.study_title.study_title_repository import (
    StudyTitleRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_activity_instruction_repository import (
    StudyActivityInstructionRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_activity_schedule_repository import (
    StudyActivityScheduleRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_compound_dosing_repository import (
    StudyCompoundDosingRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_design_cell_repository import (
    StudyDesignCellRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_epoch_repository import (
    StudyEpochRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_activity_repository import (
    StudySelectionActivityRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_arm_repository import (
    StudySelectionArmRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_branch_arm_repository import (
    StudySelectionBranchArmRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_cohort_repository import (
    StudySelectionCohortRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_compound_repository import (
    StudySelectionCompoundRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_criteria_repository import (
    StudySelectionCriteriaRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_element_repository import (
    StudySelectionElementRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_endpoint_repository import (
    StudySelectionEndpointRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_objective_repository import (
    StudySelectionObjectiveRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_visit_repository import (
    StudyVisitRepository,
)
from clinical_mdr_api.domain_repositories.templates.activity_description_template_repository import (
    ActivityDescriptionTemplateRepository,
)
from clinical_mdr_api.domain_repositories.templates.criteria_template_repository import (
    CriteriaTemplateRepository,
)
from clinical_mdr_api.domain_repositories.templates.endpoint_template_repository import (
    EndpointTemplateRepository,
)
from clinical_mdr_api.domain_repositories.templates.objective_template_repository import (
    ObjectiveTemplateRepository,
)
from clinical_mdr_api.domain_repositories.templates.timeframe_template_repository import (
    TimeframeTemplateRepository,
)


# pylint:disable=too-many-public-methods
class MetaRepository:
    """
    Utility class to provide repository instances and simplify lifecycle management (close) for them.
    It also allows us to define different repositories creation in single piece of code (not spreading out
    all over different services), which is important since we do not have any dependency injection framework in place.
    This serves are poor man's dependency injection framework for domain repositories implementations.
    """

    _repositories: MutableMapping[type, Any]

    # service instance specific variables needed for repository creation
    _user: str

    def __init__(self, user: str = "TODO Initials"):
        self._user = user
        self._repositories = {}

    def close(self) -> None:
        for repo in self._repositories.values():
            repo.close()
        self._repositories = {}

    def __del__(self):
        self.close()

    def _build_repository_instance(self, repo_interface: type) -> Any:
        """
        here we put code for build different repo classes.
        :param repo_interface: An interface to retrieve a configured implementation.
        :return:
        """

        # below you configure implementations for various repository interfaces
        # it's a dictionary which maps interface type, to (no param) Callable which creates a new instance
        # of implementing class
        repository_configuration: Mapping[type, Callable[[], Any]] = {
            StudyDefinitionRepository: lambda: StudyDefinitionRepositoryImpl(self._user)
        }

        if repo_interface not in repository_configuration:
            raise NotImplementedError(
                f"This class does not know how to provide {repo_interface} implementation."
            )

        return repository_configuration[repo_interface]()

    def get_repository_instance(self, repo_interface: type) -> Any:
        if repo_interface not in self._repositories:
            self._repositories[repo_interface] = self._build_repository_instance(
                repo_interface
            )
        return self._repositories[repo_interface]

    # convenience properties for retrieving repository instances

    @property
    def activity_instance_repository(self) -> ActivityInstanceRepository:
        return ActivityInstanceRepository()

    @property
    def reminder_repository(self) -> ReminderRepository:
        return ReminderRepository()

    @property
    def compound_dosing_repository(self) -> CompoundDosingRepository:
        return CompoundDosingRepository()

    @property
    def compound_repository(self) -> CompoundRepository:
        return CompoundRepository()

    @property
    def compound_alias_repository(self) -> CompoundAliasRepository:
        return CompoundAliasRepository()

    @property
    def categoric_finding_repository(self) -> CategoricFindingRepository:
        return CategoricFindingRepository()

    @property
    def numeric_finding_repository(self) -> NumericFindingRepository:
        return NumericFindingRepository()

    @property
    def textual_finding_repository(self) -> TextualFindingRepository:
        return TextualFindingRepository()

    @property
    def rating_scale_repository(self) -> RatingScaleRepository:
        return RatingScaleRepository()

    @property
    def laboratory_activity_repository(self) -> LaboratoryActivityRepository:
        return LaboratoryActivityRepository()

    @property
    def special_purpose_repository(self) -> SpecialPurposeRepository:
        return SpecialPurposeRepository()

    @property
    def event_repository(self) -> EventRepository:
        return EventRepository()

    @property
    def activity_repository(self) -> ActivityRepository:
        return ActivityRepository()

    @property
    def activity_sub_group_repository(self) -> ActivitySubGroupRepository:
        return ActivitySubGroupRepository()

    @property
    def activity_group_repository(self) -> ActivityGroupRepository:
        return ActivityGroupRepository()

    @property
    def numeric_value_repository(self) -> NumericValueRepository:
        return NumericValueRepository()

    @property
    def numeric_value_with_unit_repository(self) -> NumericValueWithUnitRepository:
        return NumericValueWithUnitRepository()

    @property
    def lag_time_repository(self) -> LagTimeRepository:
        return LagTimeRepository()

    @property
    def text_value_repository(self) -> TextValueRepository:
        return TextValueRepository()

    @property
    def visit_name_repository(self) -> VisitNameRepository:
        return VisitNameRepository()

    @property
    def study_day_repository(self) -> StudyDayRepository:
        return StudyDayRepository()

    @property
    def study_week_repository(self) -> StudyWeekRepository:
        return StudyWeekRepository()

    @property
    def study_duration_days_repository(self) -> StudyDurationDaysRepository:
        return StudyDurationDaysRepository()

    @property
    def study_duration_weeks_repository(self) -> StudyDurationWeeksRepository:
        return StudyDurationWeeksRepository()

    @property
    def time_point_repository(self) -> TimePointRepository:
        return TimePointRepository()

    @property
    def unit_definition_repository(self) -> UnitDefinitionRepository:
        return UnitDefinitionRepository()

    @property
    def odm_method_repository(self) -> MethodRepository:
        return MethodRepository()

    @property
    def odm_condition_repository(self) -> ConditionRepository:
        return ConditionRepository()

    @property
    def odm_formal_expression_repository(self) -> FormalExpressionRepository:
        return FormalExpressionRepository()

    @property
    def odm_form_repository(self) -> FormRepository:
        return FormRepository()

    @property
    def odm_item_group_repository(self) -> ItemGroupRepository:
        return ItemGroupRepository()

    @property
    def odm_item_repository(self) -> ItemRepository:
        return ItemRepository()

    @property
    def odm_template_repository(self) -> TemplateRepository:
        return TemplateRepository()

    @property
    def odm_description_repository(self) -> DescriptionRepository:
        return DescriptionRepository()

    @property
    def odm_alias_repository(self) -> AliasRepository:
        return AliasRepository()

    @property
    def odm_xml_extension_repository(self) -> XmlExtensionRepository:
        return XmlExtensionRepository()

    @property
    def odm_xml_extension_tag_repository(self) -> XmlExtensionTagRepository:
        return XmlExtensionTagRepository()

    @property
    def odm_xml_extension_attribute_repository(self) -> XmlExtensionAttributeRepository:
        return XmlExtensionAttributeRepository()

    @property
    def criteria_repository(self) -> CriteriaRepository:
        return CriteriaRepository()

    @property
    def objective_repository(self) -> ObjectiveRepository:
        return ObjectiveRepository()

    @property
    def endpoint_repository(self) -> EndpointRepository:
        return EndpointRepository()

    @property
    def timeframe_repository(self) -> TimeframeRepository:
        return TimeframeRepository()

    @property
    def parameter_repository(self) -> TemplateParameterRepository:
        return TemplateParameterRepository()

    @property
    def activity_description_template_repository(
        self,
    ) -> ActivityDescriptionTemplateRepository:
        return ActivityDescriptionTemplateRepository(self._user)

    @property
    def criteria_template_repository(self) -> CriteriaTemplateRepository:
        return CriteriaTemplateRepository(self._user)

    @property
    def endpoint_template_repository(self) -> EndpointTemplateRepository:
        return EndpointTemplateRepository(self._user)

    @property
    def objective_template_repository(self) -> ObjectiveTemplateRepository:
        return ObjectiveTemplateRepository(self._user)

    @property
    def timeframe_template_repository(self) -> TimeframeTemplateRepository:
        return TimeframeTemplateRepository(self._user)

    @property
    def library_repository(self) -> LibraryRepository:
        return LibraryRepository()

    @property
    def ct_catalogue_repository(self) -> CTCatalogueRepository:
        return CTCatalogueRepository()

    @property
    def ct_package_repository(self) -> CTPackageRepository:
        return CTPackageRepository()

    @property
    def ct_codelist_name_repository(self) -> CTCodelistNameRepository:
        return CTCodelistNameRepository()

    @property
    def ct_codelist_attribute_repository(self) -> CTCodelistAttributesRepository:
        return CTCodelistAttributesRepository()

    @property
    def ct_codelist_aggregated_repository(self) -> CTCodelistAggregatedRepository:
        return CTCodelistAggregatedRepository()

    @property
    def ct_term_name_repository(self) -> CTTermNameRepository:
        return CTTermNameRepository()

    @property
    def ct_term_attributes_repository(self) -> CTTermAttributesRepository:
        return CTTermAttributesRepository()

    @property
    def ct_term_aggregated_repository(self) -> CTTermAggregatedRepository:
        return CTTermAggregatedRepository()

    @property
    def dictionary_codelist_generic_repository(
        self,
    ) -> DictionaryCodelistGenericRepository:
        return DictionaryCodelistGenericRepository()

    @property
    def dictionary_term_generic_repository(self) -> DictionaryTermGenericRepository:
        return DictionaryTermGenericRepository()

    @property
    def dictionary_term_substance_repository(self) -> DictionaryTermSubstanceRepository:
        return DictionaryTermSubstanceRepository()

    @property
    def study_definition_repository(self) -> StudyDefinitionRepository:
        return self.get_repository_instance(StudyDefinitionRepository)

    @property
    def project_repository(self) -> ProjectRepository:
        return ProjectRepository()

    @property
    def brand_repository(self) -> BrandRepository:
        return BrandRepository()

    @property
    def clinical_programme_repository(self) -> ClinicalProgrammeRepository:
        return ClinicalProgrammeRepository()

    @property
    def simple_terminology_item_repository(self) -> SimpleTerminologyItemRepository:
        return SimpleTerminologyItemRepository()

    @property
    def study_selection_objective_repository(self) -> StudySelectionObjectiveRepository:
        return StudySelectionObjectiveRepository()

    @property
    def study_selection_endpoint_repository(self) -> StudySelectionEndpointRepository:
        return StudySelectionEndpointRepository()

    @property
    def study_selection_compound_repository(self) -> StudySelectionCompoundRepository:
        return StudySelectionCompoundRepository()

    @property
    def study_compound_dosing_repository(self) -> StudyCompoundDosingRepository:
        return StudyCompoundDosingRepository()

    @property
    def study_selection_criteria_repository(self) -> StudySelectionCriteriaRepository:
        return StudySelectionCriteriaRepository()

    @property
    def study_selection_activity_repository(
        self,
    ) -> StudySelectionActivityRepository:
        return StudySelectionActivityRepository()

    @property
    def study_activity_schedule_repository(self) -> StudyActivityScheduleRepository:
        return StudyActivityScheduleRepository()

    @property
    def study_design_cell_repository(self) -> StudyDesignCellRepository:
        return StudyDesignCellRepository()

    @property
    def study_activity_instruction_repository(
        self,
    ) -> StudyActivityInstructionRepository:
        return StudyActivityInstructionRepository()

    @property
    def study_title_repository(self) -> StudyTitleRepository:
        return StudyTitleRepository()

    @property
    def study_epoch_repository(self) -> StudyEpochRepository:
        return StudyEpochRepository(self._user)

    @property
    def study_visit_repository(self) -> StudyVisitRepository:
        return StudyVisitRepository(self._user)

    @property
    def ct_config_repository(self) -> CTConfigRepository:
        return CTConfigRepository(self._user)

    @property
    def study_selection_arm_repository(self) -> StudySelectionArmRepository:
        return StudySelectionArmRepository()

    @property
    def study_selection_element_repository(self) -> StudySelectionElementRepository:
        return StudySelectionElementRepository()

    @property
    def study_selection_branch_arm_repository(
        self,
    ) -> StudySelectionBranchArmRepository:
        return StudySelectionBranchArmRepository()

    @property
    def study_selection_cohort_repository(self) -> StudySelectionCohortRepository:
        return StudySelectionCohortRepository()
