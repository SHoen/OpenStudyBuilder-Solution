import datetime
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional, Sequence, Tuple

from clinical_mdr_api.domain._utils import normalize_string
from clinical_mdr_api.domain.concepts.compound import CompoundAR
from clinical_mdr_api.exceptions import BusinessLogicException


def _raise(exc: Exception) -> Any:
    raise exc


@dataclass
class StudyCompoundDosingVO:
    study_uid: str
    study_selection_uid: str
    study_compound_uid: Optional[str]
    study_element_uid: Optional[str]

    # Study selection Versioning
    start_date: datetime.datetime
    user_initials: Optional[str]

    # Optional information
    compound_uid: Optional[str] = None
    compound_alias_uid: Optional[str] = None
    dose_frequency_uid: Optional[str] = None
    dose_value_uid: Optional[str] = None

    @classmethod
    def from_input_values(
        cls,
        study_compound_uid: Optional[str],
        study_element_uid: Optional[str],
        dose_value_uid: Optional[str],
        dose_frequency_uid: Optional[str],
        user_initials: str,
        study_uid: Optional[str] = None,
        compound_uid: Optional[str] = None,
        compound_alias_uid: Optional[str] = None,
        study_selection_uid: Optional[str] = None,
        start_date: Optional[datetime.datetime] = None,
        generate_uid_callback: Callable[[], str] = (
            lambda: _raise(
                ValueError("generate_uid_callback necessary when uid not provided")
            )
        ),
    ) -> "StudyCompoundDosingVO":
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now()

        return StudyCompoundDosingVO(
            study_uid=study_uid,
            study_selection_uid=normalize_string(study_selection_uid),
            study_compound_uid=normalize_string(study_compound_uid),
            compound_uid=normalize_string(compound_uid),
            compound_alias_uid=normalize_string(compound_alias_uid),
            study_element_uid=normalize_string(study_element_uid),
            dose_value_uid=normalize_string(dose_value_uid),
            dose_frequency_uid=normalize_string(dose_frequency_uid),
            user_initials=normalize_string(user_initials),
            start_date=start_date,
        )

    def validate(
        self,
        selection_uid_by_compound_dose_and_frequency_callback: Callable[
            ["StudyCompoundDosingVO"], str
        ],
        compound_callback: Callable[[str], CompoundAR] = (lambda _: None),
    ) -> None:
        """
        Raises ValueError or BusinessLogicException if values do not comply with relevant business rules.

        """
        # Find a compound dosing selection with the same compound, dose value, dose frequency
        exisiting_uid = selection_uid_by_compound_dose_and_frequency_callback(self)
        if exisiting_uid and self.study_selection_uid != exisiting_uid:
            raise BusinessLogicException(
                "Compound dosing selection with the specified compound, dose value and dose frequency already exists."
            )

        # Validate that each of these selections is actually defined on the selected library compound:
        #   - dose value
        #   - dose frequency
        compound: CompoundAR = compound_callback(self.compound_uid)
        if compound:
            if (
                self.dose_value_uid is not None
                and self.dose_value_uid not in compound.concept_vo.dose_values_uids
            ):
                raise BusinessLogicException(
                    f"Selected dose value is not valid for compound '{compound.concept_vo.name}'."
                )
            if (
                self.dose_frequency_uid is not None
                and self.dose_frequency_uid
                not in compound.concept_vo.dose_frequency_uids
            ):
                raise BusinessLogicException(
                    f"Selected dose frequency is not valid for compound '{compound.concept_vo.name}'."
                )


