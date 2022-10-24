from typing import Optional

from clinical_mdr_api.domain.concepts.compound import CompoundAR, CompoundVO
from clinical_mdr_api.domain.concepts.concept_base import _AggregateRootType
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.brand import Brand
from clinical_mdr_api.domain_repositories.models.compounds import (
    CompoundRoot,
    CompoundValue,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    LagTimeRoot,
    NumericValueWithUnitRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.project import Project
from clinical_mdr_api.models.compound import Compound


class CompoundRepository(ConceptGenericRepository):
    root_class = CompoundRoot
    value_class = CompoundValue
    return_model = Compound

    def _get_uid_or_none(self, node):
        return node.uid if node is not None else None

    def _create_new_value_node(self, ar: _AggregateRootType) -> VersionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.analyte_number = ar.concept_vo.analyte_number
        value_node.nnc_short_number = ar.concept_vo.nnc_short_number
        value_node.nnc_long_number = ar.concept_vo.nnc_long_number
        value_node.is_sponsor_compound = ar.concept_vo.is_sponsor_compound
        value_node.is_name_inn = ar.concept_vo.is_name_inn
        value_node.save()

        for substance_uid in ar.concept_vo.substance_terms_uids:
            value_node.has_unii_value.connect(
                DictionaryTermRoot.nodes.get(uid=substance_uid)
            )

        for dose_value_uid in ar.concept_vo.dose_values_uids:
            value_node.has_dose_value.connect(
                NumericValueWithUnitRoot.nodes.get(uid=dose_value_uid)
            )

        for strength_value_uid in ar.concept_vo.strength_values_uids:
            value_node.has_strength_value.connect(
                NumericValueWithUnitRoot.nodes.get(uid=strength_value_uid)
            )

        for uid in ar.concept_vo.lag_time_uids:
            value_node.has_lag_time.connect(LagTimeRoot.nodes.get(uid=uid))

        if ar.concept_vo.half_life_uid is not None:
            value_node.has_half_life.connect(
                NumericValueWithUnitRoot.nodes.get(uid=ar.concept_vo.half_life_uid)
            )

        for uid in ar.concept_vo.dose_frequency_uids:
            value_node.has_dose_frequency.connect(CTTermRoot.nodes.get(uid=uid))

        for uid in ar.concept_vo.dosage_form_uids:
            value_node.has_dosage_form.connect(CTTermRoot.nodes.get(uid=uid))

        for uid in ar.concept_vo.route_of_administration_uids:
            value_node.has_route_of_administration.connect(
                CTTermRoot.nodes.get(uid=uid)
            )

        for uid in ar.concept_vo.delivery_devices_uids:
            value_node.has_delivery_device.connect(CTTermRoot.nodes.get(uid=uid))

        for uid in ar.concept_vo.dispensers_uids:
            value_node.has_dispenser.connect(CTTermRoot.nodes.get(uid=uid))

        for uid in ar.concept_vo.projects_uids:
            value_node.has_project.connect(Project.nodes.get(uid=uid))

        for uid in ar.concept_vo.brands_uids:
            value_node.has_brand.connect(Brand.nodes.get(uid=uid))

        return value_node

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:

        was_parent_data_modified = super()._has_data_changed(ar=ar, value=value)

        are_props_changed = (
            ar.concept_vo.analyte_number != value.analyte_number
            or ar.concept_vo.nnc_short_number != value.nnc_short_number
            or ar.concept_vo.nnc_long_number != value.nnc_long_number
            or ar.concept_vo.is_sponsor_compound != value.is_sponsor_compound
            or ar.concept_vo.is_name_inn != value.is_name_inn
        )

        are_rels_changed = (
            sorted(ar.concept_vo.substance_terms_uids)
            != sorted([unii.uid for unii in value.has_unii_value.all()])
            or sorted(ar.concept_vo.dose_values_uids)
            != sorted([val.uid for val in value.has_dose_value.all()])
            or sorted(ar.concept_vo.strength_values_uids)
            != sorted([val.uid for val in value.has_strength_value.all()])
            or sorted(ar.concept_vo.lag_time_uids)
            != sorted([val.uid for val in value.has_lag_time.all()])
            or ar.concept_vo.half_life_uid
            != self._get_uid_or_none(value.has_half_life.get_or_none())
            or sorted(ar.concept_vo.dosage_form_uids)
            != sorted([val.uid for val in value.has_dosage_form.all()])
            or sorted(ar.concept_vo.dose_frequency_uids)
            != sorted([val.uid for val in value.has_dose_frequency.all()])
            or sorted(ar.concept_vo.route_of_administration_uids)
            != sorted([val.uid for val in value.has_route_of_administration.all()])
            or sorted(ar.concept_vo.delivery_devices_uids)
            != sorted([val.uid for val in value.has_delivery_device.all()])
            or sorted(ar.concept_vo.dispensers_uids)
            != sorted([val.uid for val in value.has_dispenser.all()])
            or sorted(ar.concept_vo.projects_uids)
            != sorted([val.uid for val in value.has_project.all()])
            or sorted(ar.concept_vo.brands_uids)
            != sorted([val.uid for val in value.has_brand.all()])
        )

        return was_parent_data_modified or are_props_changed or are_rels_changed

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> CompoundAR:
        major, minor = input_dict.get("version").split(".")
        return CompoundAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=CompoundVO.from_repository_values(
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("nameSentenceCase"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                dose_frequency_uids=list(
                    map(lambda x: x.get("uid"), input_dict.get("doseFrequencies"))
                ),
                dosage_form_uids=list(
                    map(lambda x: x.get("uid"), input_dict.get("dosageForms"))
                ),
                route_of_administration_uids=list(
                    map(
                        lambda x: x.get("uid"),
                        input_dict.get("routesOfAdministration"),
                    )
                ),
                half_life_uid=input_dict.get("halfLife"),
                analyte_number=input_dict.get("analyteNumber"),
                nnc_short_number=input_dict.get("nncShortNumber"),
                nnc_long_number=input_dict.get("nncLongNumber"),
                is_sponsor_compound=input_dict.get("isSponsorCompound"),
                is_name_inn=input_dict.get("isNameInn"),
                substance_terms_uids=input_dict.get("substanceTermsUids"),
                dose_values_uids=input_dict.get("doseValuesUids"),
                strength_values_uids=input_dict.get("strengthValuesUids"),
                lag_time_uids=input_dict.get("lagTimesUids"),
                delivery_devices_uids=list(
                    map(lambda x: x.get("uid"), input_dict.get("deliveryDevices"))
                ),
                dispensers_uids=list(
                    map(lambda x: x.get("uid"), input_dict.get("dispensers"))
                ),
                projects_uids=input_dict.get("projectsUids"),
                brands_uids=input_dict.get("brandsUids"),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("libraryName"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("changeDescription"),
                status=LibraryItemStatus(input_dict.get("status")),
                author=input_dict.get("userInitials"),
                start_date=convert_to_datetime(value=input_dict.get("startDate")),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Optional[Library],
        relationship: VersionRelationship,
        value: VersionValue,
    ) -> CompoundAR:

        return CompoundAR.from_repository_values(
            uid=root.uid,
            concept_vo=CompoundVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
                half_life_uid=self._get_uid_or_none(value.has_half_life.get_or_none()),
                analyte_number=value.analyte_number,
                nnc_short_number=value.nnc_short_number,
                nnc_long_number=value.nnc_long_number,
                is_sponsor_compound=value.is_sponsor_compound,
                is_name_inn=value.is_name_inn,
                substance_terms_uids=[unii.uid for unii in value.has_unii_value.all()],
                dose_values_uids=[
                    dose_value.uid for dose_value in value.has_dose_value.all()
                ],
                strength_values_uids=[
                    strength_value.uid
                    for strength_value in value.has_strength_value.all()
                ],
                lag_time_uids=[x.uid for x in value.has_lag_time.all()],
                dose_frequency_uids=[x.uid for x in value.has_dose_frequency.all()],
                dosage_form_uids=[x.uid for x in value.has_dosage_form.all()],
                route_of_administration_uids=[
                    x.uid for x in value.has_route_of_administration.all()
                ],
                delivery_devices_uids=[x.uid for x in value.has_delivery_device.all()],
                dispensers_uids=[x.uid for x in value.has_dispenser.all()],
                projects_uids=[x.uid for x in value.has_project.all()],
                brands_uids=[x.uid for x in value.has_brand.all()],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def specific_alias_clause(self) -> str:
        return """
            WITH *,            
                [(concept_value)-[:HAS_DOSE_FREQUENCY]->(dose_frequency:CTTermRoot) | dose_frequency] AS doseFrequencies,
                [(concept_value)-[:HAS_DOSAGE_FORM]->(dosage_form:CTTermRoot) | dosage_form] AS dosageForms,
                [(concept_value)-[:HAS_ROUTE_OF_ADMINISTRATION]->(route_of_administration:CTTermRoot) | route_of_administration] AS routesOfAdministration,
                head([(concept_value)-[:HAS_HALF_LIFE]->(half_life:NumericValueWithUnitRoot) | half_life.uid]) AS halfLife,
                concept_value.analyte_number AS analyteNumber,
                concept_value.nnc_short_number AS nncShortNumber,
                concept_value.nnc_long_number AS nncLongNumber,
                concept_value.is_sponsor_compound AS isSponsorCompound,
                concept_value.is_name_inn AS isNameInn,
                [(concept_value)-[:HAS_UNII_VALUE]->(unii:DictionaryTermRoot) | unii.uid] AS substanceTermsUids,
                [(concept_value)-[:HAS_UNII_VALUE]->(unii:DictionaryTermRoot)-[:LATEST]->(unii_value:DictionaryTermValue) | unii_value.name] AS substances,
                [(concept_value)-[:HAS_UNII_VALUE]->(unii:DictionaryTermRoot)-[:LATEST]->(unii_value:DictionaryTermValue)-[:HAS_PCLASS]->(pclass_root:DictionaryTermRoot)-[:LATEST]->(pclass_value:DictionaryTermValue) | pclass_value.name] AS pharmacologicalClasses,
                [(concept_value)-[:HAS_DELIVERY_DEVICE]->(delivery_device:CTTermRoot) | delivery_device] AS deliveryDevices,
                [(concept_value)-[:HAS_DISPENSER]->(dispenser:CTTermRoot) | dispenser] AS dispensers,
                [(concept_value)-[:HAS_DOSE_VALUE]->(dose_value_root:NumericValueWithUnitRoot) | dose_value_root.uid] AS doseValuesUids,
                [(concept_value)-[:HAS_DOSE_VALUE]->(dose_value_root:NumericValueWithUnitRoot)-[:LATEST]->(dose_value_value:NumericValueWithUnitValue) | dose_value_value.value] AS doseValues,
                [(concept_value)-[:HAS_STRENGTH_VALUE]->(strength_value_root:NumericValueWithUnitRoot) | strength_value_root.uid] AS strengthValuesUids,
                [(concept_value)-[:HAS_STRENGTH_VALUE]->(strength_value_root:NumericValueWithUnitRoot)-[:LATEST]->(strength_value_value:NumericValueWithUnitValue) | strength_value_value.value] AS strengthValues,
                [(concept_value)-[:HAS_LAG_TIME]->(lag_time_root:LagTimeRoot) | lag_time_root.uid] AS lagTimesUids,
                [(concept_value)-[:HAS_LAG_TIME]->(lag_time_root:LagTimeRoot)-[:LATEST]->(lag_time_value:LagTimeValue) | lag_time_value.value] AS lagTimes,
                [(concept_value)-[:HAS_PROJECT]->(project:Project) | project.uid] AS projectsUids,
                [(concept_value)-[:HAS_BRAND]->(brand:Brand) | brand.uid] AS brandsUids,
                [(concept_value)-[:HAS_BRAND]->(brand:Brand) | brand.name] AS brands
            """
