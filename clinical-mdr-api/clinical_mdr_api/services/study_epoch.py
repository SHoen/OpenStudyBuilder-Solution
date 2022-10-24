import datetime
from typing import Optional, Sequence

from aenum import extend_enum
from neomodel import db

from clinical_mdr_api import config as settings
from clinical_mdr_api import exceptions
from clinical_mdr_api.config import STUDY_EPOCH_EPOCH_UID
from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import (
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domain.controlled_terminology.utils import TermParentType
from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domain.study_selection.study_epoch import (
    StudyEpochEpoch,
    StudyEpochSubType,
    StudyEpochType,
    StudyEpochVO,
    TimelineAR,
)
from clinical_mdr_api.domain.study_selection.study_visit import (
    StudyVisitContactMode,
    StudyVisitEpochAllocation,
    StudyVisitTimeReference,
    StudyVisitType,
)
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.study_epoch import (
    StudyEpoch,
    StudyEpochCreateInput,
    StudyEpochEditInput,
    StudyEpochTypes,
    StudyEpochVersion,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    calculate_diffs_history,
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)


class StudyEpochService:
    def __init__(self, author="TODO Initials"):
        self._repos = MetaRepository()
        self.repo = self._repos.study_epoch_repository
        self.visit_repo = self._repos.study_visit_repository
        self.author = author
        self._create_ctlist_map()

    def _create_ctlist_map(self):
        self.study_epoch_types = self.repo.create_ctlist(settings.STUDY_EPOCH_TYPE_NAME)
        self.study_epoch_subtypes = self.repo.create_ctlist(
            settings.STUDY_EPOCH_SUBTYPE_NAME
        )
        self.study_epoch_epochs = self.repo.create_ctlist(
            settings.STUDY_EPOCH_EPOCH_NAME
        )

        self.study_visit_types = self.repo.create_ctlist(settings.STUDY_VISIT_TYPE_NAME)
        self.study_visit_timeref = self.repo.create_ctlist(
            settings.STUDY_VISIT_TIMEREF_NAME
        )
        self.study_visit_contact_mode = self.repo.create_ctlist(
            settings.STUDY_VISIT_CONTACT_MODE_NAME
        )
        self.study_visit_epoch_allocation = self.repo.create_ctlist(
            settings.STUDY_VISIT_EPOCH_ALLOCATION_NAME
        )

        for uid, name in self.study_epoch_types.items():
            if uid not in StudyEpochType._member_map_:
                extend_enum(StudyEpochType, uid, name)

        for uid, name in self.study_epoch_subtypes.items():
            if uid not in StudyEpochSubType._member_map_:
                extend_enum(StudyEpochSubType, uid, name)

        for uid, name in self.study_epoch_epochs.items():
            if uid not in StudyEpochEpoch._member_map_:
                extend_enum(StudyEpochEpoch, uid, name)

        for uid, name in self.study_visit_types.items():
            if uid not in StudyVisitType._member_map_:
                extend_enum(StudyVisitType, uid, name)

        for uid, name in self.study_visit_timeref.items():
            if uid not in StudyVisitTimeReference._member_map_:
                extend_enum(StudyVisitTimeReference, uid, name)

        for uid, name in self.study_visit_contact_mode.items():
            if uid not in StudyVisitContactMode._member_map_:
                extend_enum(StudyVisitContactMode, uid, name)

        for uid, name in self.study_visit_epoch_allocation.items():
            if uid not in StudyVisitEpochAllocation._member_map_:
                extend_enum(StudyVisitEpochAllocation, uid, name)

        self._allowed_configs = self._get_allowed_configs()

    def _transform_all_to_response_model(
        self, epoch: StudyEpochVO, study_visit_count: Optional[int] = None
    ) -> StudyEpoch:

        return StudyEpoch(
            uid=epoch.uid,
            studyUid=epoch.study_uid,
            order=epoch.order,
            description=epoch.description,
            startRule=epoch.start_rule,
            endRule=epoch.end_rule,
            duration=epoch.calculated_duration
            if epoch.subtype.value != settings.BASIC_EPOCH_NAME
            else None,
            durationUnit=epoch.duration_unit,
            epoch=epoch.epoch.name,
            epochName=epoch.epoch.value,
            epochSubType=epoch.subtype.name,
            epochSubTypeName=epoch.subtype.value,
            epochType=epoch.epoch_type.name,
            status=epoch.status.value,
            startDay=epoch.get_start_day()
            if epoch.subtype.value != settings.BASIC_EPOCH_NAME
            else None,
            endDay=epoch.get_end_day()
            if epoch.subtype.value != settings.BASIC_EPOCH_NAME
            else None,
            startDate=epoch.start_date.strftime(settings.TIME_FORMAT),
            userInitials=epoch.author,
            possibleActions=epoch.possible_actions,
            changeDescription=epoch.change_description,
            colorHash=epoch.color_hash,
            studyVisitCount=study_visit_count,
        )

    def _instantiate_epoch_items(
        self,
        study_uid: str,
        study_epoch_create_input: StudyEpochCreateInput,
        preview: bool,
    ):
        subtype = StudyEpochSubType[study_epoch_create_input.epochSubType]
        epoch_type = self._get_epoch_type_object(subtype=subtype.name)
        all_epochs_in_study = self.repo.find_all_epochs_by_study(study_uid)
        epochs_in_subtype = self._get_list_of_epochs_in_subtype(
            all_epochs=all_epochs_in_study,
            epoch_sub_type=study_epoch_create_input.epochSubType,
        )
        # if epoch was previously calculated in preview call then we can just take it from the study_epoch_create_input
        # but we need to synchronize the orders because we don't synchronize them in a preview call
        if study_epoch_create_input.epoch is not None:
            epoch = StudyEpochEpoch[study_epoch_create_input.epoch]
            self._synchronize_epoch_orders(
                epochs_to_synchronize=epochs_in_subtype,
                all_epochs=all_epochs_in_study,
                after_create=True,
            )
        # it wasn't previewed and we have to derive it from the epoch subtype
        else:
            epoch = self._get_epoch_object(
                epochs_in_subtype=epochs_in_subtype, subtype=subtype, after_create=True
            )
            # if there exist one epoch in the specific subtype and the second one is being added then it means that
            # we should change the name of the first epoch for instance from "Treatment" to "Treatment 1"
            # we don't want to synchronize in case of preview because user can always cancel creation after getting preview
            if len(epochs_in_subtype) == 1 and not preview:
                self._synchronize_epoch_orders(
                    epochs_to_synchronize=epochs_in_subtype,
                    all_epochs=all_epochs_in_study,
                    after_create=True,
                )
        return epoch, subtype, epoch_type

    @db.transaction
    def get_all_epochs(
        self,
        study_uid: str,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudyEpoch]:
        repos = self._repos
        try:
            study_epochs = self.repo.find_all_epochs_by_study(study_uid=study_uid)

            study_visits = self.visit_repo.find_all_visits_by_study_uid(study_uid)
            timeline = TimelineAR(study_uid, _visits=study_visits)
            visits = timeline.collect_visits_to_epochs(study_epochs)

            all_items = [
                self._transform_all_to_response_model(
                    epoch, study_visit_count=len(visits[epoch.uid])
                )
                for epoch in study_epochs
            ]

            filtered_items = service_level_generic_filtering(
                items=all_items,
                filter_by=filter_by,
                filter_operator=filter_operator,
                sort_by=sort_by,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )

            return filtered_items
        finally:
            repos.close()

    @db.transaction
    def find_by_uid(self, uid: str) -> StudyEpoch:
        repos = self._repos
        try:
            study_epoch = self.repo.find_by_uid(uid=uid)

            return self._transform_all_to_response_model(study_epoch)
        except ValueError as e:
            raise exceptions.ValidationException(e.args[0])
        finally:
            repos.close()

    def _validate_creation(self, epoch_input: StudyEpochCreateInput):
        if epoch_input.epochSubType not in [i.name for i in StudyEpochSubType]:
            raise ValueError("Invalid value for study epoch sub type")
        epoch_subtype_name = StudyEpochSubType[epoch_input.epochSubType].value
        if epoch_subtype_name == settings.BASIC_EPOCH_NAME:
            if self.repo.get_basic_epoch(study_uid=epoch_input.studyUid):
                raise ValueError("There can exist only one Supplemental Study Epoch.")

    def _validate_update(self, epoch_input: StudyEpochCreateInput):
        if epoch_input.epochSubType is not None and epoch_input.epochSubType not in [
            i.name for i in StudyEpochSubType
        ]:
            raise ValueError("Invalid value for study epoch sub type")

    def _get_or_create_epoch_in_specific_subtype(
        self,
        epoch_order: int,
        subtype: StudyEpochSubType,
        amount_of_epochs_in_subtype: int,
    ):
        """
        Gets or creates the epoch CTTerm based on the order of given StudyEpoch inside specific subtype.
        :param epoch_order:
        :param subtype:
        :return:
        """

        # if we have less than one or one epoch in subtype we are not adding trailing number indicating order
        if amount_of_epochs_in_subtype <= 1:
            epoch_name = f"{subtype.value}"
        # if we already have some epochs in the subtype then the epoch name is the subtype name plus the trailing number
        # that indicates the order of given epoch in specific subtype
        else:
            epoch_name = f"{subtype.value} {epoch_order}"

        epoch = None
        # if epoch name is equal to the subtype name then we are reusing the subtype ct term node for the epoch node
        if epoch_name == subtype.value:
            # the following section applies if the name of the epoch is the same as the name of the send epoch subtype
            # in such case we should reuse epoch subtype node and add it to the epoch hierarchy
            epoch_uid = subtype.name
            epoch = StudyEpochSubType[epoch_uid]

            try:
                # adding the epoch sub type term to the epoch codelist
                self._repos.ct_codelist_attribute_repository.add_term(
                    codelist_uid=STUDY_EPOCH_EPOCH_UID,
                    term_uid=epoch.name,
                    # this is name prop of enum which is uid
                    author=self.author,
                    order=999999,
                )
                # connecting the created epoch to the corresponding epoch sub type
                self._repos.ct_term_attributes_repository.add_parent(
                    term_uid=epoch.name,
                    parent_uid=epoch.name,
                    relationship_type=TermParentType.PARENT_SUB_TYPE,
                )
                if epoch.name not in StudyEpochEpoch._member_map_:
                    extend_enum(StudyEpochEpoch, epoch.name, epoch.value)

            except ValueError:
                pass
        # we are trying to find the ct term with given epoch name
        else:
            epoch_uid = self._repos.ct_term_name_repository.find_uid_by_name(
                name=epoch_name
            )

        # if epoch_uid was found then it means that we can reuse it
        if epoch is None:
            if epoch_uid is not None:
                epoch = StudyEpochEpoch[epoch_uid]
            # the epoch ct term was not found and we have to create sponsor defined ct term
            else:
                epoch_sub_type_term = (
                    self._repos.ct_term_attributes_repository.find_by_uid(
                        term_uid=subtype.name
                    )
                )
                if epoch_sub_type_term.ct_term_vo.name_submission_value is None:
                    name_subm_value = None
                else:
                    name_subm_value = f"{epoch_sub_type_term.ct_term_vo.name_submission_value} {str(epoch_order)}"
                lib = self._repos.library_repository.find_by_name(name="Sponsor")
                library = LibraryVO.from_input_values_2(
                    library_name=lib.library_name,
                    is_library_editable_callback=lambda _: lib.is_editable,
                )
                ct_term_attributes_ar = CTTermAttributesAR.from_input_values(
                    author=self.author,
                    ct_term_attributes_vo=CTTermAttributesVO.from_input_values(
                        codelist_uid=STUDY_EPOCH_EPOCH_UID,
                        catalogue_name=epoch_sub_type_term.ct_term_vo.catalogue_name,
                        code_submission_value=f"{epoch_sub_type_term.ct_term_vo.code_submission_value} {str(epoch_order)}",
                        name_submission_value=name_subm_value,
                        preferred_term=epoch_sub_type_term.ct_term_vo.preferred_term,
                        definition=epoch_sub_type_term.ct_term_vo.definition,
                        codelist_exists_callback=self._repos.ct_codelist_attribute_repository.codelist_exists,
                        catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                        term_exists_by_name_callback=self._repos.ct_term_attributes_repository.term_specific_exists_by_name,
                        term_exists_by_code_submission_value_callback=(
                            self._repos.ct_term_attributes_repository.term_attributes_exists_by_code_submission_value
                        ),
                    ),
                    library=library,
                    generate_uid_callback=self._repos.ct_term_attributes_repository.generate_uid,
                )
                ct_term_attributes_ar.approve(author=self.author)
                self._repos.ct_term_attributes_repository.save(ct_term_attributes_ar)

                ct_term_name_ar = CTTermNameAR.from_input_values(
                    generate_uid_callback=lambda: ct_term_attributes_ar.uid,
                    ct_term_name_vo=CTTermNameVO.from_repository_values(
                        codelist_uid=ct_term_attributes_ar.ct_term_vo.codelist_uid,
                        catalogue_name=ct_term_attributes_ar.ct_term_vo.catalogue_name,
                        name=epoch_name,
                        name_sentence_case=epoch_name.lower(),
                        order=None,
                    ),
                    library=library,
                    author=self.author,
                )
                ct_term_name_ar.approve(author=self.author)
                self._repos.ct_term_name_repository.save(ct_term_name_ar)
                # connecting the created epoch to the corresponding epoch sub type
                self._repos.ct_term_attributes_repository.add_parent(
                    term_uid=ct_term_attributes_ar.uid,
                    parent_uid=epoch_sub_type_term.uid,
                    relationship_type=TermParentType.PARENT_SUB_TYPE,
                )
                # adding newly created sponsor defined epoch term
                if ct_term_name_ar.uid not in StudyEpochEpoch._member_map_:
                    extend_enum(
                        StudyEpochEpoch, ct_term_name_ar.uid, ct_term_name_ar.name
                    )
                epoch = StudyEpochEpoch[ct_term_attributes_ar.uid]
        return epoch

    def _get_epoch_object(
        self,
        epochs_in_subtype: Sequence[StudyEpochVO],
        subtype: StudyEpochSubType,
        after_create: bool = False,
    ):
        # amount of epochs that exists in the specific epoch sub type
        amount_of_epochs_in_subtype = len(epochs_in_subtype)

        # if we are creating a new epoch we need to add 1 to the total amount of epochs withing subtype
        # as newly created epoch doesn't exist yet in epoch subtype
        amount_of_epochs_in_subtype = (
            amount_of_epochs_in_subtype + 1
            if after_create
            else amount_of_epochs_in_subtype
        )
        epoch = self._get_or_create_epoch_in_specific_subtype(
            epoch_order=amount_of_epochs_in_subtype,
            subtype=subtype,
            amount_of_epochs_in_subtype=amount_of_epochs_in_subtype,
        )

        return epoch

    def _get_epoch_type_object(self, subtype: str):
        """
        Gets the epoch type object based on the epoch subtype and allowed configuration loaded in the constructor
        :param subtype:
        :return:
        """
        config_type = None
        for config in self._allowed_configs:
            if config.subtype == subtype:
                config_type = config.type
        return StudyEpochType[config_type]

    def _from_input_values(
        self,
        study_uid: str,
        study_epoch_create_input: StudyEpochCreateInput,
        preview: bool = False,
    ):

        epoch, subtype, epoch_type = self._instantiate_epoch_items(
            study_uid=study_uid,
            study_epoch_create_input=study_epoch_create_input,
            preview=preview,
        )

        return StudyEpochVO(
            study_uid=study_uid,
            start_rule=study_epoch_create_input.startRule,
            end_rule=study_epoch_create_input.endRule,
            description=study_epoch_create_input.description,
            epoch=epoch,
            subtype=subtype,
            epoch_type=epoch_type,
            order=study_epoch_create_input.order,
            start_date=datetime.datetime.now(),
            status=StudyStatus.DRAFT,
            author=self.author,
            color_hash=study_epoch_create_input.colorHash,
        )

    def _edit_study_epoch_vo(
        self,
        study_epoch_to_edit: StudyEpochVO,
        study_epoch_edit_input: StudyEpochEditInput,
    ):
        epoch: Optional[StudyEpochEpoch] = None
        subtype: Optional[StudyEpochSubType] = None
        epoch_type: Optional[StudyEpochType] = None

        # if the epoch subtype wasn't changed in the PATCH payload then we don't have to derive all epoch objects
        # and we can take the epoch, epoch subtype and epoch type from the value object that is being patched
        if study_epoch_to_edit.subtype.name != study_epoch_edit_input.epochSubType:
            all_epochs_in_study = self.repo.find_all_epochs_by_study(
                study_epoch_to_edit.study_uid
            )
            epochs_in_subtype = self._get_list_of_epochs_in_subtype(
                all_epochs=all_epochs_in_study,
                epoch_sub_type=study_epoch_edit_input.epochSubType,
            )
            subtype = StudyEpochSubType[study_epoch_edit_input.epochSubType]
            epoch_type = self._get_epoch_type_object(subtype=subtype.name)
            if study_epoch_edit_input.epoch is not None:
                epoch = StudyEpochEpoch[study_epoch_edit_input.epoch]
            else:
                epoch = self._get_epoch_object(
                    epochs_in_subtype=epochs_in_subtype, subtype=subtype
                )
            # if epoch subtype was modified we have to synchronize the old epoch subtype group
            self._synchronize_epoch_orders(
                epochs_to_synchronize=epochs_in_subtype, all_epochs=all_epochs_in_study
            )
            epochs_in_previous_subtype = self._get_list_of_epochs_in_subtype(
                all_epochs=all_epochs_in_study,
                epoch_sub_type=study_epoch_to_edit.subtype.name,
            )
            # if epoch subtype was modified we have to synchronize the new epoch subtype group
            self._synchronize_epoch_orders(
                epochs_to_synchronize=epochs_in_previous_subtype,
                all_epochs=all_epochs_in_study,
            )

        study_epoch_to_edit.edit_core_properties(
            start_rule=study_epoch_edit_input.startRule,
            end_rule=study_epoch_edit_input.endRule,
            description=study_epoch_edit_input.description,
            epoch=epoch if epoch else study_epoch_to_edit.epoch,
            subtype=subtype if subtype else study_epoch_to_edit.subtype,
            epoch_type=epoch_type if epoch_type else study_epoch_to_edit.epoch_type,
            order=study_epoch_edit_input.order,
            change_description=study_epoch_edit_input.changeDescription,
            color_hash=study_epoch_edit_input.colorHash,
        )

    def _synchronize_epoch_orders(
        self,
        epochs_to_synchronize: Sequence[StudyEpochVO],
        all_epochs: Sequence[StudyEpochVO],
        after_create: bool = False,
    ):
        """
        The following method synchronize the epochs order when some reorder/add/remove action was executed.
        For instance we had the following sequence of study epochs that linked to the following epochs:
        'Treatment 1', 'Treatment 2', 'Treatment 3' and the study epoch that corresponds to 'Treatment 2' was removed.
        In such case we should leave the study epoch connected to the epoch called 'Treatment 1' untouched but we should
        reconnect the Study Epoch that previously was referencing the 'Treatment 3' to 'Treatment 2'
        :param epochs_to_synchronize:
        :return:
        """
        for epoch in epochs_to_synchronize:
            new_order_in_subtype = self._get_order_of_epoch_in_subtype(
                study_epoch_uid=epoch.uid, all_epochs=epochs_to_synchronize
            )
            if new_order_in_subtype != self._get_epoch_number_from_epoch_name(
                epoch.epoch.value
            ):

                # if we are creating a new epoch we need to add 1 to the total amount of epochs withing subtype
                # as newly created epoch doesn't exist yet in epoch subtype
                amount_of_epochs_in_subtype = (
                    len(epochs_to_synchronize) + 1
                    if after_create
                    else len(epochs_to_synchronize)
                )
                new_epoch = self._get_or_create_epoch_in_specific_subtype(
                    epoch_order=new_order_in_subtype,
                    subtype=epoch.subtype,
                    amount_of_epochs_in_subtype=amount_of_epochs_in_subtype,
                )
                epoch.epoch = new_epoch
                new_order_in_all_apochs = self._get_order_of_epoch_in_subtype(
                    study_epoch_uid=epoch.uid, all_epochs=all_epochs
                )
                if new_order_in_all_apochs != epoch.order:
                    epoch.order = new_order_in_all_apochs
                self.repo.save(epoch)

    def _get_list_of_epochs_in_subtype(
        self, all_epochs: Sequence[StudyEpochVO], epoch_sub_type: str
    ) -> Sequence[StudyEpochVO]:
        """
        Returns the list of all epochs within specific epoch sub type.
        :param all_epochs:
        :param epoch_sub_type:
        :return:
        """
        return [epoch for epoch in all_epochs if epoch_sub_type == epoch.subtype.name]

    def _get_order_of_epoch_in_subtype(
        self, study_epoch_uid: str, all_epochs: Sequence[StudyEpochVO]
    ) -> int:
        """
        Gets the order of the epoch in specific epoch subtype.
        For instance for epoch called 'Treatment 5' it should return a 5.
        :param study_epoch_uid:
        :param all_epochs:
        :return:
        """
        epoch_to_get_order = None
        for epoch in all_epochs:
            # if it's the deleted epoch then
            if epoch.uid == study_epoch_uid:
                # is the epoch that needs ordering
                epoch_to_get_order = epoch
                break
        # if the epoch to be deleted is in this subtype then
        if epoch_to_get_order is not None:
            # get the uid of all of them
            subtype_epochs = [epoch.uid for epoch in all_epochs]
            # return the specific index of the deleted one
            return subtype_epochs.index(epoch_to_get_order.uid) + 1
        return 0

    def _get_epoch_number_from_epoch_name(self, epoch_name: str):
        return epoch_name.split()[-1]

    @db.transaction
    def create(self, study_uid: str, study_epoch_input: StudyEpochCreateInput):
        self._validate_creation(study_epoch_input)
        all_epochs = self.repo.find_all_epochs_by_study(study_uid)
        created_study_epoch = self._from_input_values(study_uid, study_epoch_input)

        if study_epoch_input.order:
            if len(all_epochs) + 1 < created_study_epoch.order:
                raise ValueError("Order is too big.")
            for epoch in all_epochs[created_study_epoch.order :]:
                epoch.order += 1
                self.repo.save(epoch)
        else:
            created_study_epoch.order = len(all_epochs) + 1
        updated_item = self.repo.save(created_study_epoch)
        return self._transform_all_to_response_model(updated_item)

    @db.transaction
    def preview(self, study_uid: str, study_epoch_input: StudyEpochCreateInput):
        self._validate_creation(study_epoch_input)
        all_epochs = self.repo.find_all_epochs_by_study(study_uid)
        created_study_epoch = self._from_input_values(
            study_uid, study_epoch_input, preview=True
        )

        if study_epoch_input.order:
            if len(all_epochs) + 1 < created_study_epoch.order:
                raise ValueError("Order is too big.")
            for epoch in all_epochs[created_study_epoch.order :]:
                epoch.order += 1
        else:
            created_study_epoch.order = len(all_epochs) + 1
        created_study_epoch.uid = "preview"
        return self._transform_all_to_response_model(created_study_epoch)

    @db.transaction
    def edit(
        self,
        study_epoch_uid: str,
        study_epoch_input: StudyEpochEditInput,
    ):
        self._validate_update(study_epoch_input)

        study_epoch = self.repo.find_by_uid(study_epoch_uid)
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=study_epoch_input,
            reference_base_model=self._transform_all_to_response_model(study_epoch),
        )
        self._edit_study_epoch_vo(
            study_epoch_to_edit=study_epoch, study_epoch_edit_input=study_epoch_input
        )

        updated_item = self.repo.save(study_epoch)

        return self._transform_all_to_response_model(updated_item)

    @db.transaction
    def reorder(self, study_epoch_uid: str, new_order: int):
        epoch = self.repo.find_by_uid(study_epoch_uid)
        study_epochs = self.repo.find_all_epochs_by_study(epoch.study_uid)
        study_visits = self._repos.study_visit_repository.find_all_visits_by_study_uid(
            epoch.study_uid
        )

        timeline = TimelineAR(epoch.study_uid, _visits=study_visits)
        timeline.collect_visits_to_epochs(study_epochs)
        old_order = 0
        for i, epoch_checked in enumerate(study_epochs):
            if epoch_checked.uid == study_epoch_uid:
                old_order = i
                epoch = epoch_checked

        if new_order < 0:
            raise ValueError("New order cannot be lesser than 0")
        if new_order > len(study_epochs):
            raise ValueError(f"New order cannot be greater than {len(study_epochs)}")
        if new_order > old_order:
            start_order = old_order + 1
            end_order = new_order + 1
            order_modifier = 0
        else:
            start_order = new_order
            end_order = old_order
            order_modifier = 2
        for i in range(start_order, end_order):
            replaced_epoch = study_epochs[i]
            if len(replaced_epoch.visits()) > 0 and len(epoch.visits()) > 0:
                raise ValueError("Cannot reorder epochs that already have visits")
            replaced_epoch.set_order(i + order_modifier)
            self.repo.save(replaced_epoch)
        epoch.set_order(new_order + 1)
        self.repo.save(epoch)
        study_epochs = self.repo.find_all_epochs_by_study(epoch.study_uid)
        epochs_in_subtype = self._get_list_of_epochs_in_subtype(
            all_epochs=study_epochs, epoch_sub_type=epoch.subtype.name
        )
        if len(epochs_in_subtype) > 1:
            # After reordering we need to synchronize the epochs in a given epoch subtype
            # if we had more than one epoch in a given epoch subtype
            self._synchronize_epoch_orders(
                epochs_to_synchronize=epochs_in_subtype, all_epochs=study_epochs
            )
        return self._transform_all_to_response_model(epoch)

    @db.transaction
    def delete(self, study_uid: str, study_epoch_uid: str):

        # get the possible connected StudyDesign Cells attached to it
        design_cells_on_epoch = None
        if self.repo.epoch_specific_has_connected_design_cell(
            study_uid=study_uid, epoch_uid=study_epoch_uid
        ):
            design_cells_on_epoch = self._repos.study_design_cell_repository.get_design_cells_connected_to_epoch(
                study_uid=study_uid, study_epoch_uid=study_epoch_uid
            )

        # delete those StudyDesignCells attached to the StudyEpoch
        if design_cells_on_epoch is not None:
            for i_design_cell in design_cells_on_epoch:

                study_design_cell = (
                    self._repos.study_design_cell_repository.find_by_uid(
                        study_uid=study_uid, uid=i_design_cell.uid
                    )
                )
                self._repos.study_design_cell_repository.delete(
                    study_uid, i_design_cell.uid, self.author
                )
                all_design_cells = self._repos.study_design_cell_repository.find_all_design_cells_by_study(
                    study_uid
                )
                # shift one order more to fit the modified
                for design_cell in all_design_cells[study_design_cell.order - 1 :]:
                    design_cell.order -= 1
                    self._repos.study_design_cell_repository.save(
                        design_cell, author=self.author, create=False
                    )

        # delete the StudyEpoch
        study_epoch = self.repo.find_by_uid(study_epoch_uid)

        study_visits_in_epoch = [
            visit
            for visit in self._repos.study_visit_repository.find_all_visits_by_study_uid(
                study_uid
            )
            if visit.epoch_uid == study_epoch_uid
        ]

        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits_in_epoch)
        visits = timeline.collect_visits_to_epochs(epochs=[study_epoch])
        if len(visits[study_epoch.uid]) > 0:
            raise exceptions.BusinessLogicException(
                "Study Epoch contains assigned Study Visits, it can't be removed"
            )

        study_epoch.delete()

        self.repo.save(study_epoch)
        all_epochs_in_study = self.repo.find_all_epochs_by_study(study_uid)
        epochs_in_subtype = self._get_list_of_epochs_in_subtype(
            all_epochs=all_epochs_in_study, epoch_sub_type=study_epoch.subtype.name
        )
        # After deletion we need to synchronize the epochs in a given epoch subtype
        self._synchronize_epoch_orders(
            epochs_to_synchronize=epochs_in_subtype, all_epochs=all_epochs_in_study
        )

    def _get_allowed_configs(self):
        resp = []
        for item in self.repo.get_allowed_configs():
            resp.append(
                StudyEpochTypes(
                    subtype=item[0],
                    subtype_name=item[1],
                    type=item[2],
                    type_name=item[3],
                )
            )
        return resp

    @db.transaction
    def get_allowed_configs(self):
        return self._allowed_configs

    @db.transaction
    def audit_trail(
        self,
        epoch_uid: str,
        study_uid: str,
    ) -> Sequence[StudyEpochVersion]:
        all_versions = self.repo.get_all_versions(uid=epoch_uid, study_uid=study_uid)
        versions = [
            self._transform_all_to_response_model(_).dict() for _ in all_versions
        ]
        data = calculate_diffs(versions, StudyEpochVersion)
        return data

    @db.transaction
    def audit_trail_all_epochs(
        self,
        study_uid: str,
    ) -> Sequence[StudyEpochVersion]:
        data = calculate_diffs_history(
            get_all_object_versions=self.repo.get_all_epoch_versions,
            transform_all_to_history_model=self._transform_all_to_response_model,
            study_uid=study_uid,
            version_object_class=StudyEpochVersion,
        )
        return data

    def get_distinct_values_for_header(
        self,
        study_uid: str,
        field_name: str,
        search_string: Optional[str] = "",
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        result_count: int = 10,
    ):
        all_items = self.get_all_epochs(study_uid=study_uid)

        header_values = service_level_generic_header_filtering(
            items=all_items.items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
        )

        return header_values
