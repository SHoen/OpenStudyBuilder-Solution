from datetime import datetime
from typing import Iterable, MutableSet, Optional, Sequence, Tuple
from unittest.mock import Mock, PropertyMock, patch

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis.strategies import (
    booleans,
    composite,
    datetimes,
    lists,
    none,
    one_of,
    sampled_from,
)

# noinspection PyProtectedMember
from clinical_mdr_api.domain._utils import normalize_string
from clinical_mdr_api.domain.library.library_ar import LibraryAR
from clinical_mdr_api.domain.unit_definition.unit_definition import (
    CONCENTRATION_UNIT_DIMENSION_VALUE,
    UnitDefinitionAR,
    UnitDefinitionValueVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.domain_repositories.concepts.unit_definition.unit_definition_repository import (
    UnitDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.library.library_repository import (
    LibraryRepository,
)
from clinical_mdr_api.exceptions import NotFoundException, ValidationException
from clinical_mdr_api.models.ct_term import SimpleTermModel
from clinical_mdr_api.models.unit_definition import (
    UnitDefinitionModel,
    UnitDefinitionPatchInput,
    UnitDefinitionPostInput,
)
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.unit_definition import UnitDefinitionService
from clinical_mdr_api.tests.unit.domain.unit_definition.test_unit_definition import (
    draft_unit_definitions,
    final_unit_definitions,
    get_mock_ct_item,
    get_mock_dictionary_item,
    retired_unit_definitions,
    unit_definition_values,
    unit_definitions,
)
from clinical_mdr_api.tests.utils.common_strategies import (
    strings_with_at_least_one_non_space_char,
    stripped_non_empty_strings,
)


class UnitDefinitionRepositoryFakeBase(UnitDefinitionRepository):

    verified_names: MutableSet[str]
    verified_dimensions: MutableSet[str]
    verified_legacy_codes: MutableSet[str]
    verified_unit_ct_uids: MutableSet[str]
    saved_item: Optional[UnitDefinitionAR]

    def __init__(self):
        self.verified_names = set()
        self.verified_dimensions = set()
        self.verified_legacy_codes = set()
        self.verified_unit_ct_uids = set()
        self.saved_item = None

    def exists_by_unit_ct_uid(self, unit_ct_uid: str) -> bool:
        self.verified_unit_ct_uids.add(unit_ct_uid)
        return False

    def exists_by_legacy_code(self, legacy_code: str) -> bool:
        self.verified_legacy_codes.add(legacy_code)
        return False

    def check_exists_by_name(self, name: str) -> bool:
        self.verified_names.add(name)
        return False

    def check_exists_final_version(self, uid: str) -> bool:
        raise NotImplementedError

    def master_unit_exists_by_unit_dimension(self, unit_dimension: str) -> bool:
        self.verified_dimensions.add(unit_dimension)
        return False

    #  pylint: disable=unused-argument
    def find_all(
        self,
        library: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
        **kwargs,
    ) -> Tuple[Sequence, int]:
        raise AssertionError("Call not expected")

    def find_releases_referenced_by_any_study(self) -> Iterable[UnitDefinitionAR]:
        return AssertionError("Call not expected")

    def find_releases(
        self, uid: str, return_study_count: Optional[bool] = True
    ) -> Iterable[UnitDefinitionAR]:
        raise AssertionError("Call not expected")

    def find_by_uid_2(
        self,
        uid: str,
        *,
        version: Optional[str] = None,
        status: Optional[LibraryItemStatus] = None,
        at_specific_date: Optional[datetime] = None,
        for_update: bool = False,
    ) -> Optional[UnitDefinitionAR]:
        raise AssertionError("Call not expected")

    def save(self, item: UnitDefinitionAR) -> None:
        assert self.saved_item is None, "save called twice"
        self.verified_unit_ct_uids.update(
            [ct_unit.uid for ct_unit in item.concept_vo.ct_units]
        )
        self.saved_item = item

    @property
    def user_initials(self) -> Optional[str]:
        raise AssertionError("Call not expected")

    def generate_uid_callback(self) -> Optional[str]:
        raise AssertionError("Call not expected")

    def get_all_versions_2(self, uid: str) -> Iterable[UnitDefinitionAR]:
        raise AssertionError("Call not expected")

    def check_usage_count(self, uid: str) -> int:
        raise AssertionError("Call not expected")

    def close(self) -> None:
        raise AssertionError("Call not expected")


class LibraryRepositoryFakeBase(LibraryRepository):
    def find_by_name(self, name: str) -> Optional[LibraryAR]:
        raise AssertionError("Call not expected")

    def library_exists(self, library_name: str) -> bool:
        raise AssertionError("Call not expected")


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    find_all_result=lists(unit_definitions(), max_size=10),
    a_library_name=one_of(none(), stripped_non_empty_strings()),
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition__get_all__library_name__result(
    unit_definition_repository_property_mock: PropertyMock,
    find_all_result: Sequence[UnitDefinitionAR],
    a_library_name: Optional[str],
):
    # given
    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):
        def find_all(
            self,
            *,
            library: Optional[str] = None,
            sort_by: Optional[dict] = None,
            page_number: int = 1,
            page_size: int = 0,
            filter_by: Optional[dict] = None,
            filter_operator: Optional[FilterOperator] = FilterOperator.AND,
            total_count: bool = False,
            **kwargs,
        ) -> Tuple[Sequence, int]:
            # pylint: disable=unused-argument
            assert library == a_library_name
            return find_all_result, 0

    unit_definition_repository_property_mock.return_value = (
        UnitDefinitionRepositoryFake()
    )
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # when
    service_result = service.get_all(library_name=a_library_name)

    # then
    assert list(service_result.items) == [
        UnitDefinitionModel.from_unit_definition_ar(
            _,
            find_term_by_uid=lambda _: None,
            find_dictionary_term_by_uid=lambda _: None,
        )
        for _ in find_all_result
    ]


@settings(max_examples=int(max(10, settings.default.max_examples / 5)), deadline=None)
@given(
    find_by_uid_result=unit_definitions(),
    a_version=one_of(none(), stripped_non_empty_strings()),
    a_status=sampled_from(["Draft", "Final", "Retired", None]),
    a_at_specified_date=one_of(none(), datetimes()),
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.ct_term_name_repository",
    new_callable=Mock,
)
@patch(
    UnitDefinitionService.__module__
    + ".MetaRepository.dictionary_term_generic_repository",
    new_callable=Mock,
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition__get_by_uid__existing__result(
    unit_definition_repository_property_mock: PropertyMock,
    dictionary_term_repository_property_mock: PropertyMock,
    ct_term_name_repository_property_mock: PropertyMock,
    find_by_uid_result: UnitDefinitionAR,
    a_version: Optional[str],
    a_status: Optional[str],
    a_at_specified_date: Optional[datetime],
):
    # given
    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):
        def find_by_uid_2(
            self,
            uid: str,
            *,
            version: Optional[str] = None,
            status: Optional[LibraryItemStatus] = None,
            at_specific_date: Optional[datetime] = None,
            for_update: bool = False,
        ) -> Optional[UnitDefinitionAR]:
            assert uid == find_by_uid_result.uid
            assert version == a_version
            assert (
                a_status is None
                and status is None
                or a_status is not None
                and status == LibraryItemStatus(a_status)
            )
            assert at_specific_date == a_at_specified_date
            assert not for_update
            return find_by_uid_result

    unit_definition_repository_property_mock.return_value = (
        UnitDefinitionRepositoryFake()
    )
    dictionary_term_repository_property_mock.find_by_uid.return_value = None
    ct_term_name_repository_property_mock.find_by_uid.return_value = None
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # when
    service_result = service.get_by_uid(
        uid=find_by_uid_result.uid,
        at_specified_datetime=a_at_specified_date,
        status=a_status,
        version=a_version,
    )

    # then
    assert service_result == UnitDefinitionModel.from_unit_definition_ar(
        find_by_uid_result,
        find_term_by_uid=lambda _: None,
        find_dictionary_term_by_uid=lambda _: None,
    )


@settings(max_examples=int(max(10, settings.default.max_examples / 5)), deadline=None)
@given(
    a_uid=stripped_non_empty_strings(),
    a_version=one_of(none(), stripped_non_empty_strings()),
    a_status=sampled_from(["Draft", "Final", "Retired", None]),
    a_at_specified_date=one_of(none(), datetimes()),
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition__get_by_uid__non_existing__result(
    unit_definition_repository_property_mock: PropertyMock,
    a_uid: str,
    a_version: Optional[str],
    a_status: Optional[str],
    a_at_specified_date: Optional[datetime],
):
    # given
    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):
        def find_by_uid_2(
            self,
            uid: str,
            *,
            version: Optional[str] = None,
            status: Optional[LibraryItemStatus] = None,
            at_specific_date: Optional[datetime] = None,
            for_update: bool = False,
        ) -> Optional[UnitDefinitionAR]:
            assert uid == a_uid
            assert version == a_version
            assert (
                a_status is None
                and status is None
                or a_status is not None
                and status == LibraryItemStatus(a_status)
            )
            assert at_specific_date == a_at_specified_date
            assert not for_update

    unit_definition_repository_property_mock.return_value = (
        UnitDefinitionRepositoryFake()
    )
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # then
    with pytest.raises(NotFoundException):
        # when
        service.get_by_uid(
            uid=a_uid,
            at_specified_datetime=a_at_specified_date,
            status=a_status,
            version=a_version,
        )


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    assumed_repository_get_versions_result=lists(
        unit_definitions(), min_size=1, max_size=10
    ),
    a_uid=stripped_non_empty_strings(),
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition__get_versions__existing_uid__result(
    unit_definition_repository_property_mock: PropertyMock,
    assumed_repository_get_versions_result: Sequence[UnitDefinitionAR],
    a_uid: str,
):
    # given
    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):
        def get_all_versions_2(self, uid: str) -> Iterable[UnitDefinitionAR]:
            assert uid == a_uid
            return assumed_repository_get_versions_result

    unit_definition_repository_property_mock.return_value = (
        UnitDefinitionRepositoryFake()
    )
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # when
    service_result = service.get_versions(uid=a_uid)

    # then
    assert list(service_result) == [
        UnitDefinitionModel.from_unit_definition_ar(
            _,
            find_term_by_uid=lambda _: None,
            find_dictionary_term_by_uid=lambda _: None,
        )
        for _ in assumed_repository_get_versions_result
    ]


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(a_uid=stripped_non_empty_strings())
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition__get_versions__non_existing_uid__result(
    unit_definition_repository_property_mock: PropertyMock, a_uid: str
):
    # given
    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):
        def get_all_versions_2(self, uid: str) -> Iterable[UnitDefinitionAR]:
            assert uid == a_uid
            return []

    unit_definition_repository_property_mock.return_value = (
        UnitDefinitionRepositoryFake()
    )
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # then
    with pytest.raises(NotFoundException):
        # when
        service.get_versions(uid=a_uid)


