from typing import cast

from neomodel import db
from pydantic import BaseModel

from clinical_mdr_api.domain.library.library_ar import LibraryAR
from clinical_mdr_api.domain.template_parameters import ParameterTemplateAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryVO,
    TemplateVO,
    VersioningException,
)
from clinical_mdr_api.domain_repositories.templates.parameter_template_repository import (
    ParameterTemplateRepository,
)
from clinical_mdr_api.exceptions import (
    BusinessLogicException,
    NotFoundException,
    ValidationException,
)
from clinical_mdr_api.models.complex_parameter_template import (
    ComplexParameterTemplate,
    ComplexParameterTemplateCreateInput,
    ComplexParameterTemplateVersion,
)
from clinical_mdr_api.services.generic_template_service import (
    GenericTemplateService,  # type: ignore
)


class ComplexParameterTemplateService(GenericTemplateService[ParameterTemplateAR]):
    aggregate_class = ParameterTemplateAR
    version_class = ComplexParameterTemplateVersion
    repository_interface = ParameterTemplateRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ParameterTemplateAR
    ) -> ComplexParameterTemplate:
        return ComplexParameterTemplate.from_parameter_template_ar(item_ar)

    def create(
        self, template: ComplexParameterTemplateCreateInput
    ) -> ComplexParameterTemplate:
        # TODO: do sth for better typing
        # This function is not decorated with db.transaction as internal transactions
        # are handled manually by "with" statement.
        try:
            # Transaction that is performing initial save
            with db.transaction:
                # TODO: prepare proper validation
                template_vo = TemplateVO.from_input_values_2(
                    template_name=template.name,
                    parameter_name_exists_callback=lambda x: True,
                )

                try:
                    library_vo = LibraryVO.from_input_values_2(
                        library_name=template.libraryName,
                        is_library_editable_callback=(
                            lambda name: (
                                cast(
                                    LibraryAR,
                                    self._repos.library_repository.find_by_name(name),
                                ).is_editable
                                if self._repos.library_repository.find_by_name(name)
                                is not None
                                else None
                            )
                        ),
                    )
                except ValueError as exc:
                    raise NotFoundException(
                        f"The library with the name='{template.libraryName}' could not be found."
                    ) from exc
                try:
                    item = ParameterTemplateAR.from_input_values(
                        author=self.user_initials,
                        parameter_name=template.parameterName,
                        library=library_vo,
                        template=template_vo,
                    )
                except ValueError as e:
                    raise ValidationException(e.args[0]) from e

                self.repository.save(item)

            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

    def approve_cascade(self, uid: str) -> None:
        raise NotImplementedError("This function is not implemented")

    @db.transaction
    def edit_draft(self, uid: str, template: BaseModel) -> BaseModel:
        try:
            # TODO: find better validation
            template_vo = TemplateVO.from_input_values_2(
                template_name=template.name,
                parameter_name_exists_callback=lambda x: True,
            )

            item = self._find_by_uid_or_raise_not_found(uid, for_update=True)

            item.edit_draft(
                author=self.user_initials,
                change_description=template.changeDescription,
                template=template_vo,
            )
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e
