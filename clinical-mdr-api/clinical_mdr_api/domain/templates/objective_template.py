from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.domain.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    InstantiationCountsVO,
    LibraryItemMetadataVO,
    LibraryVO,
    TemplateAggregateRootBase,
    TemplateVO,
)


@dataclass
class ObjectiveTemplateAR(TemplateAggregateRootBase):
    """
    A specific Objective Template AR. It can be used to customize Objective Template
    behavior. Inherits generic template versioning behaviors
    """

    _confirmatory_testing: Optional[bool] = None

    _indications: Optional[Sequence[DictionaryTermAR]] = None

    _categories: Optional[Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]]] = None

    @property
    def confirmatory_testing(self) -> bool:
        return self._confirmatory_testing

    @property
    def indications(self) -> Sequence[DictionaryTermAR]:
        return self._indications

    @property
    def categories(self) -> Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]]:
        return self._categories

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        editable_instance: bool,
        template: TemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        study_count: Optional[int] = None,
        counts: Optional[InstantiationCountsVO] = None,
        confirmatory_testing: Optional[bool] = None,
        indications: Optional[Sequence[DictionaryTermAR]] = None,
        categories: Optional[Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]]] = None,
    ) -> "TemplateAggregateRootBase":
        ar = cls(
            _uid=uid,
            _editable_instance=editable_instance,
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
            _confirmatory_testing=confirmatory_testing,
            _indications=indications,
            _categories=categories,
            _study_count=study_count,
            _counts=counts,
        )
        return ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        editable_instance: bool,
        template: TemplateVO,
        library: LibraryVO,
        template_value_exists_callback: Callable[
            [TemplateVO], bool
        ],  # = (lambda _: False),
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
        confirmatory_testing: Optional[bool] = None,
        indications: Optional[Sequence[DictionaryTermAR]] = None,
        categories: Optional[Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]]] = None
    ) -> "ObjectiveTemplateAR":
        ar: ObjectiveTemplateAR = super().from_input_values(
            author=author,
            editable_instance=editable_instance,
            template=template,
            library=library,
            template_value_exists_callback=template_value_exists_callback,
            generate_uid_callback=generate_uid_callback,
        )
        ar._confirmatory_testing = confirmatory_testing
        ar._indications = indications
        ar._categories = categories

        return ar
