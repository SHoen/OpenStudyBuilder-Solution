from unittest.mock import Mock, patch

from hypothesis import given
from hypothesis.strategies import booleans, composite, text

from clinical_mdr_api.domain_repositories.library.library_repository import (
    LibraryRepository,
)
from clinical_mdr_api.domain_repositories.models.generic import Library


@composite
def library_nodes(draw):
    return Library(name=draw(text()), is_editable=draw(booleans()))


@given(library_node=library_nodes())
@patch(LibraryRepository.__module__ + ".LibraryAR")
@patch(LibraryRepository.__module__ + ".Library")
def test__library_repository_impl__find_by_name__existing_library__result(
    library_mock, library_ar_mock, *, library_node: Library
):
    # given
    repo = LibraryRepository()
    library_mock.nodes.get_or_none.return_value = library_node
    library_ar_mock.from_repository_values.return_value = Mock()
    name = library_node.name
    is_editable = library_node.is_editable

    # when
    repo.find_by_name(name)

    # then
    library_ar_mock.from_repository_values.assert_called_once_with(
        library_name=name, is_editable=is_editable
    )


@given(library_name=text())
@patch(LibraryRepository.__module__ + ".Library")
def test__library_repository_impl__find_by_name__non_existing_library__result(
    library_mock, *, library_name: str
):
    # given
    repo = LibraryRepository()
    library_mock.nodes.get_or_none.return_value = None

    # when
    find_by_name_result = repo.find_by_name(library_name)

    # then
    assert find_by_name_result is None
