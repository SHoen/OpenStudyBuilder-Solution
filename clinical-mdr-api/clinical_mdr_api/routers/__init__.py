from clinical_mdr_api.routers.activities import router as activities_router
from clinical_mdr_api.routers.activity_description_templates import (
    router as activity_description_templates_router,
)
from clinical_mdr_api.routers.activity_groups import router as activity_groups_router
from clinical_mdr_api.routers.activity_instances import (
    router as activity_instances_router,
)
from clinical_mdr_api.routers.activity_sub_groups import (
    router as activity_sub_groups_router,
)
from clinical_mdr_api.routers.admin import router as admin_router
from clinical_mdr_api.routers.brands import router as brands_router
from clinical_mdr_api.routers.categoric_findings import (
    router as categoric_finding_router,
)
from clinical_mdr_api.routers.clinical_programmes import (
    router as clinical_programmes_router,
)
from clinical_mdr_api.routers.complex_template_parameter_templates import (
    router as complex_template_parameter_router,
)
from clinical_mdr_api.routers.compound_aliases import router as compound_aliases_router
from clinical_mdr_api.routers.compound_dosings import router as compound_dosings_router
from clinical_mdr_api.routers.compounds import router as compounds_router
from clinical_mdr_api.routers.configuration import router as configuration_router
from clinical_mdr_api.routers.criteria import router as criteria_router
from clinical_mdr_api.routers.criteria_templates import (
    router as criteria_templates_router,
)
from clinical_mdr_api.routers.ct_catalogues import router as ct_catalogues_router
from clinical_mdr_api.routers.ct_codelist_attributes import (
    router as ct_codelist_attributes_router,
)
from clinical_mdr_api.routers.ct_codelist_names import (
    router as ct_codelist_names_router,
)
from clinical_mdr_api.routers.ct_codelists import router as ct_codelists_router
from clinical_mdr_api.routers.ct_packages import router as ct_packages_router
from clinical_mdr_api.routers.ct_stats import router as ct_stats_router
from clinical_mdr_api.routers.ct_term_attributes import (
    router as ct_term_attributes_router,
)
from clinical_mdr_api.routers.ct_term_names import router as ct_term_names_router
from clinical_mdr_api.routers.ct_terms import router as ct_terms_router
from clinical_mdr_api.routers.dictionary_codelists import (
    router as dictionary_codelists_router,
)
from clinical_mdr_api.routers.dictionary_terms import router as dictionary_terms_router
from clinical_mdr_api.routers.endpoint_templates import (
    router as endpoint_templates_router,
)
from clinical_mdr_api.routers.endpoints import router as endpoints_router
from clinical_mdr_api.routers.events import router as events_router
from clinical_mdr_api.routers.laboratory_activities import (
    router as laboratory_activities_router,
)
from clinical_mdr_api.routers.lag_times import router as lag_times_router
from clinical_mdr_api.routers.libraries import router as libraries_router
from clinical_mdr_api.routers.listings import metadata_router
from clinical_mdr_api.routers.listings import router as listing_router
from clinical_mdr_api.routers.listings_sdtm import router as sdtm_listing_router
from clinical_mdr_api.routers.listings_study import router as study_listing_router
from clinical_mdr_api.routers.numeric_findings import router as numeric_findings_router
from clinical_mdr_api.routers.numeric_values import router as numeric_values_router
from clinical_mdr_api.routers.numeric_values_with_unit import (
    router as numeric_values_with_unit_router,
)
from clinical_mdr_api.routers.objective_templates import (
    router as objective_templates_router,
)
from clinical_mdr_api.routers.objectives import router as objectives_router
from clinical_mdr_api.routers.odm_aliases import router as odm_aliases_router
from clinical_mdr_api.routers.odm_conditions import router as odm_conditions_router
from clinical_mdr_api.routers.odm_descriptions import router as odm_descriptions_router
from clinical_mdr_api.routers.odm_formal_expressions import (
    router as odm_formal_expressions_router,
)
from clinical_mdr_api.routers.odm_forms import router as odm_forms_router
from clinical_mdr_api.routers.odm_item_groups import router as odm_item_groups_router
from clinical_mdr_api.routers.odm_items import router as odm_item_router
from clinical_mdr_api.routers.odm_metadata import router as odm_metadata_router
from clinical_mdr_api.routers.odm_methods import router as odm_methods_router
from clinical_mdr_api.routers.odm_templates import router as odm_templates_router
from clinical_mdr_api.routers.odm_xml_extension_attributes import (
    router as odm_xml_extension_attribute_router,
)
from clinical_mdr_api.routers.odm_xml_extension_tags import (
    router as odm_xml_extension_tag_router,
)
from clinical_mdr_api.routers.odm_xml_extensions import (
    router as odm_xml_extension_router,
)
from clinical_mdr_api.routers.projects import router as projects_router
from clinical_mdr_api.routers.rating_scales import router as rating_scales_router
from clinical_mdr_api.routers.reminders import router as reminders_router
from clinical_mdr_api.routers.special_purposes import router as special_purposes_router
from clinical_mdr_api.routers.studies import router as studies_router
from clinical_mdr_api.routers.study import router as study_router
from clinical_mdr_api.routers.study_activity_instructions import (
    router as study_activity_instructions_router,
)
from clinical_mdr_api.routers.study_activity_schedule import (
    router as study_activity_schedule_router,
)
from clinical_mdr_api.routers.study_compound_dosing import (
    router as study_compound_dosing_router,
)
from clinical_mdr_api.routers.study_days import router as study_days_router
from clinical_mdr_api.routers.study_design_cell import (
    router as study_design_cell_router,
)
from clinical_mdr_api.routers.study_design_figure import router as study_design_figure
from clinical_mdr_api.routers.study_duration_days import (
    router as study_duration_days_router,
)
from clinical_mdr_api.routers.study_duration_weeks import (
    router as study_duration_weeks_router,
)
from clinical_mdr_api.routers.study_epochs import router as study_epoch_router
from clinical_mdr_api.routers.study_flowchart import router as study_flowchart_router
from clinical_mdr_api.routers.study_interventions import (
    router as study_interventions_router,
)
from clinical_mdr_api.routers.study_visits import router as study_visit_router
from clinical_mdr_api.routers.study_weeks import router as study_weeks_router
from clinical_mdr_api.routers.system import router as system_router
from clinical_mdr_api.routers.template_parameters import (
    router as template_parameters_router,
)
from clinical_mdr_api.routers.text_values import router as text_values_router
from clinical_mdr_api.routers.textual_findings import router as textual_findings_router
from clinical_mdr_api.routers.time_points import router as time_points_router
from clinical_mdr_api.routers.timeframe_templates import (
    router as timeframe_templates_router,
)
from clinical_mdr_api.routers.timeframes import router as timeframes_router
from clinical_mdr_api.routers.unit_definitions import router as unit_definition_router
from clinical_mdr_api.routers.visit_names import router as visit_names_router