@composite
def unit_definition_post_inputs(draw):
    unit_definition_value: UnitDefinitionValueVO = draw(unit_definition_values())
    return UnitDefinitionPostInput(
        name=unit_definition_value.name,
        ctUnits=[ct_unit.uid for ct_unit in unit_definition_value.ct_units],
        unitSubsets=[
            unit_subset.uid for unit_subset in unit_definition_value.unit_subsets
        ],
        convertibleUnit=unit_definition_value.convertible_unit,
        displayUnit=unit_definition_value.display_unit,
        masterUnit=unit_definition_value.master_unit,
        siUnit=unit_definition_value.si_unit,
        usConventionalUnit=unit_definition_value.us_conventional_unit,
        unitDimension=unit_definition_value.unit_dimension_uid,
        legacyCode=unit_definition_value.legacy_code,
        molecularWeightConvExpon=unit_definition_value.molecular_weight_conv_expon,
        libraryName=draw(stripped_non_empty_strings()),
        conversionFactorToMaster=unit_definition_value.conversion_factor_to_master,
        ucum=unit_definition_value.ucum_uid,
        definition=unit_definition_value.definition,
        order=unit_definition_value.order,
        comment=unit_definition_value.comment,
    )


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(unit_definition_post_input=unit_definition_post_inputs())
@patch(UnitDefinitionService.__module__ + ".MetaRepository.ct_term_name_repository")
@patch(
    UnitDefinitionService.__module__
    + ".MetaRepository.dictionary_term_generic_repository"
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.library_repository",
    new_callable=PropertyMock,
)
def test__unit_definition_service__post__result(
    library_repository_property_mock: PropertyMock,
    unit_definition_repository_property_mock: PropertyMock,
    dictionary_term_repository_property_mock: PropertyMock,
    ct_term_name_repository_property_mock: PropertyMock,
    unit_definition_post_input: UnitDefinitionPostInput,
):
    # given

    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):
        pass

    class LibraryRepositoryFake(LibraryRepositoryFakeBase):
        def find_by_name(self, name: str) -> Optional[LibraryAR]:
            assert name == unit_definition_post_input.libraryName
            return LibraryAR.from_repository_values(
                library_name=unit_definition_post_input.libraryName, is_editable=True
            )

        def library_exists(self, library_name: str) -> bool:
            assert library_name == unit_definition_post_input.libraryName
            return True

    repo_fake = UnitDefinitionRepositoryFake()
    unit_definition_repository_property_mock.return_value = repo_fake
    library_repository_property_mock.return_value = LibraryRepositoryFake()
    dictionary_term_repository_property_mock.find_by_uid.return_value = None
    dictionary_term_repository_property_mock.term_exists.return_value = True
    ct_term_name_repository_property_mock.find_by_uid.return_value = get_mock_ct_item(
        unit_definition_post_input.unitDimension
    )
    ct_term_name_repository_property_mock.term_exists = lambda _: True
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # when
    service_result = service.post(unit_definition_post_input)

    # then
    item = repo_fake.saved_item
    assert item is not None
    assert item.uid is not None
    assert item.concept_vo == UnitDefinitionValueVO.from_input_values(
        name=unit_definition_post_input.name,
        ct_units=unit_definition_post_input.ctUnits,
        unit_subsets=unit_definition_post_input.unitSubsets,
        convertible_unit=unit_definition_post_input.convertibleUnit,
        display_unit=unit_definition_post_input.displayUnit,
        master_unit=unit_definition_post_input.masterUnit,
        si_unit=unit_definition_post_input.siUnit,
        us_conventional_unit=unit_definition_post_input.usConventionalUnit,
        unit_dimension_uid=unit_definition_post_input.unitDimension,
        legacy_code=unit_definition_post_input.legacyCode,
        molecular_weight_conv_expon=unit_definition_post_input.molecularWeightConvExpon,
        conversion_factor_to_master=unit_definition_post_input.conversionFactorToMaster,
        unit_ct_uid_exists_callback=lambda _: True,
        ucum_uid_exists_callback=lambda _: True,
        find_term_by_uid=lambda _: get_mock_ct_item(
            unit_definition_post_input.unitDimension
        ),
        ucum_uid=unit_definition_post_input.ucum,
        definition=unit_definition_post_input.definition,
        order=unit_definition_post_input.order,
        comment=unit_definition_post_input.comment,
        is_template_parameter=False,
    )
    assert service_result == UnitDefinitionModel.from_unit_definition_ar(
        item,
        find_term_by_uid=lambda _: get_mock_ct_item(
            unit_definition_post_input.unitDimension
        ),
        find_dictionary_term_by_uid=lambda _: None,
    )

    assert repo_fake.verified_names == {unit_definition_post_input.name}
    assert repo_fake.verified_unit_ct_uids == {
        _ for _ in unit_definition_post_input.ctUnits if _ is not None
    }
    assert repo_fake.verified_legacy_codes == {
        _ for _ in [unit_definition_post_input.legacyCode] if _ is not None
    }

    assert repo_fake.verified_dimensions == {
        _.unitDimension
        for _ in [unit_definition_post_input]
        if _.unitDimension is not None and _.masterUnit
    }


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(unit_definition_post_input=unit_definition_post_inputs())
@patch(UnitDefinitionService.__module__ + ".MetaRepository.ct_term_name_repository")
@patch(
    UnitDefinitionService.__module__
    + ".MetaRepository.dictionary_term_generic_repository"
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.library_repository",
    new_callable=PropertyMock,
)
def test__unit_definition_service__post_with_non_unique_name__result(
    library_repository_property_mock: PropertyMock,
    unit_definition_repository_property_mock: PropertyMock,
    dictionary_term_repository_property_mock: PropertyMock,
    ct_term_name_repository_property_mock: PropertyMock,
    unit_definition_post_input: UnitDefinitionPostInput,
):
    # given

    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):
        def check_exists_by_name(self, name: str) -> bool:
            return super().check_exists_by_name(name) or True

    class LibraryRepositoryFake(LibraryRepositoryFakeBase):
        def find_by_name(self, name: str) -> Optional[LibraryAR]:
            assert name == unit_definition_post_input.libraryName
            return LibraryAR.from_repository_values(
                library_name=unit_definition_post_input.libraryName, is_editable=True
            )

        def library_exists(self, library_name: str) -> bool:
            assert library_name == unit_definition_post_input.libraryName
            return True

    repo_fake = UnitDefinitionRepositoryFake()
    unit_definition_repository_property_mock.return_value = repo_fake
    library_repository_property_mock.return_value = LibraryRepositoryFake()
    dictionary_term_repository_property_mock.term_exists.return_value = True
    ct_term_name_repository_property_mock.term_exists.return_value = True
    dictionary_term_repository_property_mock.find_by_uid.return_value = (
        get_mock_dictionary_item(unit_definition_post_input.ucum)
    )
    ct_term_name_repository_property_mock.find_by_uid.return_value = get_mock_ct_item(
        unit_definition_post_input.unitDimension
    )
    # get_mock_ct_item(unit_definition_post_input.unitDimension)
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # when
    with pytest.raises(ValidationException):
        service.post(unit_definition_post_input)

    # then
    assert repo_fake.verified_names == {unit_definition_post_input.name}


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_post_input=unit_definition_post_inputs().filter(
        lambda x: x.legacyCode is not None
    )
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.ct_term_name_repository",
    new_callable=PropertyMock,
)
@patch(
    UnitDefinitionService.__module__
    + ".MetaRepository.dictionary_term_generic_repository",
    new_callable=PropertyMock,
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.library_repository",
    new_callable=PropertyMock,
)
def test__unit_definition_service__post_with_non_unique_legacy_code__result(
    library_repository_property_mock: PropertyMock,
    unit_definition_repository_property_mock: PropertyMock,
    dictionary_term_repository_property_mock: PropertyMock,
    ct_term_name_repository_property_mock: PropertyMock,
    unit_definition_post_input: UnitDefinitionPostInput,
):
    # given

    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):
        def exists_by_legacy_code(self, legacy_code: str) -> bool:
            return super().exists_by_legacy_code(legacy_code) or True

    class LibraryRepositoryFake(LibraryRepositoryFakeBase):
        def find_by_name(self, name: str) -> Optional[LibraryAR]:
            assert name == unit_definition_post_input.libraryName
            return LibraryAR.from_repository_values(
                library_name=unit_definition_post_input.libraryName, is_editable=True
            )

        def library_exists(self, library_name: str) -> bool:
            assert library_name == unit_definition_post_input.libraryName
            return True

    repo_fake = UnitDefinitionRepositoryFake()
    unit_definition_repository_property_mock.return_value = repo_fake
    library_repository_property_mock.return_value = LibraryRepositoryFake()
    dictionary_term_repository_property_mock.term_exists.return_value = True
    ct_term_name_repository_property_mock.term_exists.return_value = True
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # when
    with pytest.raises(ValidationException):
        service.post(unit_definition_post_input)

    # then
    assert repo_fake.verified_legacy_codes == {unit_definition_post_input.legacyCode}


