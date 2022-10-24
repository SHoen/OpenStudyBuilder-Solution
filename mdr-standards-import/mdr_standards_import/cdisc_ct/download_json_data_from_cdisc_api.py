import json
from typing import Sequence
import requests
from requests.exceptions import HTTPError
from os import listdir
from os import environ
from os import mkdir
from os import path
from mdr_standards_import.cdisc_ct.entities.package import Package
from mdr_standards_import.cdisc_ct.entities.ct_import import CTImport
from mdr_standards_import.cdisc_ct.utils import get_cdisc_neo4j_driver, is_newer_than
from neo4j.exceptions import ServiceUnavailable


CDISC_IMPORT_DATABASE = environ.get("NEO4J_CDISC_IMPORT_DATABASE", "cdisc-ct")
AUTH_TOKEN = environ.get("CDISC_AUTH_TOKEN")
HEADERS = {'api-key': AUTH_TOKEN, 'Accept': 'application/json'}
BASE_URL = environ.get("CDISC_BASE_URL")


def download_newer_packages_than(last_effective_date: str, to_directory: str):
    """
    Downloads those packages from the CDISC REST API where the effective date is newer than the specified
    <last_effective_date>.
    Stores the data in JSON files on disc.

    :param last_effective_date: string (YYYY-MM-DD, e.g. "2020-12-31"), the date of the last loaded package.
        Only packages newer than this date will be loaded. May be None: in that case 2014-01-01 is used as default date.
    """

    if last_effective_date is None:
        last_effective_date = '2014-01-01'
    
    print(f"Checking for packages newer than the effective_date='{last_effective_date}'.", end="")

    available_packages_json_data = get_available_packages_meta_data_from_cdisc_api_as_json()

    packages_to_load = []
    for package in available_packages_json_data['_links']['packages']:
        href = package["href"]
        # example for the href property: "/mdr/ct/packages/adamct-2014-09-26"
        # the package_id is the part of the href after the last slash (/)
        # e.g. "adamct-2014-09-26"
        package_id = path.basename(href)
        # Strip off the date
        name = package_id.rsplit("-",3)[0]
        # the effective date is at the end of the package id
        # e.g. "2014-09-26"
        effective_date = "-".join(package_id.rsplit("-",3)[-3:])
        ct_import = CTImport(effective_date, "TMP")
        if is_newer_than(effective_date, last_effective_date):
            package = Package(ct_import)
            package.set_catalogue_name(href)
            package.set_href(href)
            packages_to_load.append(package)

    if len(packages_to_load) > 0:
        download_packages_data(packages_to_load, to_directory)
    else:
        print(f" -> No packages found for downloading.")


def get_available_packages_meta_data_from_cdisc_api_as_json():
    """
    Gets the CT packages list from the CDISC REST API.

    The JSON result has the following form:
    {
        "_links": {
            "self": {
                "href": "/mdr/ct/packages",
                "title": "Product Group Terminology",
                "type": "Controlled Terminology Package List"
            },
            "packages": [
                {
                    "href": "/mdr/ct/packages/sdtmct-2019-12-20",
                    "title": "SDTM Controlled Terminology Package 40 Effective 2019-12-20",
                    "type": "Terminology"
                }
            ]
        }
    }
    """
    response = requests.get(BASE_URL + '/mdr/ct/packages', headers=HEADERS)
    response.raise_for_status()
    return response.json()


def download_packages_data(packages_to_download: Sequence[Package], to_directory: str):
    """
    Downloads the CDISC CT package data for those packages specified by <packages_to_download>.
    Stores the data in JSON files on disc.

    If the corresponding JSON files are already present for one or more packages, those packages will be skipped.

    :param packages_to_download: a list of those packages that shall be downloaded.
    """

    create_cdisc_data_dir(to_directory)
    print("")
    print(f"Storing files in directory='{to_directory}'.")
    existing_packages = set([path.splitext(path.basename(x))[0]
                            for x in listdir(to_directory) if path.splitext(x)[1] == ".json"])
    step = 1
    number_of_packages = len(packages_to_download)
    for package in packages_to_download:
        package_id = package.catalogue_name + '-' + package.get_ct_import().effective_date
        if (path.basename(package_id.lower()) in existing_packages):
            print(
                f"  Step: {step}/{number_of_packages} - Package '{package_id}' already downloaded.")
        else:
            print(
                f"  Step: {step}/{number_of_packages} - Downloading package '{package_id}'.")
            try:
                response = requests.get(
                    BASE_URL + package.href, headers=HEADERS)
                response.raise_for_status()
                package_data = response.json()
            except HTTPError as http_err:
                print(f'    HTTP error occurred: {http_err}')
            except Exception as err:
                print(f'    Other error occurred: {err}')
            else:
                filename = package_id.split("/")[-1].lower() + ".json"
                with open(path.join(to_directory, filename), 'w') as ctpkg_file:
                    ctpkg_file.write(json.dumps(package_data))
                    ctpkg_file.write('\n')
        step += 1


def create_cdisc_data_dir(directory: str):
    try:
        mkdir(directory, 0o750)
    except OSError as error:
        # ignore [Errno 17] File exists
        if error.errno != 17:
            print(error)


def get_latest_effective_date():
    cdisc_neo4j_driver = get_cdisc_neo4j_driver()
    try:
        with cdisc_neo4j_driver.session(database="system") as session:
            session.run("CREATE DATABASE $database IF NOT EXISTS", database=CDISC_IMPORT_DATABASE)
    except ServiceUnavailable:
        print("Can't connect to neo4j database, using default latest date")
        return None

    with cdisc_neo4j_driver.session(database=CDISC_IMPORT_DATABASE) as session:
        with session.begin_transaction() as tx:
            record = tx.run(
                """
                MATCH (import:Import)
                WITH import.effective_date AS effective_date
                ORDER BY effective_date DESC
                LIMIT 1
                RETURN
                    effective_date.year + '-' + right('0' + effective_date.month, 2) + '-' + right('0' + effective_date.day, 2)
                        AS effective_date
                """
            ).single()
            return record['effective_date'] if record is not None else None


def download_json_data_from_cdisc_api(to_directory: str):
    download_newer_packages_than(get_latest_effective_date(), to_directory)
