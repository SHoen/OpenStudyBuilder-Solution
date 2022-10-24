import logging
from functools import wraps
from typing import Dict
from collections.abc import Callable
import time

import aiohttp
import requests

from importers.metrics import Metrics
from .api_bindings import ApiBinding
from .functions.utils import create_logger, load_env
from .functions.caselessdict import CaselessDict

logger = logging.getLogger("legacy_mdr_migrations - utils")

metrics = Metrics()

API_HEADERS = {"Accept": "application/json"}

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
API_BASE_URL = load_env("API_BASE_URL")


class TermCache:
    def __init__(self, api):
        self.api = api
        self.all_terms_attributes = self.api.get_all_from_api("/ct/terms/attributes")
        self.all_terms_name_submission_values = CaselessDict(
            self.api.get_all_identifiers(
                self.all_terms_attributes,
                identifier="nameSubmissionValue",
                value="termUid",
            )
        )
        self.all_terms_code_submission_values = CaselessDict(
            self.api.get_all_identifiers(
                self.all_terms_attributes,
                identifier="codeSubmissionValue",
                value="termUid",
            )
        )
        self.all_term_names = self.api.get_all_from_api("/ct/terms/names")
        self.all_term_name_values = CaselessDict(
            self.api.get_all_identifiers_multiple(
                self.all_term_names, identifier="sponsorPreferredName", values=["termUid", "catalogueName"]
            )
        )
        self.added_terms = CaselessDict()


# Decorator to avoid starting every function with the open() context manager
def open_file():
    def open_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self = args[0]
            filename = args[1]
            if filename:
                self.log.info(f"Opening file: {filename}")
                try:
                    with open(filename, encoding="utf-8", errors="ignore") as textfile:
                        return func(self, textfile, *args[2:], **kwargs)
                except FileNotFoundError:
                    self.log.error(f"File {filename} not found, skipping")
            else:
                self.log.info("Empty filename, skipping")

        return wrapper

    return open_decorator


# Decorator to avoid starting every function with the open() context manager
def open_file_async():
    def open_decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            self = args[0]
            filename = args[1]
            if filename:
                self.log.info(f"Opening file: {filename}")
                try:
                    with open(filename, encoding="utf-8", errors="ignore") as textfile:
                        await func(self, textfile, *args[2:], **kwargs)
                except FileNotFoundError:
                    self.log.error(f"File {filename} not found, skipping")
            else:
                self.log.info("Empty filename, skipping")

        return wrapper

    return open_decorator


