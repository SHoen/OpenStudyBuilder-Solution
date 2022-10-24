from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from clinical_mdr_api.domain.concepts.concept_base import (
    ConceptARBase,
    ConceptVO,
    _AggregateRootType,
    _ConceptVOType,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass(frozen=True)
class ActivityInstanceVO(ConceptVO):
    """
    The ActivityInstanceVO acts as the value object for a single ActivityInstance aggregate
    """

    topic_code: str
    adam_param_code: str
    legacy_description: Optional[str]
    sdtm_variable_uid: Optional[str]
    sdtm_variable_name: Optional[str]
    sdtm_subcat_uid: Optional[str]
    sdtm_subcat_name: Optional[str]
    sdtm_cat_uid: Optional[str]
    sdtm_cat_name: Optional[str]
    sdtm_domain_uid: Optional[str]
    sdtm_domain_name: Optional[str]
    activity_uids: Sequence[str]
    specimen_uid: Optional[str]
    specimen_name: Optional[str]
    activity_type: Optional[str]

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: str,
        definition: str,
        abbreviation: Optional[str],
        topic_code: str,
        adam_param_code: str,
        legacy_description: Optional[str],
        sdtm_variable_uid: Optional[str],
        sdtm_variable_name: Optional[str],
        sdtm_subcat_uid: Optional[str],
        sdtm_subcat_name: Optional[str],
        sdtm_cat_uid: Optional[str],
        sdtm_cat_name: Optional[str],
        sdtm_domain_uid: Optional[str],
        sdtm_domain_name: Optional[str],
        activity_uids: Sequence[str],
        specimen_uid: Optional[str],
        specimen_name: Optional[str],
        activity_type: Optional[str],
    ) -> "ActivityInstanceVO":
        activity_instance_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            activity_type=activity_type,
            topic_code=topic_code,
            adam_param_code=adam_param_code,
            legacy_description=legacy_description,
            sdtm_variable_uid=sdtm_variable_uid,
            sdtm_variable_name=sdtm_variable_name,
            sdtm_subcat_uid=sdtm_subcat_uid,
            sdtm_subcat_name=sdtm_subcat_name,
            sdtm_cat_uid=sdtm_cat_uid,
            sdtm_cat_name=sdtm_cat_name,
            sdtm_domain_uid=sdtm_domain_uid,
            sdtm_domain_name=sdtm_domain_name,
            specimen_uid=specimen_uid,
            specimen_name=specimen_name,
            activity_uids=activity_uids if activity_uids is not None else [],
        )

        return activity_instance_vo

    def validate(
        self,
        activity_hierarchy_exists_by_uid_callback: Callable[[str], bool],
        ct_term_exists_callback: Callable[[str], bool],
        activity_exists_by_name_callback: Callable[[str], bool] = None,
        previous_name: Optional[str] = None,
    ) -> None:

        if activity_exists_by_name_callback(self.name) and self.name != previous_name:
            raise ValueError(
                f"{self.__class__.__name__} with name ({self.name}) already exists"
            )

        for activity in self.activity_uids:
            if not activity_hierarchy_exists_by_uid_callback(activity):
                raise ValueError(
                    f"{self.__class__.__name__} tried to connect to non existing Activity identified by uid ({activity})"
                )

        if self.sdtm_variable_uid is not None and not ct_term_exists_callback(
            self.sdtm_variable_uid
        ):
            raise ValueError(
                f"{self.__class__.__name__} tried to connect to non existing sdtm variable identified by uid ({self.sdtm_variable_uid})"
            )
        if self.sdtm_subcat_uid is not None and not ct_term_exists_callback(
            self.sdtm_subcat_uid
        ):
            raise ValueError(
                f"{self.__class__.__name__} tried to connect to non existing sdtm subcat identified by uid ({self.sdtm_subcat_uid})"
            )
        if self.sdtm_cat_uid is not None and not ct_term_exists_callback(
            self.sdtm_cat_uid
        ):
            raise ValueError(
                f"{self.__class__.__name__} tried to connect to non existing sdtm cat identified by uid ({self.sdtm_cat_uid})"
            )
        if self.sdtm_domain_uid is not None and not ct_term_exists_callback(
            self.sdtm_domain_uid
        ):
            raise ValueError(
                f"{self.__class__.__name__} tried to connect to non existing sdtm domain identified by uid ({self.sdtm_domain_uid})"
            )


@dataclass
class ActivityInstanceAR(ConceptARBase):
    _concept_vo: ActivityInstanceVO

    @property
    def concept_vo(self) -> _ConceptVOType:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: _ConceptVOType,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> _AggregateRootType:
        activity_ar = cls(
            _uid=uid,
            _concept_vo=concept_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return activity_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        concept_vo: _ConceptVOType,
        library: LibraryVO,
        concept_exists_by_name_callback: Callable[[str], bool],
        activity_hierarchy_exists_by_uid_callback: Callable[[str], bool],
        ct_term_exists_callback: Callable[[str], bool],
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
    ) -> _AggregateRootType:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        if not library.is_editable:
            raise ValueError(
                f"The library with the name='{library.name}' does not allow to create objects."
            )

        concept_vo.validate(
            activity_exists_by_name_callback=concept_exists_by_name_callback,
            activity_hierarchy_exists_by_uid_callback=activity_hierarchy_exists_by_uid_callback,
            ct_term_exists_callback=ct_term_exists_callback,
        )

        activity_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return activity_ar

    def edit_draft(
        self,
        author: str,
        change_description: Optional[str],
        concept_vo: _ConceptVOType,
        concept_exists_by_name_callback: Callable[[str], bool],
        activity_hierarchy_exists_by_uid_callback: Callable[[str], bool] = None,
        ct_term_exists_callback: Callable[[str], bool] = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            activity_exists_by_name_callback=concept_exists_by_name_callback,
            activity_hierarchy_exists_by_uid_callback=activity_hierarchy_exists_by_uid_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            previous_name=self.name,
        )
        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