@dataclass
class StudySelectionCompoundDosingsAR:
    _study_uid: str
    _study_compound_dosings_selection: Sequence
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    @property
    def study_uid(self) -> str:
        return self._study_uid

    @property
    def study_compound_dosings_selection(self) -> Sequence[StudyCompoundDosingVO]:
        return self._study_compound_dosings_selection

    def get_specific_compound_dosing_selection(
        self, study_selection_uid: str
    ) -> Tuple[StudyCompoundDosingVO, int]:
        """
        Used to receive a specific VO from the AR
        :param study_selection_uid:
        :return:
        """
        for order, selection in enumerate(
            self.study_compound_dosings_selection, start=1
        ):
            if selection.study_selection_uid == study_selection_uid:
                return selection, order
        raise ValueError(
            f"There is no selection between the compound dosing ({study_selection_uid} and the study)"
        )

    def add_compound_dosing_selection(
        self,
        study_compound_dosing_selection: StudyCompoundDosingVO,
        selection_uid_by_compound_dose_and_frequency_callback: Callable[
            [StudyCompoundDosingVO], str
        ],
        compound_callback: Callable[[str], CompoundAR] = (lambda _: None),
    ) -> None:
        """
        Adding a new study compound to the _study_compound_selection
        """
        # validate VO before adding
        study_compound_dosing_selection.validate(
            selection_uid_by_compound_dose_and_frequency_callback=selection_uid_by_compound_dose_and_frequency_callback,
            compound_callback=compound_callback,
        )
        self._study_compound_dosings_selection = (
            self._study_compound_dosings_selection + [study_compound_dosing_selection]
        )

    @classmethod
    def from_repository_values(
        cls,
        study_uid: str,
        selection: Iterable[StudyCompoundDosingVO],
    ) -> "StudySelectionCompoundDosingsAR":
        """
        Factory method to create a AR
        """
        return cls(
            _study_uid=normalize_string(study_uid),
            _study_compound_dosings_selection=list(selection),
        )

    def remove_compound_dosing_selection(self, study_selection_uid: str):
        """
        removing a study compound dosing
        :param study_selection_uid:
        :return:
        """
        updated_selection = []
        for selection in self.study_compound_dosings_selection:
            if not selection.study_selection_uid == study_selection_uid:
                updated_selection.append(selection)
        self._study_compound_dosings_selection = tuple(updated_selection)

    def set_new_order_for_selection(self, study_selection_uid: str, new_order: int):
        """
        Used to reorder a study compound dosing
        :param study_selection_uid:
        :param new_order:
        :return:
        """
        # check if the new order is valid using the robustness principle
        if new_order > len(self.study_compound_dosings_selection):
            # If order is higher than maximum allowed then set to max
            new_order = len(self.study_compound_dosings_selection)
        elif new_order < 1:
            # If order is lower than 1 set to 1
            new_order = 1
        # find the selection
        selected_value, old_order = self.get_specific_compound_dosing_selection(
            study_selection_uid
        )
        # change the order
        updated_selections = []
        for order, selection in enumerate(
            self.study_compound_dosings_selection, start=1
        ):
            # if the order is the where the new item is meant to be put
            if order == new_order:
                # we check if the order is being changed to lower or higher and add it to the list appropriately
                if old_order >= new_order:
                    updated_selections.append(selected_value)
                    if (
                        not selection.study_selection_uid
                        == selected_value.study_selection_uid
                    ):
                        updated_selections.append(selection)
                else:
                    if (
                        not selection.study_selection_uid
                        == selected_value.study_selection_uid
                    ):
                        updated_selections.append(selection)
                    updated_selections.append(selected_value)
            # We add all other vo to in the same order as before, except for the vo we are moving
            elif (
                not selection.study_selection_uid == selected_value.study_selection_uid
            ):
                updated_selections.append(selection)
        self._study_compound_dosings_selection = tuple(updated_selections)

    def update_selection(
        self,
        updated_study_compound_dosing_selection: StudyCompoundDosingVO,
        selection_uid_by_compound_dose_and_frequency_callback: Callable[
            [StudyCompoundDosingVO], str
        ],
        compound_callback: Callable[[str], CompoundAR] = (lambda _: None),
    ) -> None:
        """
        Used when a study compound is updated
        """
        updated_study_compound_dosing_selection.validate(
            selection_uid_by_compound_dose_and_frequency_callback=selection_uid_by_compound_dose_and_frequency_callback,
            compound_callback=compound_callback,
        )
        updated_selection = []
        for selection in self.study_compound_dosings_selection:
            if (
                selection.study_selection_uid
                == updated_study_compound_dosing_selection.study_selection_uid
            ):
                updated_selection.append(updated_study_compound_dosing_selection)
            else:
                updated_selection.append(selection)
        self._study_compound_dosings_selection = tuple(updated_selection)
