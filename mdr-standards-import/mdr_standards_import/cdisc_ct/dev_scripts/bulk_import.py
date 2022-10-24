"""
This script is not meant to be called by the automatic pipelines.

This script is meant to be called e.g. via:

> `python -m pipenv run bulk_import <user initials> <JSON directory name> <skip download step>`

The script expects the following parameters:

1. <user initials> - The Novo Nordisk user initials of the person who started the process: String, e.g. "MT", "TKQT", ...
2. <JSON directory name> - Optional, default "". The directory name where the JSON files are stored. It can be absolute or relative.
    If relative (or empty), the passed directory name will be appended to the content of the environment variable 'CDISC_DATA_DIR'.
    String, E.g. "", "subset-1", "/my/absoulte/path/to/json-files"
3. <skip download step> - Optional, default "false". Denotes whether or not the download step is skipped. String, e.g. "true" or "false"
"""
from os import environ

from mdr_standards_import.cdisc_ct.utils import get_directory_name, get_ordered_package_dates, get_skip_download_step, get_user_initials
#from mdr_standards_import.cdisc_ct.wrapper.wrapper_automatic_resolution_of_inconsistencies import wrapper_automatic_resolution_of_inconsistencies
from mdr_standards_import.cdisc_ct.wrapper.wrapper_import_cdisc_ct_into_cdisc_ct_db import wrapper_import_cdisc_ct_into_cdisc_ct_db
from mdr_standards_import.cdisc_ct.wrapper.wrapper_import_from_cdisc_ct_db_into_mdr import wrapper_import_from_cdisc_ct_db_into_mdr


CDISC_DIR = environ.get("CDISC_DATA_DIR", "json_data/packages")


def bulk_import(user_initials: str, json_data_directory: str = '', skip_download_step: bool = False):
    wrapper_import_cdisc_ct_into_cdisc_ct_db(user_initials, json_data_directory, skip_download_step)
    #wrapper_automatic_resolution_of_inconsistencies()

    package_dates = get_ordered_package_dates(json_data_directory)
    for effective_date in package_dates:
        wrapper_import_from_cdisc_ct_db_into_mdr(user_initials, effective_date)

if __name__ == "__main__":
    bulk_import(get_user_initials(1), get_directory_name(2), get_skip_download_step(3))
