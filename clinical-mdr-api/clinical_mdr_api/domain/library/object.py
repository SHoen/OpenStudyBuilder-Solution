import datetime
from dataclasses import dataclass
from functools import reduce
from operator import add
from typing import AbstractSet, Callable, Optional, Sequence

from clinical_mdr_api.domain._utils import (
    convert_to_plain,
    extract_parameters,
    strip_html,
)
from clinical_mdr_api.domain.library.parameter_value import ParameterValueEntryVO
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
    TemplateVO,
)


@dataclass(frozen=True)
class ParametrizedTemplateVO:
    """
    Object representing template with proper parameter setting.
    Allows for creation of proper object name
    """

    template_name: str
    template_uid: str
    parameter_values: Sequence[ParameterValueEntryVO]

    @classmethod
    def from_repository_values(
        cls,
        *,
        template_name: str,
        template_uid: str,
        parameter_values: Sequence[ParameterValueEntryVO]
    ) -> "ParametrizedTemplateVO":
        """
        Creates object based on repository values
        """
        return cls(
            template_uid=template_uid,
            template_name=template_name,
            parameter_values=tuple(parameter_values),
        )

    @classmethod
    def from_input_values_2(
        cls,
        *,
        template_uid: str,
        parameter_values: Sequence[ParameterValueEntryVO],
        name_override: Optional[str] = None,
        is_instance_editable_callback: Optional[Callable[[str], bool]] = None,
        get_final_template_vo_by_template_uid_callback: Callable[
            [str], Optional[TemplateVO]
        ]
    ) -> "ParametrizedTemplateVO":
        """
        Creates object based on external input
        """
        template = get_final_template_vo_by_template_uid_callback(template_uid)

        if template is None:
            raise ValueError(
                "The template was not found. Make sure that there is a latest 'Final' version."
            )

        # TODO: is there replacement?
        # if [_.parameter_name for _ in parameter_values] != list(template.parameter_names):
        #    raise ValueError("Parameter value list does not match template defined parameter list")

        if name_override is not None:
            if extract_parameters(name_override) != extract_parameters(template.name):
                raise ValueError(
                    "Name override does not match template defined parameter list"
                )
            if not is_instance_editable_callback(template_uid):
                raise ValueError(
                    "Editing the name of an instance of this template is not allowed"
                )

        return cls(
            template_name=name_override if name_override is not None else template.name,
            template_uid=template_uid,
            parameter_values=tuple(parameter_values),
        )

    @classmethod
    def from_name_and_parameter_values(
        cls,
        name: str,
        template_uid: str,
        parameter_values: Sequence[ParameterValueEntryVO],
    ) -> "ParametrizedTemplateVO":
        return cls(
            template_name=name,
            template_uid=template_uid,
            parameter_values=parameter_values,
        )

    @staticmethod
    def _create_name_from_template(
        template_name: str, parameter_values: Sequence[ParameterValueEntryVO]
    ) -> str:
        """
        Calculates current name based on template name and current list of parameters
        """
        name = template_name
        template_parameters = extract_parameters(template_name)
        if parameter_values is not None:
            for i, param in enumerate(parameter_values):
                values = param.parameters
                conjunction = param.conjunction
                if len(values) == 0:
                    # If no values are selected, the template will be filled in without a name.
                    combined_name = ""
                elif len(values) == 1:
                    # if only one value is present (c.q. no conjunctions) we just use this value.
                    combined_name = values[0].value
                else:
                    # Use a Python reduce function to combine the values array and the conjunctions array into a string.
                    # We use comma's for the first few items, and the specified conjuction word between the last two.
                    combined_name = reduce(
                        add,
                        [
                            str(values[x].value)
                            + ParametrizedTemplateVO.generate_template_value_seperator(
                                template_name,
                                parameter_values,
                                template_parameters[i],
                                i,
                                values,
                                x,
                                conjunction,
                            )
                            for x in range(len(values) - 1)
                        ],
                    ) + str(values[len(values) - 1].value)
                name = name.replace(
                    "[" + template_parameters[i] + "]", "[" + combined_name + "]", 1
                )

            # Clean up extra spacing, unneeded brackets, etc.
            name = ParametrizedTemplateVO.clean_instantiation_name(name)
        return name

    @staticmethod
    def clean_instantiation_name(name):
        # Filter out unneeded brackets, double spaces, and extra spacing around the string.
        replacement_rules = {
            "([])": "[]",
            "[NA]": "[]",
            ",,": ",",
            "  ": " ",
            "[] []": "[][]",
            "[] ([": "[]([",
            "[) []": "])[]",
            "] and []": "][]",
            "[] and [": "[][",
            "], []": "][]",
            "[], [": "[][",
            "] or []": "][]",
            "[] or [": "[][",
            "] []": "][]",
            "[] [": "[][",
            "()": "",
            "(,)": "",
        }
        for original, replacement in replacement_rules.items():
            while original in name:
                name = name.replace(original, replacement)
        name = name.strip()
        return name

    @staticmethod
    def generate_template_value_seperator(
        template,
        parameter_values,
        parameter_name,
        template_index,
        values,
        index,
        conjunction,
    ) -> str:

        # We check if there's a 'joined' parameter value following the current one.
        # This, for example, ensure that we generate:
        # "To investigate [A,B,C] and [D]"
        # instead of:
        # "To investigate [A,B and C] and [D]".
        text_after_parameter = template.split("[" + parameter_name + "]")[1]
        next_parameter_has_value = (
            template_index < len(parameter_values) - 1
            and len(parameter_values[template_index + 1].parameters) > 0
        )
        has_joined_parameter_value = (
            next_parameter_has_value
            and text_after_parameter.strip().startswith(conjunction)
        )

        if index < (len(values) - 2) or has_joined_parameter_value:
            return ", "
        return " " + conjunction + " "

    @property
    def template_name_plain(self) -> str:
        return strip_html(self.template_name)

    @property
    def expanded_template_value(self) -> str:
        return self._create_name_from_template(
            template_name=self.template_name, parameter_values=self.parameter_values
        )

    @property
    def expanded_plain_template_value(self) -> str:
        name = self._create_name_from_template(
            template_name=self.template_name,
            parameter_values=self.parameter_values,
        )
        return convert_to_plain(name)


