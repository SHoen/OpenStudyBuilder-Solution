from importers.metrics import Metrics
import requests
import aiohttp
import asyncio
from os import environ
from typing import Optional, Sequence, Any
import logging
from aiohttp_trace import request_tracer
import sys
import json
import time

# ---------------------------------------------------------------
# Api bindings
# ---------------------------------------------------------------
#
class ApiBinding:
    def __init__(self, api_base_url, api_headers, metrics, logger=None):
        self.api_headers = api_headers
        self.api_base_url = api_base_url
        if metrics is None:
            self.metrics = Metrics()
        else:
            self.metrics = metrics
        self.sem = asyncio.Semaphore(8)
        if logger is not None:
            self.log = logger
        else:
            self.log = logging.getLogger("legacy_mdr_migrations - apibinding")
        self.verify_connection()
        self.check_for_ct_packages()

    # ---------------------------------------------------------------
    # Verify connection to api (and database)
    # ---------------------------------------------------------------
    #
    # Verify that Clinical MDR API is online
    # TODO Replace with api health check resource ...
    def verify_connection(self):
        try:
            response = requests.get(
                self.api_base_url + "/openapi.json", headers=self.api_headers
            )
            response.raise_for_status()
        except Exception as e:
            self.log.critical(
                f"Failed to connect to backend, is it running?\nError was:\n{e}"
            )
            sys.exit(1)

    # Verify that the bare minimum of CT packages are available.
    def check_for_ct_packages(self):
        packages = self.get_all_from_api("/ct/packages")
        package_names = set()
        for package in packages:
            package_names.add(package.get("catalogueName"))
        mandatory_packages = {
            "ADAM CT",
            "CDASH CT",
            "DEFINE-XML CT",
            "SDTM CT"
        }
        optional_packages = {
            "COA CT",
            "GLOSSARY CT",
            "PROTOCOL CT",
            "QRS CT",
            "QS-FT CT",
            "SEND CT"
        }
        missing = mandatory_packages - package_names
        if len(missing) > 0:
            self.log.critical(
                f"Missing CT packages: {','.join(missing)}.\nPlease run the clinical standards import before this tool."
            )
            sys.exit(1)
        missing = optional_packages - package_names
        if len(missing) > 0:
            self.log.warning(
                f"Missing optional CT packages: {','.join(missing)}."
            )

    def simple_post_to_api(self, path, body, simple_path=None):
        if simple_path is None:
            simple_path = path
        response = requests.post(
            self.api_base_url + path, headers=self.api_headers, json=body
        )
        if response.ok:
            self.metrics.icrement(simple_path + "--POST")
            self.log.debug("POST %s %s", path, "success")
            return response.json()
        else:
            self.log.debug("POST %s", path)
            if "message" in response.json() and (
                "already exists" in response.json()["message"]
                or "all ready" in response.json()["message"]
                or "Duplicate template" in response.json()["message"]
                or "There is already" in response.json()["message"]
            ):
                self.log.warning(response.json()["message"])
                self.metrics.icrement(simple_path + "--AlreadyExists")
            elif (
                "message" in response.json()
                and "no approved objective" in response.json()["message"]
            ):
                self.log.warning(response.json()["message"])
                self.metrics.icrement(simple_path + "--NoObjective")
            else:
                self.log.warning(response.text)
                self.metrics.icrement(simple_path + "--ERROR")
            return None

    def post_to_api(self, object, body=None, path=None):
        if path is None:
            response = requests.post(
                self.api_base_url + object["path"],
                headers=self.api_headers,
                json=object["body"],
            )
            path = object["path"]
        else:
            response = requests.post(
                self.api_base_url + path, headers=self.api_headers, json=body
            )
        short_path = "".join(
                [i for i in path if not i.isdigit()]
            )

        if response.ok:
            self.metrics.icrement(short_path + "--POST")
            if "name" in object["body"]:
                self.log.debug("POST %s %s", object["path"], object["body"]["name"])
            else:
                self.log.debug("POST %s %s", object["path"], "success")
            return response.json()

        else:
            if "name" in object["body"]:
                self.log.debug("POST %s %s", object["path"], object["body"]["name"])
            else:
                self.log.debug("POST %s %s", object["path"], "no name")
            if "message" in response.json() and (
                "already exists" in response.json()["message"]
                or "Duplicate template" in response.json()["message"]
                or "already has" in response.json()["message"]
            ):
                self.log.warning("Post to %s failed: %s", path, response.json()["message"])
                self.metrics.icrement(short_path + "--AlreadyExists")
            elif (
                "message" in response.json()
                and ("not found" in response.json()["message"]
                or "does not exist" in response.json()["message"])
            ):
                self.log.warning("Post to %s failed: %s", path, response.json()["message"])
                self.metrics.icrement(short_path + "--NotFound")
            else:
                self.log.warning("Post to %s failed: %s", path, response.text)
                self.metrics.icrement(short_path + "--ERROR")
            return None

    def patch_to_api(self, body, path):
        url = self.api_base_url + path + body["uid"]
        response = requests.patch(url, headers=self.api_headers, json=body)
        if response.ok:
            self.metrics.icrement(path + "--Patch")
            self.log.info("Patch %s %s", path, "success")
            return response.json()
        else:
            self.log.warning("Patch %s %s", path, "error")
            if (
                "message" in response.json().keys()
                and "already exists" in response.json()["message"]
            ):
                self.log.warning(response.json()["message"])
                self.metrics.icrement(path + "--AlreadyExists")
            else:
                self.log.warning(response.text)
                self.metrics.icrement(path + "--Patch-ERROR")
            return None

    def approve_item(self, uid: str, url: str):
        if not url.endswith("/"):
            url = url + "/"
        response = requests.post(
            self.api_base_url + url + uid + "/approve", headers=self.api_headers
        )
        if not response.ok:
            self.log.warning("Failed to approve %s %s", uid, response.content)
            return False
        else:
            return True

    def approve_item_names_and_attributes(self, uid: str, url: str):
        if not url.endswith("/"):
            url = url + "/"
        response = requests.post(
            self.api_base_url + url + uid + "/names/approve", headers=self.api_headers
        )
        if not response.ok:
            self.log.warning("Failed to approve names %s %s", uid, response.content)
            return False
        response = requests.post(
            self.api_base_url + url + uid + "/attributes/approve", headers=self.api_headers
        )
        if not response.ok:
            self.log.warning("Failed to approve attributes %s %s", uid, response.content)
            return False
        else:
            return True

    def get_all_from_api(self, path, params=None, items_only=True):
        # print(self.api_base_url + path, params, self.api_headers)
        response = requests.get(
            self.api_base_url + path, params=params, headers=self.api_headers
        )
        if response.ok:
            res = response.json()
            if "items" in res and items_only:
                self.metrics.icrement(path + "--GET", len(res["items"]))
                return res["items"]
            else:
                return res
        else:
            if "message" in response.json().keys():
                self.log.error("get %s, message: %s", path, response.json()["message"])
            else:
                self.log.error("get %s %s", path, response.text)
            return None

    def get_all_identifiers(self, responses: list, identifier: str, value: str = None):
        if value is None:
            identifiers = []
            for response_item in responses:
                identifiers.append(response_item[identifier])
            return identifiers
        else:
            identifiers = {}
            if responses == None:
                return identifiers
            for response_item in responses:
                identifiers[response_item[identifier]] = response_item[value]
            return identifiers

    # Alternative version of get_all_identifiers() that returns a dict with only lower case keys.
    # Each item is list of all found values.
    def get_all_identifiers_multiple(
        self, responses: list, identifier: str, values: Sequence[str]
    ):
        identifiers = {}
        if responses == None:
            return identifiers
        for response_item in responses:
            ident = response_item[identifier].lower()
            if ident not in identifiers:
                identifiers[ident] = []
            requested_values = {}
            for value in values:
                requested_values[value] = response_item[value]
            identifiers[ident].append(requested_values)
        return identifiers

    def get_libraries(self):
        response = requests.get(
            self.api_base_url + "/libraries", headers=self.api_headers
        )
        response.raise_for_status()
        libs = response.json()
        libNames = [lib["name"] for lib in libs]
        self.log.info("Existing libraries: %s", libNames)
        return libNames

    def create_library(self, object):
        self.metrics.icrement("/libraries")
        response = requests.post(
            self.api_base_url + "/libraries", headers=self.api_headers, json=object
        )
        response.raise_for_status()

    # Get all terms from a codelist identified by codelist name
    def get_terms_for_codelist_name(self, codelist_name: str):
        response = requests.get(
            self.api_base_url + f"/ct/terms",
            params={"codelist_name": codelist_name, "page": 1, "size": 0},
            headers=self.api_headers,
        )
        response.raise_for_status()
        result = response.json()
        return result["items"]

    # Get all terms from a codelist identified by codelist uid
    def get_terms_for_codelist_uid(self, codelist_uid: str):
        response = requests.get(
            self.api_base_url + f"/ct/terms",
            params={"codelist_uid": codelist_uid, "page": 1, "size": 0},
            headers=self.api_headers,
        )
        response.raise_for_status()
        result = response.json()
        return result["items"]

    # Get all dictionary mapping all codelist names to a uid
    def get_code_lists_uids(self):
        response = requests.get(
            self.api_base_url + "/ct/codelists/names?page=0&size=10000",
            headers=self.api_headers,
        )
        response.raise_for_status()
        result = response.json()
        codelists_uids = {}
        for res in result["items"]:
            codelists_uids[res["name"]] = res["codelistUid"]
        return codelists_uids

    def get_all_activity_objects(self, object_type):
        page_number = 1
        page_size = 100
        total_count = True
        params = {
            "pageNumber": page_number,
            "pageSize": page_size,
            "totalCount": total_count,
        }
        self.log.info(
            f"Getting {object_type} page:{page_number}, page_size:{page_size}"
        )
        all_activities_initial = self.get_all_from_api(
            f"/concepts/activities/{object_type}", params=params, items_only=False
        )
        if all_activities_initial:
            all_activity_objects = all_activities_initial["items"]
            count = all_activities_initial["total"]
        else:
            all_activity_objects = []
            count = 0


        while page_size * page_number < count:
            page_number += 1
            total_count = False
            params = {
                "pageNumber": page_number,
                "pageSize": page_size,
                "totalCount": total_count,
            }
            self.log.info(
                f"Getting {object_type} page:{page_number}, page_size:{page_size}, total:{count}"
            )
            all_activity_objects += self.get_all_from_api(
                f"/concepts/activities/{object_type}", params=params, items_only=True
            )
        return all_activity_objects

    def get_study_objectives_for_study(self, study_uid):
        response = requests.get(
            self.api_base_url + "/study/" + study_uid + "/study-objectives",
            headers=self.api_headers,
        )
        response.raise_for_status()
        result = response.json()
        temp_dict = {}
        for res in result["items"]:
            temp_dict[res["objective"]["name"]] = res["studyObjectiveUid"]
        return temp_dict

    def get_templates_as_dict(self, path):
        response = requests.get(self.api_base_url + path, headers=self.api_headers)
        response.raise_for_status()
        result = response.json()
        objective_temp_dict = {}
        result = result["items"] if type(result) is dict else result
        for res in result:
            objective_temp_dict[res["name"]] = res
        return objective_temp_dict

    def find_object_by_name(self, name, path):
        response = requests.get(
            self.api_base_url + path + "/get-by-name/" + name, headers=self.api_headers
        )
        if response.ok:
            return response.json()
        else:
            return None

    # Find the uid for a dictionary from its name
    def find_dictionary_uid(self, name):
        response = requests.get(
            self.api_base_url + "/dictionaries/codelists/" + name,
            headers=self.api_headers,
        )
        if response.ok:
            # This assumes there is only one version, do we need to handle multiple?
            return response.json()["items"][0]["codelistUid"]
        else:
            return None

    # Find a term via its name from a dictionary
    def find_dictionary_item_uid_from_name(self, dict_uid, name):
        response = requests.get(
            self.api_base_url + "/dictionaries/terms",
            params={
                "codelist_uid": dict_uid,
                "filters": json.dumps({"name": {"v": [name]}}),
                "page": 1,
                "size": 0,
            },
            headers=self.api_headers,
        )
        if response.ok:
            if len(response.json()["items"]) > 0:
                # This assumes there is only one version, do we need to handle multiple?
                return response.json()["items"][0]["termUid"]
        return None

    def get_studies_as_dict(self, path="/studies"):
        response = requests.get(self.api_base_url + path, headers=self.api_headers)
        response.raise_for_status()
        result = response.json()
        temp_dict = {}
        for res in result["items"]:
            temp_dict[res["studyId"]] = res
        return temp_dict

    def simple_approve(self, path: str):
        path = self.api_base_url + path
        res = requests.post(path, headers=self.api_headers)
        if not res.ok:
            self.log.warning("Failed to approve %s", path)
            return False
        else:
            return True

    def simple_approve2(self, url: str, path: str, label=""):
        url = url + path
        res = requests.post(self.api_base_url + url, headers=self.api_headers)
        if not res.ok:
            self.log.warning("Failed to approve %s", url)
            self.metrics.icrement(f"{url}--{label}ApproveError")
            return False
        else:
            self.metrics.icrement(f"{url}--{label}Approve")
            return True

    def simple_patch(self, body, url, path):
        full_url = self.api_base_url + url
        response = requests.patch(full_url, headers=self.api_headers, json=body)
        if response.ok:
            self.metrics.icrement(path + "--Patch")
            self.log.info("Patch %s %s", path, "success")
            return response.json()
        else:
            if (
                "message" in response.json().keys()
                and "already exists" in response.json()["message"]
            ):
                self.log.warning("Patch %s %s", url, "error, item already exists")
                self.metrics.icrement(path + "--AlreadyExists")
            elif (
                "message" in response.json().keys()
                and "does not exist" in response.json()["message"]
            ):
                self.log.warning("Patch %s %s", url, "error, item not found")
                self.metrics.icrement(path + "--NotFound")
            else:
                self.log.warning("Patch %s %s", url, response.text)
                self.metrics.icrement(path + "--Patch-ERROR")
            return None

    # ---------------------------------------------------------------
    # Async building blocks
    # ---------------------------------------------------------------
    #
    async def new_version_to_api_async(self, path: str, session: aiohttp.ClientSession):
        async with session.post(
            self.api_base_url + path, json={}, headers=self.api_headers
        ) as response:
            return await response.json()

    async def patch_to_api_async(
        self, path: str, body: dict, session: aiohttp.ClientSession
    ):
        async with session.patch(
            self.api_base_url + path, json=body, headers=self.api_headers
        ) as response:
            return await response.json()

    # This gives reasonable waiting for lock on atomic incrementing of identifiers
    async def post_to_api_async(
        self, url: str, body: dict, session: aiohttp.ClientSession
    ):
        async with self.sem:
            async with session.post(
                self.api_base_url + url, json=body, headers=self.api_headers
            ) as response:
                status = response.status
                result = await response.json()
                return status, result

    async def approve_async(self, url: str, session: aiohttp.ClientSession):
        async with session.post(
            self.api_base_url + url, headers=self.api_headers
        ) as response:
            status = response.status
            result = await response.json()
            return status, result

    async def approve_item_async(
        self, uid: str, url: str, session: aiohttp.ClientSession
    ):
        async with session.post(
            self.api_base_url + url + "/" + uid + "/approve", headers=self.api_headers
        ) as response:
            status = response.status
            result = await response.json()
            if status != 201:
                self.metrics.icrement(url + "--ApproveError")
            else:
                self.metrics.icrement(url + "--Approve")
            return result

    async def post_then_approve(
        self, data: dict, session: aiohttp.ClientSession, approve: bool
    ):
        self.log.debug(f"Post to {data['path']}")
        status, response = await self.post_to_api_async(
            url=data["path"], body=data["body"], session=session
        )
        uid = response.get("uid")
        if approve == True and uid != None:
            # Sleeping to avoid errors when running locally (with limited resources for the db).
            time.sleep(0.05)
            self.log.info(f"Approve item with uid '{uid}'")
            result = await self.approve_item_async(
                uid=uid, url=data["approve_path"], session=session
            )
            return result
        else:
            return response

    async def new_version_patch_then_approve(
        self, data: dict, session: aiohttp.ClientSession, approve: bool
    ):
        response = await self.new_version_to_api_async(
            path=data["new_path"], session=session
        )
        response = await self.patch_to_api_async(
            path=data["patch_path"], body=data["body"], session=session
        )
        uid = response.get("uid")
        if approve == True and uid != None:
            # Sleeping to avoid errors when running locally (with limited resources for the db).
            time.sleep(0.05)
            return await self.approve_item_async(
                uid=response.get("uid"), url=data["approve_path"], session=session
            )
        else:
            time.sleep(0.05)
            return await self.patch_to_api_async(
                path=data["patch_path"], body=data["body"], session=session
            )