class BaseImporter:
    logging_name = "legacy_mdr_migrations"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        self.log = create_logger(self.logging_name)
        if metrics_inst is None:
            self.metrics = Metrics()
        else:
            self.metrics = metrics_inst
        if api is None:
            headers = self._authenticate(API_HEADERS)
            self.api = ApiBinding(API_BASE_URL, headers, self.metrics, logger=self.log)
        else:
            self.api = api

        self.cache = cache

        self.visit_type_codelist_name = "VisitType"
        self.element_subtype_codelist_name = "Element Sub Type"

    @staticmethod
    def _authenticate(headers: Dict) -> Dict:
        """Authenticates with client secret flow and appends Authorization header the dict of API request headers"""

        headers = headers.copy()

        client_id = load_env("CLIENT_ID", "")

        if client_id:
            client_secret = load_env("CLIENT_SECRET")
            token_endpoint = load_env("TOKEN_ENDPOINT")
            scope = load_env("SCOPE")

            response = requests.post(
                token_endpoint,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "client_credentials",
                    "scope": scope,
                },
            )

            response.raise_for_status()
            payload = response.json()

            access_token = payload.get("access_token")
            if not access_token:
                msg = "missing access token from token payload"
                logger.error(msg)
                raise RuntimeError(msg)

            token_type = payload.get("token_type")
            if not access_token:
                msg = "missing token type from token payload"
                logger.error(msg)
                raise RuntimeError(msg)

            headers["Authorization"] = f"{token_type} {access_token}"

        return headers

    def run(self):
        pass

    def prepare(self):
        pass

    def ensure_cache(self):
        if self.cache is None:
            self.log.info("Creating term cache")
            self.cache = TermCache(self.api)

    def get_cache(self):
        self.ensure_cache()
        return self.cache

    ############ helper functions ###########

    # Check if a codelist contains a term with sponsor preferred name equal to the given name.
    def search_codelist(self, codelist, name):
        for item in codelist:
            if (
                item.get("name", {}).get("sponsorPreferredName", "").lower()
                == name.lower()
            ):
                return True
        return False

    # Search a codelist for a term with the given sponsor preferred name.
    # For use with codelists fetched like:
    # terms = self.api.get_terms_for_codelist_name("Objective Category")
    def get_uid_for_sponsor_preferred_name(self, terms, name):
        for item in terms:
            try:
                if item["name"]["sponsorPreferredName"] == name:
                    return item["termUid"]
            except KeyError:
                pass

    # Helper to return the first term that has a matching catalogue name.
    def _find_term_with_catalogue(self, terms, catalogue):
        for term in terms:
            if term["catalogueName"] == catalogue:
                return term

    async def process_simple_term_migration(
        self, data: dict, session: aiohttp.ClientSession
    ):
        self.ensure_cache()
        result = None
        termName = data["body"]["sponsorPreferredName"]
        post_status, post_result = await self.api.post_to_api_async(
            url="/ct/terms", body=data["body"], session=session
        )
        termUid = None
        if post_status == 201:
            self.cache.added_terms[termName] = post_result
            termUid = post_result["termUid"]
            self.log.info(f"Added term name '{termName}' with uid '{termUid}'")
            time.sleep(0.01)
            status, result = await self.api.approve_async(
                "/ct/terms/" + termUid + "/names/approve", session=session
            )
            if status != 201:
                self.log.error(
                    f"Failed to approve term name '{termName}' with uid '{termUid}'"
                )
                metrics.icrement("/ct/terms--NamesApproveError")
            else:
                self.log.info(f"Approved term name '{termName}' with uid '{termUid}'")
                metrics.icrement("/ct/terms--NamesApprove")
            status, result = await self.api.approve_async(
                "/ct/terms/" + termUid + "/attributes/approve", session=session
            )
            if status != 201:
                self.log.error(
                    f"Failed to approve term attributes '{termName}' with uid '{termUid}'"
                )
                metrics.icrement("/ct/terms--AttributesApproveError")
            else:
                self.log.info(
                    f"Approved term attributes '{termName}' with uid '{termUid}'"
                )
                metrics.icrement("/ct/terms--AttributesApprove")
        else:
            self.log.error(
                f"Failed to add term name '{termName}' with uid '{termUid}', trying to link to already existing"
            )
            if termName in self.cache.added_terms:
                termUid = self.cache.added_terms[termName]["termUid"]
                self.log.info(
                    f"Term name '{termName}' with uid '{termUid}' found in cache of newly added terms"
                )
            elif termName in self.cache.all_term_name_values:
                found_terms = self.cache.all_term_name_values[termName]
                term_in_catalogue = self._find_term_with_catalogue(found_terms, data["body"]["catalogueName"])
                self.log.info(
                    f"Term name '{termName}' found as '{[str(t['catalogueName']) + ':' + t['termUid'] for t in found_terms]}' among existing term names"
                )
                if term_in_catalogue is None:
                    self.log.error(
                        f"Term '{termName}' not found in catalogue: '{data['body']['catalogueName']}', using first match from catalogue '{found_terms[0]['catalogueName']}'"
                    )
                    termUid = found_terms[0]["termUid"]
                else:
                    termUid = term_in_catalogue["termUid"]
                codelist_uid = data["body"]["codelistUid"]
                codelist = self.retry_function(self.api.get_terms_for_codelist_uid, [codelist_uid], nbr_retries=3, retry_delay=0.5)
                if self.search_codelist(codelist, termName):
                    self.log.info(
                        f"Term name '{termName}' already exits in the codelist with uid {codelist_uid}, not adding again"
                    )
                    return
            elif (
                data["body"].get("codeSubmissionValue")
                in self.cache.all_terms_code_submission_values
            ):
                termUid = self.cache.all_terms_code_submission_values[
                    data["body"].get("codeSubmissionValue")
                ]
                self.log.info(
                    f"Term name '{termName}' found with uid '{termUid}' among existing term code submission values"
                )
            elif (
                data["body"].get("nameSubmissionValue")
                in self.cache.all_terms_name_submission_values
            ):
                termUid = self.cache.all_terms_name_submission_values[
                    data["body"].get("nameSubmissionValue")
                ]
                self.log.info(
                    f"Term name '{termName}' found with uid '{termUid}' among existing term name submission values"
                )
            if termUid:
                codelist_uid = data["body"]["codelistUid"]
                self.log.info(
                    f"Add term name '{termName}' with uid '{termUid}' to codelist '{codelist_uid}'"
                )
                result = await self.api.post_to_api_async(
                    url="/ct/codelists/" + codelist_uid + "/add-term",
                    body={"termUid": termUid, "order": data["body"]["order"]},
                    session=session,
                )
        if data.get("validEpochUids"):
            for valid_epoch_uid in data.get("validEpochUids"):
                self.api.post_to_api(
                    {
                        "path": f"/ct/terms/{termUid}/add-parent?parent_uid={valid_epoch_uid}&relationship_type=valid_for_epoch",
                        "body": {},
                    }
                )
        if data.get("elementTypeUid"):
            self.api.post_to_api(
                {
                    "path": f"/ct/terms/{termUid}/add-parent?parent_uid={data.get('elementTypeUid')}&relationship_type=type",
                    "body": {},
                }
            )
        return result

    # Retry a function that sporadically fails.
    # After the first failure it will sleep for retry_delay seconds,
    # then double the delay for each subsequent failure.
    def retry_function(self, function: Callable, args: list, nbr_retries:int=3, retry_delay:float=0.5):
        for n in range(nbr_retries+1):
            try:
                return function(*args)
            except Exception:
                self.log.warning(f"Function failed, retry {n+1} of {nbr_retries} in {retry_delay} seconds")
                time.sleep(retry_delay)
                retry_delay = 2*retry_delay