@settings(
    max_examples=int(max(10, settings.default.max_examples / 10)),
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
@given(unit_definition_post_input=unit_definition_post_inputs())
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.ct_term_name_repository",
    new_callable=PropertyMock,
)
@patch(
    UnitDefinitionService.__module__
    + ".MetaRepository.dictionary_term_generic_repository",
    new_callable=PropertyMock,
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.library_repository",
    new_callable=PropertyMock,
)
def test__unit_definition_service__post_another_master_unit__result(
    library_repository_property_mock: PropertyMock,
    unit_definition_repository_property_mock: PropertyMock,
    dictionary_term_repository_property_mock: PropertyMock,
    ct_term_name_repository_property_mock: PropertyMock,
    unit_definition_post_input: UnitDefinitionPostInput,
):
    # given

    assume(
        unit_definition_post_input.masterUnit
        and normalize_string(unit_definition_post_input.unitDimension) is not None
    )

    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):
        def master_unit_exists_by_unit_dimension(self, unit_dimension: str) -> bool:
            return super().master_unit_exists_by_unit_dimension(unit_dimension) or True

    class LibraryRepositoryFake(LibraryRepositoryFakeBase):
        def find_by_name(self, name: str) -> Optional[LibraryAR]:
            assert name == unit_definition_post_input.libraryName
            return LibraryAR.from_repository_values(
                library_name=unit_definition_post_input.libraryName, is_editable=True
            )

        def library_exists(self, library_name: str) -> bool:
            assert library_name == unit_definition_post_input.libraryName
            return True

    repo_fake = UnitDefinitionRepositoryFake()
    unit_definition_repository_property_mock.return_value = repo_fake
    library_repository_property_mock.return_value = LibraryRepositoryFake()
    dictionary_term_repository_property_mock.term_exists.return_value = True
    ct_term_name_repository_property_mock.term_exists.return_value = True
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # when
    with pytest.raises(ValidationException):
        service.post(unit_definition_post_input)

    # then
    assert repo_fake.verified_dimensions == {unit_definition_post_input.unitDimension}


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(unit_definition_ar=draft_unit_definitions())
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition_service__delete__result(
    unit_definition_repository_property_mock: PropertyMock,
    unit_definition_ar: UnitDefinitionAR,
):
    # given
    assume(unit_definition_ar.item_metadata.major_version == 0)

    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):

        savedItem: Optional[UnitDefinitionAR] = None

        def save(self, item: UnitDefinitionAR) -> None:
            assert self.savedItem is None
            self.savedItem = item

        def find_by_uid_2(
            self,
            uid: str,
            *,
            version: Optional[str] = None,
            status: Optional[LibraryItemStatus] = None,
            at_specific_date: Optional[datetime] = None,
            for_update: bool = False,
        ) -> Optional[UnitDefinitionAR]:
            assert for_update
            assert uid == unit_definition_ar.uid
            assert version is None
            assert status is None
            assert at_specific_date is None
            return unit_definition_ar

    repo_fake = UnitDefinitionRepositoryFake()
    unit_definition_repository_property_mock.return_value = repo_fake
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # when
    service.delete(uid=unit_definition_ar.uid)

    # then
    item = repo_fake.savedItem
    assert item is unit_definition_ar
    assert item.is_deleted


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(unit_definition_ar=draft_unit_definitions())
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition_service__approve__result(
    unit_definition_repository_property_mock: PropertyMock,
    unit_definition_ar: UnitDefinitionAR,
):
    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):

        savedItem: Optional[UnitDefinitionAR] = None

        def save(self, item: UnitDefinitionAR) -> None:
            assert self.savedItem is None
            self.savedItem = item

        def find_by_uid_2(
            self,
            uid: str,
            *,
            version: Optional[str] = None,
            status: Optional[LibraryItemStatus] = None,
            at_specific_date: Optional[datetime] = None,
            for_update: bool = False,
        ) -> Optional[UnitDefinitionAR]:
            assert for_update
            assert uid == unit_definition_ar.uid
            assert version is None
            assert status is None
            assert at_specific_date is None
            return unit_definition_ar

    repo_fake = UnitDefinitionRepositoryFake()
    unit_definition_repository_property_mock.return_value = repo_fake
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # when
    value_before = unit_definition_ar.concept_vo
    service_result = service.approve(uid=unit_definition_ar.uid)

    # then
    item = repo_fake.savedItem
    assert item is unit_definition_ar
    assert item.item_metadata.status == LibraryItemStatus.FINAL
    assert item.concept_vo == value_before
    assert service_result == UnitDefinitionModel.from_unit_definition_ar(
        item,
        find_term_by_uid=lambda _: None,
        find_dictionary_term_by_uid=lambda _: None,
    )


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(unit_definition_ar=final_unit_definitions())
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition_service__inactivate__result(
    unit_definition_repository_property_mock: PropertyMock,
    unit_definition_ar: UnitDefinitionAR,
):
    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):

        savedItem: Optional[UnitDefinitionAR] = None

        def save(self, item: UnitDefinitionAR) -> None:
            assert self.savedItem is None
            self.savedItem = item

        def find_by_uid_2(
            self,
            uid: str,
            *,
            version: Optional[str] = None,
            status: Optional[LibraryItemStatus] = None,
            at_specific_date: Optional[datetime] = None,
            for_update: bool = False,
        ) -> Optional[UnitDefinitionAR]:
            assert for_update
            assert uid == unit_definition_ar.uid
            assert version is None
            assert status is None
            assert at_specific_date is None
            return unit_definition_ar

    repo_fake = UnitDefinitionRepositoryFake()
    unit_definition_repository_property_mock.return_value = repo_fake
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # when
    value_before = unit_definition_ar.concept_vo
    service_result = service.inactivate(uid=unit_definition_ar.uid)

    # then
    item = repo_fake.savedItem
    assert item is unit_definition_ar
    assert item.item_metadata.status == LibraryItemStatus.RETIRED
    assert item.concept_vo == value_before
    assert service_result == UnitDefinitionModel.from_unit_definition_ar(
        item,
        find_term_by_uid=lambda _: None,
        find_dictionary_term_by_uid=lambda _: None,
    )


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(unit_definition_ar=retired_unit_definitions())
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition_service__reactivate__result(
    unit_definition_repository_property_mock: PropertyMock,
    unit_definition_ar: UnitDefinitionAR,
):
    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):

        savedItem: Optional[UnitDefinitionAR] = None

        def save(self, item: UnitDefinitionAR) -> None:
            assert self.savedItem is None
            self.savedItem = item

        def find_by_uid_2(
            self,
            uid: str,
            *,
            version: Optional[str] = None,
            status: Optional[LibraryItemStatus] = None,
            at_specific_date: Optional[datetime] = None,
            for_update: bool = False,
        ) -> Optional[UnitDefinitionAR]:
            assert for_update
            assert uid == unit_definition_ar.uid
            assert version is None
            assert status is None
            assert at_specific_date is None
            return unit_definition_ar

    repo_fake = UnitDefinitionRepositoryFake()
    unit_definition_repository_property_mock.return_value = repo_fake
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # when
    value_before = unit_definition_ar.concept_vo
    service_result = service.reactivate(uid=unit_definition_ar.uid)

    # then
    item = repo_fake.savedItem
    assert item is unit_definition_ar
    assert item.item_metadata.status == LibraryItemStatus.FINAL
    assert item.concept_vo == value_before
    assert service_result == UnitDefinitionModel.from_unit_definition_ar(
        item,
        find_term_by_uid=lambda _: None,
        find_dictionary_term_by_uid=lambda _: None,
    )


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(unit_definition_ar=final_unit_definitions())
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition_service__new_version__result(
    unit_definition_repository_property_mock: PropertyMock,
    unit_definition_ar: UnitDefinitionAR,
):
    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):

        savedItem: Optional[UnitDefinitionAR] = None

        def save(self, item: UnitDefinitionAR) -> None:
            assert self.savedItem is None
            self.savedItem = item

        def find_by_uid_2(
            self,
            uid: str,
            *,
            version: Optional[str] = None,
            status: Optional[LibraryItemStatus] = None,
            at_specific_date: Optional[datetime] = None,
            for_update: bool = False,
        ) -> Optional[UnitDefinitionAR]:
            assert for_update
            assert uid == unit_definition_ar.uid
            assert version is None
            assert status is None
            assert at_specific_date is None
            return unit_definition_ar

    repo_fake = UnitDefinitionRepositoryFake()
    unit_definition_repository_property_mock.return_value = repo_fake
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # when
    value_before = unit_definition_ar.concept_vo
    service_result = service.new_version(uid=unit_definition_ar.uid)

    # then
    item = repo_fake.savedItem
    assert item is unit_definition_ar
    assert item.item_metadata.status == LibraryItemStatus.DRAFT
    assert item.concept_vo == value_before
    assert service_result == UnitDefinitionModel.from_unit_definition_ar(
        item,
        find_term_by_uid=lambda _: None,
        find_dictionary_term_by_uid=lambda _: None,
    )


