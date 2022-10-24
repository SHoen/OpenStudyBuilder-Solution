from typing import Optional

from clinical_mdr_api.repositories import libraries as libraries_repository


def get_libraries(is_editable: Optional[bool]):
    return libraries_repository.find_all(is_editable)


def create(name: str, is_editable: bool):
    return libraries_repository.create(name, is_editable)