__all__ = [
    "activities_router",
    "odm_templates_router",
    "odm_forms_router",
    "odm_item_groups_router",
    "odm_item_router",
    "odm_conditions_router",
    "odm_methods_router",
    "odm_formal_expressions_router",
    "odm_descriptions_router",
    "odm_aliases_router",
    "odm_xml_extension_router",
    "odm_xml_extension_tag_router",
    "odm_xml_extension_attribute_router",
    "activity_instances_router",
    "odm_metadata_router",
    "reminders_router",
    "compound_dosings_router",
    "compounds_router",
    "compound_aliases_router",
    "special_purposes_router",
    "categoric_finding_router",
    "rating_scales_router",
    "laboratory_activities_router",
    "numeric_findings_router",
    "textual_findings_router",
    "events_router",
    "activity_sub_groups_router",
    "activity_groups_router",
    "numeric_values_router",
    "numeric_values_with_unit_router",
    "lag_times_router",
    "text_values_router",
    "time_points_router",
    "libraries_router",
    "ct_catalogues_router",
    "ct_packages_router",
    "ct_codelists_router",
    "ct_codelist_names_router",
    "ct_codelist_attributes_router",
    "ct_terms_router",
    "ct_term_names_router",
    "ct_term_attributes_router",
    "ct_stats_router",
    "dictionary_codelists_router",
    "dictionary_terms_router",
    "activity_description_templates_router",
    "criteria_templates_router",
    "criteria_router",
    "objective_templates_router",
    "objectives_router",
    "template_parameters_router",
    "endpoint_templates_router",
    "endpoints_router",
    "projects_router",
    "brands_router",
    "admin_router",
    "clinical_programmes_router",
    "studies_router",
    "system_router",
    "timeframe_templates_router",
    "timeframes_router",
    "study_router",
    "study_epoch_router",
    "study_visit_router",
    "study_activity_instructions_router",
    "study_activity_schedule_router",
    "study_design_cell_router",
    "study_duration_days_router",
    "study_duration_weeks_router",
    "study_days_router",
    "study_weeks_router",
    "metadata_router",
    "listing_router",
    "sdtm_listing_router",
    "study_listing_router",
    "unit_definition_router",
    "complex_template_parameter_router",
    "configuration_router",
    "study_design_figure",
    "study_interventions_router",
    "study_flowchart_router",
    "study_compound_dosing_router",
    "visit_names_router",
]