@composite
def unit_definition_patch_inputs(draw):
    unit_definition_value: UnitDefinitionValueVO = draw(unit_definition_values())
    use_unitCt = draw(booleans())
    use_unitSubsets = draw(booleans())
    use_convertibleUnit = draw(booleans())
    use_displayUnit = draw(booleans())
    use_masterUnit = draw(booleans())
    use_siUnit = draw(booleans())
    use_usConventionalUnit = draw(booleans())
    use_unitDimension = draw(booleans())
    use_legacyCode = draw(booleans())
    use_molecularWeightConvExpon = draw(booleans())
    use_conversionFactorToMaster = draw(booleans())
    use_name = draw(booleans())

    changeDescription: str = draw(strings_with_at_least_one_non_space_char())
    ctUnits: Sequence[str] = [ct_unit.uid for ct_unit in unit_definition_value.ct_units]
    unitSubsets: Sequence[str] = [
        unit_subset.uid for unit_subset in unit_definition_value.unit_subsets
    ]
    convertibleUnit: bool = unit_definition_value.convertible_unit
    displayUnit: bool = unit_definition_value.display_unit
    masterUnit: bool = unit_definition_value.master_unit
    siUnit: bool = unit_definition_value.si_unit
    usConventionalUnit: bool = unit_definition_value.us_conventional_unit
    unitDimension: Optional[str] = unit_definition_value.unit_dimension_uid
    legacyCode: Optional[str] = unit_definition_value.legacy_code
    molecularWeightConvExpon: Optional[
        int
    ] = unit_definition_value.molecular_weight_conv_expon
    conversionFactorToMaster: Optional[
        float
    ] = unit_definition_value.conversion_factor_to_master
    name: str = unit_definition_value.name

    result = {"changeDescription": changeDescription}

    if use_unitCt:
        result["ctUnits"] = ctUnits
    if use_unitSubsets:
        result["unitSubsets"] = unitSubsets
    if use_convertibleUnit:
        result["convertibleUnit"] = convertibleUnit
    if use_displayUnit:
        result["displayUnit"] = displayUnit
    if use_masterUnit or (
        use_conversionFactorToMaster and conversionFactorToMaster != 1.0
    ):
        result["masterUnit"] = masterUnit
    if use_siUnit:
        result["siUnit"] = siUnit
    if use_usConventionalUnit:
        result["usConventionalUnit"] = usConventionalUnit
    if use_unitDimension or (
        use_molecularWeightConvExpon and molecularWeightConvExpon is None
    ):
        result["unitDimension"] = unitDimension
    if use_legacyCode:
        result["legacyCode"] = legacyCode
    if use_molecularWeightConvExpon or (
        use_unitDimension and unitDimension == CONCENTRATION_UNIT_DIMENSION_VALUE
    ):
        result["molecularWeightConvExpon"] = molecularWeightConvExpon
    if use_conversionFactorToMaster or use_masterUnit:
        result["conversionFactorToMaster"] = conversionFactorToMaster
    if use_name:
        result["name"] = name

    return UnitDefinitionPatchInput(**result)