@dataclass
class ParametrizedTemplateARBase(LibraryItemAggregateRootBase):
    """
    Aggregate root supporting template derived object with proper parametrization

    """

    CASCADING_UPDATE_LABEL = "Cascading update triggered by template update uid: '{}'"  # TODO: put reference with uid
    # inheritance from class with default values
    _template: ParametrizedTemplateVO

    _study_count: Optional[int] = None

    @property
    def study_count(self) -> int:
        return self._study_count

    @classmethod
    def _from_repository_values(
        cls,
        *,
        library: LibraryVO,
        uid: str,
        item_metadata: LibraryItemMetadataVO,
        study_count: Optional[int],
        **kwargs
    ) -> "LibraryItemAggregateRootBase":
        # noinspection PyArgumentList
        # pylint:disable=no-value-for-parameter
        return cls(
            _uid=uid,
            _library=library,  # type: ignore
            _item_metadata=item_metadata,
            _study_count=study_count**kwargs,
        )

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        template: ParametrizedTemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        study_count: Optional[int] = None,
    ) -> "ParametrizedTemplateARBase":
        ar = cls(
            _uid=uid,
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
            _study_count=study_count,
        )

        return ar

    @classmethod
    def from_input_values(
        cls,
        author: str,
        library: LibraryVO,
        template: ParametrizedTemplateVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
    ) -> "ParametrizedTemplateARBase":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        ar = cls(
            _uid=generate_uid_callback(),
            _library=library,
            _template=template,
            _item_metadata=item_metadata,
        )
        return ar

    def edit_draft(
        self, author: str, change_description: str, template: ParametrizedTemplateVO
    ):
        """
        Creates a new draft version for the object.
        """
        if self._template != template:
            super()._edit_draft(change_description=change_description, author=author)
            self._template = template

    def cascade_update(
        self,
        author: str,
        date: datetime.datetime,
        new_template_name: str,
        change_description: str = CASCADING_UPDATE_LABEL,
    ):
        change_description = change_description.format(self.template_uid)
        self._template = ParametrizedTemplateVO.from_name_and_parameter_values(
            new_template_name,
            self.template_uid,
            self._template.parameter_values,
        )
        self._item_metadata = self._item_metadata.new_version_start_date(
            author=author, change_description=change_description, date=date
        )

    @property
    def template_uid(self) -> str:
        return self._template.template_uid

    @property
    def template_name(self) -> str:
        return self._template.template_name

    @property
    def template_name_plain(self) -> str:
        return self._template.template_name_plain

    @property
    def name(self) -> str:
        return self._template.expanded_template_value

    @property
    def name_plain(self) -> str:
        return self._template.expanded_plain_template_value

    def get_parameters(self) -> Sequence[ParameterValueEntryVO]:
        return self._template.parameter_values

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if (
            self._item_metadata.status == LibraryItemStatus.DRAFT
            and self._item_metadata.major_version == 0
        ):
            return {ObjectAction.APPROVE, ObjectAction.EDIT, ObjectAction.DELETE}
        if self._item_metadata.status == LibraryItemStatus.DRAFT:
            return {ObjectAction.APPROVE, ObjectAction.EDIT}
        if self._item_metadata.status == LibraryItemStatus.FINAL:
            return {ObjectAction.INACTIVATE}
        if self._item_metadata.status == LibraryItemStatus.RETIRED:
            return {ObjectAction.REACTIVATE}
        return frozenset()
