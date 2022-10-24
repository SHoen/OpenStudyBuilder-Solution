from importers.importer import BaseImporter, open_file, open_file_async
from importers.metrics import Metrics
import asyncio
import aiohttp
import csv
from typing import Optional, Sequence, Any

from importers.functions.utils import load_env

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")
MDR_MIGRATION_ACTIVITIES = load_env("MDR_MIGRATION_ACTIVITIES")
MDR_MIGRATION_ACTIVITY_SUB_GROUPS = load_env("MDR_MIGRATION_ACTIVITY_SUB_GROUPS")
MDR_MIGRATION_ACTIVITY_GROUPS = load_env("MDR_MIGRATION_ACTIVITY_GROUPS")
MDR_MIGRATION_ACTIVITY_INSTANCES = load_env("MDR_MIGRATION_ACTIVITY_INSTANCES")


# ---------------------------------------------------------------
# Utilites for parsing and converting data
# ---------------------------------------------------------------
#


def sample_from_dict(d, sample=10):
    if SAMPLE:
        keys = list(d)[0:sample]
        values = [d[k] for k in keys]
        return dict(zip(keys, values))
    else:
        return d


def sample_from_list(d, sample=10):
    if SAMPLE:
        return d[0:sample]
    else:
        return d


# Activities with instances, groups and subgroups in sponsor library
class Activities(BaseImporter):
    logging_name = "activities"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)

    @open_file_async()
    async def handle_activity_groups(self, csvfile, session):
        # Populate then activity groups in sponsor library
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks = []

        existing_rows = self.api.get_all_identifiers(
            self.api.get_all_from_api("/concepts/activities/activity-groups"),
            identifier="name",
            value="uid",
        )

        for row in readCSV:
            data = {
                "path": "/concepts/activities/activity-groups",
                "approve_path": "/concepts/activities/activity-groups",
                "body": {
                    "name": row[headers.index("std_assm_grp")],
                    "nameSentenceCase": row[headers.index("std_assm_grp")].lower(),
                    "definition": "Definition not provided",
                    "libraryName": "Sponsor",
                },
            }
            if not existing_rows.get(data["body"]["name"]):
                self.log.info(
                    f"Add activity group '{data['body']['name']}' to library '{data['body']['libraryName']}'"
                )
                api_tasks.append(
                    self.api.post_then_approve(data=data, session=session, approve=True)
                )  # TODO Verify if activity groups can be approved?
            else:
                self.log.info(
                    f"Item '{data['body']['name']}' already exists in library '{data['body']['libraryName']}'"
                )
        await asyncio.gather(*api_tasks)
        # await session.close()

    @open_file_async()
    async def handle_activity_sub_groups(self, csvfile, session):
        # Populate then activity subgroups in sponsor library
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)

        existing_groups = sample_from_dict(
            self.api.get_all_identifiers(
                self.api.get_all_from_api("/concepts/activities/activity-groups"),
                identifier="name",
                value="uid",
            ),
            sample=10,
        )

        existing_sub_groups = {}

        for item in self.api.get_all_from_api(
            "/concepts/activities/activity-sub-groups"
        ):
            existing_sub_groups[item["name"]] = {
                "uid": item["uid"],
                "activityGroup": item["activityGroup"],
            }

        api_tasks = []
        file_data = {}

        for row in readCSV:
            sub_group_name = row[headers.index("std_assm_sub_grp")]
            group_name = row[headers.index("std_assm_grp")]
            if group_name != "" and sub_group_name != "":
                #print(group_name, " - ", sub_group_name)
                if sub_group_name in file_data:
                    self.log.warn(f"Subgroup '{sub_group_name}' is already belonging to group '{file_data[sub_group_name]}', ignoring group '{group_name}'")
                file_data[sub_group_name] = group_name
        #print(file_data)

        for sub_group_name, group_name in file_data.items():
            # Check if all group names are defined
            if group_name not in existing_groups:
                self.log.warning(f"Group name not found: '{group_name}' will not create subgroup: '{sub_group_name}'")
                continue
            # Check if subgroup exists
            if sub_group_name in existing_sub_groups:
                # If the subgroup has the wrong group, patch it
                if existing_sub_groups[sub_group_name]["activityGroup"]["name"] == group_name:
                    self.log.info(f"Subgroup '{sub_group_name}' already exists for group '{group_name}'")
                    continue
                data = {
                    "path": "/concepts/activities/activity-sub-groups",
                    "patch_path": "/concepts/activities/activity-sub-groups/"
                    + existing_sub_groups[sub_group_name]["uid"],
                    "new_path": "/concepts/activities/activity-sub-groups/"
                    + existing_sub_groups[sub_group_name]["uid"]
                    + "/new-version",
                    "approve_path": "/concepts/activities/activity-sub-groups",
                    "body": {
                        "name": sub_group_name,
                        "nameSentenceCase": sub_group_name.lower(),
                        "libraryName": "Sponsor",
                        "activityGroup": existing_groups[group_name]
                    },
                }
                self.log.info(
                    f"Patching subgroup '{sub_group_name}' to group '{group_name}'"
                )
                api_tasks.append(
                    self.api.new_version_patch_then_approve(
                        data=data, session=session, approve=True
                    )
                )
            else:
                # Create the new subgroup
                data = {
                    "path": "/concepts/activities/activity-sub-groups",
                    "approve_path": "/concepts/activities/activity-sub-groups",
                    "body": {
                        "name": sub_group_name,
                        "nameSentenceCase": sub_group_name.lower(),
                        "libraryName": "Sponsor",
                        "activityGroup": existing_groups[group_name]
                    },
                }
                self.log.info(
                    f"Adding subgroup '{sub_group_name}' to groups '{group_name}'"
                )
                api_tasks.append(
                    self.api.post_then_approve(
                        data=data, session=session, approve=True
                    )
                )
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_activities(self, csvfile, session):
        # Populate the activities in sponsor library
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        self.log.info("Fetching all existing activity subgroups")
        existing_sub_groups = self.api.get_all_identifiers(
            self.api.get_all_from_api("/concepts/activities/activity-sub-groups"),
            identifier="name",
            value="uid",
        )
        print(existing_sub_groups)

        self.log.info("Fetching all existing activities")
        existing_activities = {}
        for item in self.api.get_all_activity_objects("activities"):
            existing_activities[item["name"]] = {
                "uid": item["uid"],
                "activitySubGroup": item["activitySubGroup"],
            }

        api_tasks = []
        file_data = {}

        for row in readCSV:
            activity_name = row[headers.index("activity")]
            sub_group_name = row[headers.index("std_assm_sub_grp")]
            if activity_name != "" and sub_group_name != "":
                if sub_group_name in file_data:
                    self.log.warn(f"Activity '{activity_name}' is already belonging to subgroup '{file_data[sub_group_name]}', ignoring subgroup '{sub_group_name}'")
                file_data[activity_name] = sub_group_name

        file_data = sample_from_dict(file_data, sample=100)

        for activity_name, sub_group_name in file_data.items():
            # Check if all sub group names are defined
            if sub_group_name not in existing_sub_groups:
                self.log.warning(f"Sub group name not found: {sub_group_name} will not create activity: {activity_name}")
                continue
            # Check if activity exists
            if activity_name in existing_activities:
                # If the activity does not already have all groups -> patch it
                if existing_activities[activity_name]["activitySubGroup"]["name"] == sub_group_name:
                    self.log.info(f"Activity '{activity_name}' already exists for subgroup '{sub_group_name}'")
                    continue
                data = {
                    "path": "/concepts/activities/activities",
                    "patch_path": "/concepts/activities/activities",
                    "new_path": "/concepts/activities/activities/"
                    + existing_activities[activity_name]["uid"]
                    + "/new-version",
                    "approve_path": "/concepts/activities/activities",
                    "body": {
                        "name": activity_name,
                        "nameSentenceCase": activity_name.lower(),
                        "libraryName": "Sponsor",
                        "activitySubGroup": existing_sub_groups[sub_group_name] 
                    },
                }
                self.log.info(
                    f"Adding activity '{activity_name}' to subgroup '{sub_group_name}'"
                )
                api_tasks.append(
                    self.api.new_version_patch_then_approve(
                        data=data, session=session, approve=True
                    )
                )


            else:  # Create the activity
                data = {
                    "path": "/concepts/activities/activities",
                    "approve_path": "/concepts/activities/activities",
                    "body": {
                        "name": activity_name,
                        "nameSentenceCase": activity_name.lower(),
                        "libraryName": "Sponsor",
                        "activitySubGroup": existing_sub_groups[sub_group_name]
                    },
                }
                self.log.info(
                    f"Adding activity '{activity_name}' to subgroup '{sub_group_name}'"
                )
                api_tasks.append(
                    self.api.post_then_approve(
                        data=data, session=session, approve=True
                    )
                )

        await asyncio.gather(*api_tasks)
        # await session.close()

    @open_file_async()
    async def handle_activity_instances(self, csvfile, session):
        self.ensure_cache()
        readCSV = csv.reader(csvfile, delimiter=",")
        headers = next(readCSV)
        api_tasks = []

        all_activity_hierarchies = self.api.get_all_identifiers(
            self.api.get_all_activity_objects("activities"),
            identifier="name",
            value="uid",
        )

        existing_rows = self.api.get_all_identifiers(
            self.api.get_all_activity_objects("activity-instances"),
            identifier="name",
            value="uid",
        )

        file_data = []
        for row in readCSV:
            file_data.append(row)

        file_data = sample_from_list(file_data, sample=10)

        for row in file_data:
            activity_name = row[headers.index("activity_instance")]
            activity = row[headers.index("activity")]
            activity_uids = []
            if all_activity_hierarchies.get(activity):
                activity_uids.append(all_activity_hierarchies.get(activity))

            general_domain_class = row[headers.index("GENERAL_DOMAIN_CLASS")]
            sub_domain_class = row[headers.index("sub_domain_class")]
            path = "/concepts/activities"
            if general_domain_class.lower() == "events":
                path += "/events"
            elif general_domain_class.lower() == "special purposes":
                path += "/special-purposes"
            elif general_domain_class.lower() == "reminders":
                path += "/reminders"
            elif sub_domain_class.lower() == "compound dosing":
                path += "/compound-dosings"
            elif sub_domain_class.lower() == "categoric finding":
                path += "/categoric-findings"
            elif sub_domain_class.lower() == "numeric finding":
                path += "/numeric-findings"
            elif sub_domain_class.lower() == "textual finding":
                path += "/textual-findings"
            else:
                # The activity instance type was not recognized
                self.log.warning(
                    f"Activity instance '{activity_name}' has an unknown domain class '{sub_domain_class}'"
                )
                continue
            data = {
                "path": path,
                "approve_path": "/concepts/activities/activity-instances",
                "body": {
                    "name": activity_name,
                    "nameSentenceCase": activity_name.lower(),
                    "adamParamCode": row[headers.index("adam_param_code")],
                    "activities": activity_uids,
                    "legacyDescription": row[headers.index("legacy_description")],
                    "topicCode": row[headers.index("TOPIC_CD")],
                    "libraryName": "Sponsor",
                },
            }
            if row[headers.index("specimen")] != "":
                if (
                    row[headers.index("specimen")]
                    in self.cache.all_terms_name_submission_values
                ):
                    data["body"][
                        "specimen"
                    ] = self.cache.all_terms_name_submission_values[
                        row[headers.index("specimen")]
                    ]
                elif (
                    row[headers.index("specimen")]
                    in self.cache.all_terms_code_submission_values
                ):
                    data["body"][
                        "specimen"
                    ] = self.cache.all_terms_code_submission_values[
                        row[headers.index("specimen")]
                    ]
            if row[headers.index("SDTM_DOMAIN")] != "":
                if (
                    row[headers.index("SDTM_DOMAIN")]
                    in self.cache.all_terms_name_submission_values
                ):
                    data["body"][
                        "sdtmDomain"
                    ] = self.cache.all_terms_name_submission_values[
                        row[headers.index("SDTM_DOMAIN")]
                    ]
                elif (
                    row[headers.index("SDTM_DOMAIN")]
                    in self.cache.all_terms_code_submission_values
                ):
                    data["body"][
                        "sdtmDomain"
                    ] = self.cache.all_terms_code_submission_values[
                        row[headers.index("SDTM_DOMAIN")]
                    ]
            if not existing_rows.get(activity_name):
                self.log.info(
                    f"Adding activity '{activity}' to instance '{activity_name}' at path '{path}'"
                )
                api_tasks.append(
                    self.api.post_then_approve(data=data, session=session, approve=True)
                )
            else:
                self.log.info(
                    f"Activity '{activity}' in instance '{activity_name}' already exists"
                )
        await asyncio.gather(*api_tasks)

    async def async_run(self):
        timeout = aiohttp.ClientTimeout(None)
        conn = aiohttp.TCPConnector(limit=4, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
            await self.handle_activity_groups(MDR_MIGRATION_ACTIVITY_GROUPS, session)
            await self.handle_activity_sub_groups(
                MDR_MIGRATION_ACTIVITY_SUB_GROUPS, session
            )
            await self.handle_activities(MDR_MIGRATION_ACTIVITIES, session)
            await self.handle_activity_instances(
                MDR_MIGRATION_ACTIVITY_INSTANCES, session
            )

    def run(self):
        self.log.info("Importing activities")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_run())
        self.log.info("Done importing activities")


def main():
    metr = Metrics()
    migrator = Activities(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