@settings(max_examples=int(max(10, settings.default.max_examples / 10)), deadline=None)
@given(
    unit_definition_ar=draft_unit_definitions(),
    unit_definition_patch_input=unit_definition_patch_inputs(),
)
@patch(UnitDefinitionService.__module__ + ".MetaRepository.ct_term_name_repository")
@patch(
    UnitDefinitionService.__module__
    + ".MetaRepository.dictionary_term_generic_repository"
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition_service__patch__result(
    unit_definition_repository_property_mock: PropertyMock,
    dictionary_term_repository_property_mock: PropertyMock,
    ct_term_name_repository_property_mock: PropertyMock,
    unit_definition_ar: UnitDefinitionAR,
    unit_definition_patch_input: UnitDefinitionPatchInput,
):

    assume(
        unit_definition_ar.concept_vo.ct_units == []
        or "unitCt" not in unit_definition_patch_input.__fields_set__
        or unit_definition_patch_input.ctUnits == unit_definition_ar.concept_vo.ct_units
    )

    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):
        def find_by_uid_2(
            self,
            uid: str,
            *,
            version: Optional[str] = None,
            status: Optional[LibraryItemStatus] = None,
            at_specific_date: Optional[datetime] = None,
            for_update: bool = False,
        ) -> Optional[UnitDefinitionAR]:
            assert for_update
            assert uid == unit_definition_ar.uid
            assert version is None
            assert status is None
            assert at_specific_date is None
            return unit_definition_ar

    repo_fake = UnitDefinitionRepositoryFake()
    unit_definition_repository_property_mock.return_value = repo_fake
    dictionary_term_repository_property_mock.term_exists.return_value = True
    ct_term_name_repository_property_mock.term_exists.return_value = True
    dictionary_term_repository_property_mock.find_by_uid = get_mock_dictionary_item
    ct_term_name_repository_property_mock.find_by_uid = get_mock_ct_item
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # when
    model_before = UnitDefinitionModel.from_unit_definition_ar(
        unit_definition_ar,
        find_term_by_uid=lambda _: None,
        find_dictionary_term_by_uid=lambda _: None,
    )
    service_result = service.patch(
        uid=unit_definition_ar.uid, patch_input=unit_definition_patch_input
    )

    # then
    item = repo_fake.saved_item
    assert item is unit_definition_ar
    assert item.item_metadata.status == LibraryItemStatus.DRAFT
    assert service_result == UnitDefinitionModel.from_unit_definition_ar(
        item,
        find_term_by_uid=get_mock_ct_item,
        find_dictionary_term_by_uid=get_mock_dictionary_item,
    )
    for field in unit_definition_patch_input.__fields_set__:
        if isinstance(getattr(service_result, field), SimpleTermModel):
            assert (
                str(getattr(service_result, field).termUid).strip()
                == str(getattr(unit_definition_patch_input, field)).strip()
            )
        elif isinstance(getattr(service_result, field), Sequence):
            if (
                len(getattr(service_result, field)) > 0
                and getattr(service_result, field)[0] is SimpleTermModel
            ):
                assert [
                    term.termUid for term in getattr(service_result, field)
                ] == getattr(unit_definition_patch_input, field)
        else:
            assert (
                str(getattr(service_result, field)).strip()
                == str(getattr(unit_definition_patch_input, field)).strip()
            )

    for field in (
        set(unit_definition_patch_input.__fields__)
        - unit_definition_patch_input.__fields_set__
    ):
        assert getattr(service_result, field) == getattr(model_before, field)


