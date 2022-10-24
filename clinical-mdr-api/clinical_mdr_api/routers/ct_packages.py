"""CTPackage router."""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.services.ct_package import CTPackageService

router = APIRouter()
CTCodelistUid = Path(None, description="The unique id of the CTCodelist")


@router.get(
    "/packages",
    summary="Returns all controlled terminology packages.",
    response_model=List[models.CTPackage],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_packages(
    catalogue_name: Optional[str] = Query(
        None,
        description="If specified, only packages from given catalogue are returned.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_package_service = CTPackageService(current_user_id)
    return ct_package_service.get_all_ct_packages(catalogue_name=catalogue_name)


@router.get(
    "/packages/changes",
    summary="Returns changes between codelists and terms inside two different packages.",
    response_model=models.CTPackageChanges,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_packages_changes_between_codelists_and_terms(
    catalogue_name: str,
    old_package_date: date = Query(
        ...,
        description="The date for the old package, for instance '2020-03-27'"
        "\nThe possible dates for given catalogue_name can be retrieved by the /ct/packages/dates endpoint",
    ),
    new_package_date: date = Query(
        ...,
        description="The datetime for the new package, for instance '2020-06-26'"
        "\nThe possible dates for given catalogue_name can be retrieved by the /ct/packages/dates endpoint",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_package_service = CTPackageService(current_user_id)
    return ct_package_service.get_ct_packages_changes(
        catalogue_name=catalogue_name,
        old_package_date=old_package_date,
        new_package_date=new_package_date,
    )


@router.get(
    "/packages/{codelistuid}/changes",
    summary="Returns changes from given codelist and all associated terms inside two different packages.",
    response_model=models.CTPackageChangesSpecificCodelist,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_packages_changes_between_codelist_and_all_associated_terms(
    catalogue_name: str,
    codelistuid: str = CTCodelistUid,
    old_package_date: date = Query(
        ...,
        description="The date for the old package, for instance '2020-03-27'"
        "\nThe possible dates for given catalogue_name can be retrieved by the /ct/packages/dates endpoint",
    ),
    new_package_date: date = Query(
        ...,
        description="The date for the new package, for instance '2020-06-26'"
        "\nThe possible dates for given catalogue_name can be retrieved by the /ct/packages/dates endpoint",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_package_service = CTPackageService(current_user_id)
    return ct_package_service.get_ct_packages_codelist_changes(
        catalogue_name=catalogue_name,
        old_package_date=old_package_date,
        new_package_date=new_package_date,
        codelist_uid=codelistuid,
    )


@router.get(
    "/packages/dates",
    summary="Returns all effective dates for packages in a given catalogue.",
    response_model=models.CTPackageDates,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_package_dates(
    catalogue_name: str, current_user_id: str = Depends(get_current_user_id)
):
    ct_package_service = CTPackageService(current_user_id)
    return ct_package_service.get_all_effective_dates(catalogue_name=catalogue_name)
