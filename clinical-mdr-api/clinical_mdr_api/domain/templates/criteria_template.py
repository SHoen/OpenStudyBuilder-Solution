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
class CriteriaTemplateAR(TemplateAggregateRootBase):
    """
    A specific Criteria Template AR. It can be used to customize Criteria Template
    behavior. Inherits generic template versioning behaviors
    """

    _type: Tuple[CTTermNameAR, CTTermAttributesAR] = ()

    _indications: Optional[Sequence[DictionaryTermAR]] = None

    _categories: Optional[Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]]] = None

    _sub_categories: Optional[Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]]] = None

    @property
    def type(self) -> Tuple[CTTermNameAR, CTTermAttributesAR]:
        return self._type

    @property
    def indications(self) -> Sequence[DictionaryTermAR]:
        return self._indications

    @property
    def categories(self) -> Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]]:
        return self._categories

    @property
    def sub_categories(self) -> Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]]:
        return self._sub_categories

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
        criteria_type: Tuple[CTTermNameAR, CTTermAttributesAR] = None,
        indications: Optional[Sequence[DictionaryTermAR]] = None,
        categories: Optional[Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]]] = None,
        sub_categories: Optional[
            Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]]
        ] = None,
    ) -> "TemplateAggregateRootBase":
        ar = cls(
            _uid=uid,
            _editable_instance=editable_instance,
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
            _type=criteria_type,
            _indications=indications,
            _categories=categories,
            _sub_categories=sub_categories,
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
        criteria_type: Tuple[CTTermNameAR, CTTermAttributesAR] = None,
        indications: Optional[Sequence[DictionaryTermAR]] = None,
        categories: Optional[Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]]] = None,
        sub_categories: Optional[
            Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]]
        ] = None
    ) -> "CriteriaTemplateAR":
        ar: CriteriaTemplateAR = super().from_input_values(
            author=author,
            editable_instance=editable_instance,
            template=template,
            library=library,
            template_value_exists_callback=template_value_exists_callback,
            generate_uid_callback=generate_uid_callback,
        )
        ar._type = criteria_type
        ar._indications = indications
        ar._categories = categories
        ar._sub_categories = sub_categories

        return ar