@settings(
    max_examples=int(max(10, settings.default.max_examples / 10)),
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
@given(
    unit_definition_ar=draft_unit_definitions(),
    unit_definition_patch_input=unit_definition_patch_inputs().filter(
        lambda x: x.name is not None
    ),
)
@patch(UnitDefinitionService.__module__ + ".MetaRepository.ct_term_name_repository")
@patch(
    UnitDefinitionService.__module__
    + ".MetaRepository.dictionary_term_generic_repository"
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition_service__patch_to_non_unique_name__result(
    unit_definition_repository_property_mock: PropertyMock,
    dictionary_term_repository_property_mock: PropertyMock,
    ct_term_name_repository_property_mock: PropertyMock,
    unit_definition_ar: UnitDefinitionAR,
    unit_definition_patch_input: UnitDefinitionPatchInput,
):
    # given
    assume(
        unit_definition_ar.concept_vo.ct_units == []
        or "unitCt" not in unit_definition_patch_input.__fields_set__
        or unit_definition_patch_input.ctUnits == unit_definition_ar.concept_vo.ct_units
    )

    assume(unit_definition_patch_input.name != unit_definition_ar.name)

    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):
        def find_by_uid_2(
            self,
            uid: str,
            *,
            version: Optional[str] = None,
            status: Optional[LibraryItemStatus] = None,
            at_specific_date: Optional[datetime] = None,
            for_update: bool = False,
        ) -> Optional[UnitDefinitionAR]:
            assert for_update
            assert uid == unit_definition_ar.uid
            assert version is None
            assert status is None
            assert at_specific_date is None
            return unit_definition_ar

        def check_exists_by_name(self, name: str) -> bool:
            return super().check_exists_by_name(name) or True

    repo_fake = UnitDefinitionRepositoryFake()
    unit_definition_repository_property_mock.return_value = repo_fake
    dictionary_term_repository_property_mock.term_exists.return_value = True
    ct_term_name_repository_property_mock.term_exists.return_value = True
    dictionary_term_repository_property_mock.find_by_uid = get_mock_dictionary_item
    ct_term_name_repository_property_mock.find_by_uid = get_mock_ct_item
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # then
    with pytest.raises(ValidationException):
        # when
        service.patch(
            uid=unit_definition_ar.uid, patch_input=unit_definition_patch_input
        )

    assert repo_fake.verified_names == {unit_definition_patch_input.name}
    assert repo_fake.saved_item is None


@settings(
    max_examples=int(max(10, settings.default.max_examples / 10)),
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
@given(
    unit_definition_ar=draft_unit_definitions(),
    unit_definition_patch_input=unit_definition_patch_inputs().filter(
        lambda x: x.legacyCode is not None
    ),
)
@patch(UnitDefinitionService.__module__ + ".MetaRepository.ct_term_name_repository")
@patch(
    UnitDefinitionService.__module__
    + ".MetaRepository.dictionary_term_generic_repository"
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition_service__patch_to_non_unique_legacy_code__result(
    unit_definition_repository_property_mock: PropertyMock,
    dictionary_term_repository_property_mock: PropertyMock,
    ct_term_name_repository_property_mock: PropertyMock,
    unit_definition_ar: UnitDefinitionAR,
    unit_definition_patch_input: UnitDefinitionPatchInput,
):
    assume(
        unit_definition_patch_input.legacyCode
        != unit_definition_ar.concept_vo.legacy_code
    )

    assume(
        unit_definition_ar.concept_vo.ct_units == []
        or "unitCt" not in unit_definition_patch_input.__fields_set__
        or unit_definition_patch_input.ctUnits == unit_definition_ar.concept_vo.ct_units
    )

    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):
        def find_by_uid_2(
            self,
            uid: str,
            *,
            version: Optional[str] = None,
            status: Optional[LibraryItemStatus] = None,
            at_specific_date: Optional[datetime] = None,
            for_update: bool = False,
        ) -> Optional[UnitDefinitionAR]:
            assert for_update
            assert uid == unit_definition_ar.uid
            assert version is None
            assert status is None
            assert at_specific_date is None
            return unit_definition_ar

        def exists_by_legacy_code(self, legacy_code: str) -> bool:
            return super().exists_by_legacy_code(legacy_code) or True

    repo_fake = UnitDefinitionRepositoryFake()
    unit_definition_repository_property_mock.return_value = repo_fake
    dictionary_term_repository_property_mock.term_exists.return_value = True
    ct_term_name_repository_property_mock.term_exists.return_value = True
    dictionary_term_repository_property_mock.find_by_uid = get_mock_dictionary_item
    ct_term_name_repository_property_mock.find_by_uid = get_mock_ct_item
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # then
    with pytest.raises(ValidationException):
        # when
        service.patch(
            uid=unit_definition_ar.uid, patch_input=unit_definition_patch_input
        )

    assert repo_fake.verified_legacy_codes == {unit_definition_patch_input.legacyCode}
    assert repo_fake.saved_item is None


@settings(
    max_examples=int(max(10, settings.default.max_examples / 10)),
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    deadline=None,
)
@given(
    unit_definition_ar=draft_unit_definitions(),
    unit_definition_patch_input=unit_definition_patch_inputs().filter(
        lambda x: x.unitDimension is not None
    ),
)
@patch(UnitDefinitionService.__module__ + ".MetaRepository.ct_term_name_repository")
@patch(
    UnitDefinitionService.__module__
    + ".MetaRepository.dictionary_term_generic_repository"
)
@patch(
    UnitDefinitionService.__module__ + ".MetaRepository.unit_definition_repository",
    new_callable=PropertyMock,
)
def test__unit_definition_service__patch_to_another_master_unit__result(
    unit_definition_repository_property_mock: PropertyMock,
    dictionary_term_repository_property_mock: PropertyMock,
    ct_term_name_repository_property_mock: PropertyMock,
    unit_definition_ar: UnitDefinitionAR,
    unit_definition_patch_input: UnitDefinitionPatchInput,
):
    # given
    assume(
        unit_definition_patch_input.unitDimension
        != unit_definition_ar.concept_vo.unit_dimension_uid
    )

    assume(
        unit_definition_patch_input.masterUnit
        or (
            unit_definition_patch_input.masterUnit is None
            and unit_definition_ar.concept_vo.master_unit
        )
    )

    assume(
        unit_definition_ar.concept_vo.ct_units == []
        or "unitCt" not in unit_definition_patch_input.__fields_set__
        or unit_definition_patch_input.ctUnits == unit_definition_ar.concept_vo.ct_units
    )

    class UnitDefinitionRepositoryFake(UnitDefinitionRepositoryFakeBase):
        def find_by_uid_2(
            self,
            uid: str,
            *,
            version: Optional[str] = None,
            status: Optional[LibraryItemStatus] = None,
            at_specific_date: Optional[datetime] = None,
            for_update: bool = False,
        ) -> Optional[UnitDefinitionAR]:
            assert for_update
            assert uid == unit_definition_ar.uid
            assert version is None
            assert status is None
            assert at_specific_date is None
            return unit_definition_ar

        def master_unit_exists_by_unit_dimension(self, unit_dimension: str) -> bool:
            return super().master_unit_exists_by_unit_dimension(unit_dimension) or True

    repo_fake = UnitDefinitionRepositoryFake()
    unit_definition_repository_property_mock.return_value = repo_fake
    dictionary_term_repository_property_mock.term_exists.return_value = True
    ct_term_name_repository_property_mock.term_exists.return_value = True
    dictionary_term_repository_property_mock.find_by_uid = get_mock_dictionary_item
    ct_term_name_repository_property_mock.find_by_uid = get_mock_ct_item
    service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )

    # then
    with pytest.raises(ValidationException):
        # when
        service.patch(
            uid=unit_definition_ar.uid, patch_input=unit_definition_patch_input
        )

    assert repo_fake.verified_dimensions == {unit_definition_patch_input.unitDimension}
