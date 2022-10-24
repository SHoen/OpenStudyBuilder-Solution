import datetime
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Iterable, Optional, Sequence, Tuple

from clinical_mdr_api.domain._utils import normalize_string


@dataclass(frozen=True)
class StudySelectionObjectiveVO:
    """
    The StudySelectionObjectiveVO acts as the value object for a single selection between a study and a objective
    """

    study_selection_uid: str
    study_uid: Optional[str]
    objective_uid: Optional[str]
    objective_version: Optional[str]
    objective_level_uid: Optional[str]
    objective_level_order: Optional[int]
    # Study selection Versioning
    start_date: datetime.datetime
    user_initials: Optional[str]
    accepted_version: bool = False

    @classmethod
    def from_input_values(
        cls,
        objective_uid: str,
        objective_version: str,
        objective_level_uid: Optional[str],
        objective_level_order: Optional[int],
        user_initials: str,
        study_uid: Optional[str] = None,
        study_selection_uid: Optional[str] = None,
        start_date: Optional[datetime.datetime] = None,
        generate_uid_callback: Callable[[], str] = None,
        accepted_version: bool = False,
    ):
        if not objective_level_order:
            objective_level_order = 0

        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now()

        return cls(
            study_uid=study_uid,
            objective_uid=normalize_string(objective_uid),
            objective_version=objective_version,
            start_date=start_date,
            study_selection_uid=normalize_string(study_selection_uid),
            objective_level_uid=normalize_string(objective_level_uid),
            objective_level_order=objective_level_order,
            user_initials=normalize_string(user_initials),
            accepted_version=accepted_version,
        )

    def validate(
        self,
        objective_exist_callback: Callable[[str], bool] = (lambda _: True),
        ct_term_level_exist_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        # Checks if there exists a objective which is approved with objective_uid
        if not objective_exist_callback(normalize_string(self.objective_uid)):
            raise ValueError(
                f"There is no approved objective identified by provided uid ({self.objective_uid})"
            )
        if (
            not ct_term_level_exist_callback(self.objective_level_uid)
            and self.objective_level_uid
        ):
            raise ValueError(
                f"There is no approved objective level identified by provided term uid ({self.objective_level_uid})"
            )

    def update_version(self, objective_version: str):
        return replace(self, objective_version=objective_version)

    def accept_versions(self):
        return replace(self, accepted_version=True)


@dataclass
class StudySelectionObjectivesAR:
    """
    The StudySelectionObjectivesAR holds all the study objective selections for a given study, the aggregate root also ,
    takes care of all operations changing the study selections for a study.
    * add more selections
    * remove selections
    * patch selection
    * delete selection
    """

    _study_uid: str
    _study_objectives_selection: Tuple
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    @property
    def study_uid(self) -> str:
        return self._study_uid

    @property
    def study_objectives_selection(self) -> Sequence[StudySelectionObjectiveVO]:
        return self._study_objectives_selection

    def get_specific_objective_selection(
        self, study_selection_uid: str
    ) -> Tuple[StudySelectionObjectiveVO, int]:
        for order, selection in enumerate(self.study_objectives_selection, start=1):
            if selection.study_selection_uid == study_selection_uid:
                return selection, order
        raise ValueError(
            f"The study objective uid does not exist ({study_selection_uid})"
        )

    def add_objective_selection(
        self,
        study_objective_selection: StudySelectionObjectiveVO,
        objective_exist_callback: Callable[[str], bool] = (lambda _: True),
        ct_term_level_exist_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        study_objective_selection.validate(
            objective_exist_callback, ct_term_level_exist_callback
        )

        # add new value object in the list based on the objective level order
        selection_inserted = False
        if study_objective_selection.objective_level_order:
            updated_selections = []
            for selection in self._study_objectives_selection:
                if (
                    selection.objective_level_order
                    > study_objective_selection.objective_level_order
                    and not selection_inserted
                ):
                    updated_selections.append(study_objective_selection)
                    selection_inserted = True
                updated_selections.append(selection)
            if not selection_inserted:
                updated_selections.append(study_objective_selection)
            self._study_objectives_selection = tuple(updated_selections)
        else:
            self._study_objectives_selection = self._study_objectives_selection + (
                study_objective_selection,
            )

    @classmethod
    def from_repository_values(
        cls,
        study_uid: str,
        study_objectives_selection: Iterable[StudySelectionObjectiveVO],
    ) -> "StudySelectionObjectivesAR":
        return cls(
            _study_uid=normalize_string(study_uid),
            _study_objectives_selection=tuple(study_objectives_selection),
        )

    def remove_objective_selection(self, study_selection_uid: str) -> None:
        updated_selection = []
        for selection in self.study_objectives_selection:
            if selection.study_selection_uid != study_selection_uid:
                updated_selection.append(selection)
        self._study_objectives_selection = tuple(updated_selection)

    def set_new_order_for_selection(
        self, study_selection_uid: str, new_order: int, user_initials: str
    ):
        # check if the new order is valid using the robustness principle
        if new_order > len(self.study_objectives_selection):
            # If order is higher than maximum allowed then set to max
            new_order = len(self.study_objectives_selection)
        elif new_order < 1:
            # If order is lower than 1 set to 1
            new_order = 1
        # find the selection
        selected_value, old_order = self.get_specific_objective_selection(
            study_selection_uid
        )
        # We have to reset the selected value so it can be set to edit in the domain
        selected_value = StudySelectionObjectiveVO.from_input_values(
            objective_uid=selected_value.objective_uid,
            objective_level_uid=selected_value.objective_level_uid,
            user_initials=user_initials,
            study_selection_uid=selected_value.study_selection_uid,
            objective_level_order=selected_value.objective_level_order,
            objective_version=selected_value.objective_version,
        )
        # change the order
        updated_selections = []
        # We need to handle if front end selects a order number there is out of range
        #  then we just move it to best possible position
        selection_needs_inserting = False
        for order, selection in enumerate(self.study_objectives_selection, start=1):
            if (
                selection_needs_inserting
                and selection.objective_level_order
                >= selected_value.objective_level_order
            ):
                updated_selections.append(selected_value)
                selection_needs_inserting = False

            # if the order is the where the new item is meant to be put
            if order == new_order:
                # we check if the order is being changed to lower or higher and add it to the list appropriately
                if old_order >= new_order:
                    if (
                        selection.objective_level_order
                        >= selected_value.objective_level_order
                    ):
                        updated_selections.append(selected_value)
                    else:
                        updated_selections = True
                    if (
                        selection.study_selection_uid
                        != selected_value.study_selection_uid
                    ):
                        updated_selections.append(selection)
                else:
                    if (
                        selection.study_selection_uid
                        != selected_value.study_selection_uid
                    ):
                        updated_selections.append(selection)
                    if (
                        selection.objective_level_order
                        >= selected_value.objective_level_order
                    ):
                        updated_selections.append(selected_value)
                    else:
                        updated_selections = True
            # We add all other vo to in the same order as before, except for the vo we are moving
            elif selection.study_selection_uid != selected_value.study_selection_uid:
                updated_selections.append(selection)
        self._study_objectives_selection = tuple(updated_selections)

    def update_selection(
        self,
        updated_study_objective_selection: StudySelectionObjectiveVO,
        objective_exist_callback: Callable[[str], bool] = (lambda _: True),
        ct_term_level_exist_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        updated_study_objective_selection.validate(
            objective_exist_callback=objective_exist_callback,
            ct_term_level_exist_callback=ct_term_level_exist_callback,
        )
        updated_selection = []
        further_update = False
        for selection in self.study_objectives_selection:
            if (
                selection.study_selection_uid
                == updated_study_objective_selection.study_selection_uid
            ):
                if (
                    updated_study_objective_selection.objective_level_order
                    == selection.objective_level_order
                ):
                    updated_selection.append(updated_study_objective_selection)
                else:
                    # the objective level have changed, so the objective level order is changed
                    further_update = True
            else:
                updated_selection.append(selection)
        if further_update:
            # The objective level is updated
            selection_inserted = False
            updated_selections = []
            for selection in updated_selection:
                if (
                    selection.objective_level_order
                    > updated_study_objective_selection.objective_level_order
                    and not selection_inserted
                ):
                    updated_selections.append(updated_study_objective_selection)
                    selection_inserted = True
                updated_selections.append(selection)
            if selection_inserted is False:
                updated_selections.append(updated_study_objective_selection)
            self._study_objectives_selection = tuple(updated_selections)
        else:
            # The objective level is unchanged
            self._study_objectives_selection = tuple(updated_selection)

    def validate(self):
        objectives = []
        for selection in self.study_objectives_selection:
            if selection.objective_uid in objectives:
                raise ValueError(
                    f"There is already a study selection to that objective ({selection.objective_uid})"
                )
            objectives.append(selection.objective_uid)
