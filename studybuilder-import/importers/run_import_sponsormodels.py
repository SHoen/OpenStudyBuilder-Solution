import asyncio
import csv
import json
import os
from collections import defaultdict

import aiohttp

from .functions.utils import load_env
from .utils.importer import BaseImporter, open_file_async
from .utils.metrics import Metrics

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")

MDR_MIGRATION_ACTIVITY_INSTANCE_CLASS_MODEL_RELS = load_env(
    "MDR_MIGRATION_ACTIVITY_INSTANCE_CLASS_MODEL_RELS"
)
MDR_MIGRATION_SPONSOR_MODEL_DIRECTORY = load_env(
    "MDR_MIGRATION_SPONSOR_MODEL_DIRECTORY"
)
MDR_MIGRATION_SPONSOR_MODEL_DATASET_CLASSES = load_env(
    "MDR_MIGRATION_SPONSOR_MODEL_DATASET_CLASSES"
)
MDR_MIGRATION_SPONSOR_MODEL_DATASETS = load_env("MDR_MIGRATION_SPONSOR_MODEL_DATASETS")
MDR_MIGRATION_SPONSOR_MODEL_VARIABLE_CLASSES = load_env(
    "MDR_MIGRATION_SPONSOR_MODEL_VARIABLE_CLASSES"
)
MDR_MIGRATION_SPONSOR_MODEL_DATASET_VARIABLES = load_env(
    "MDR_MIGRATION_SPONSOR_MODEL_DATASET_VARIABLES"
)

SPONSOR_MODELS_PATH_PREFIX = "/standards/sponsor-models/"
SPONSOR_MODELS_PATH = SPONSOR_MODELS_PATH_PREFIX + "models"
SPONSOR_MODELS_DATASET_CLASSES_PATH = SPONSOR_MODELS_PATH_PREFIX + "dataset-classes"
SPONSOR_MODELS_VARIABLE_CLASSES_PATH = SPONSOR_MODELS_PATH_PREFIX + "variable-classes"
SPONSOR_MODELS_DATASETS_PATH = SPONSOR_MODELS_PATH_PREFIX + "datasets"
SPONSOR_MODELS_DATASET_VARIABLES_PATH = SPONSOR_MODELS_PATH_PREFIX + "dataset-variables"
ACTIVITY_INSTANCE_CLASSES_PATH = "/activity-instance-classes"
ACTIVITY_ITEM_CLASSES_PATH = "/activity-item-classes"


# SponsorModels with datasets and variables
class SponsorModels(BaseImporter):
    logging_name = "sponsor_models"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)

        self._common_body_params = {}
        self._model_body_params = {}

    def parse_bool(self, cell):
        if cell is None:
            return None
        else:
            return cell == "Y"

    def parse_instance_class_name(self, name):
        parsed = name.replace("AP ", "AssociatedPersons")
        return parsed

    def parse_item_class_name(self, name):
        return name.replace(" ", "").lower()

    def parse_variable_class_name(self, name):
        return name.replace("__", "--")

    @open_file_async()
    async def handle_activity_instance_class_relations(
        self, instance_class_csvfile, session
    ):
        api_tasks = []

        # Parse and PATCH ActivityInstanceClasses
        csv_reader = csv.reader(instance_class_csvfile, delimiter=",")
        headers = next(csv_reader)
        existing_instance_classes = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_INSTANCE_CLASSES_PATH),
            identifier="name",
            value="uid",
        )

        existing_instance_classes = {
            self.parse_instance_class_name(i): v
            for i, v in existing_instance_classes.items()
        }

        grouped_items = defaultdict(list)

        for row in csv_reader:
            class_cell = row[headers.index("activity_instance_class")]
            if class_cell:
                activity_instance_class_uid = existing_instance_classes.get(
                    self.parse_instance_class_name(class_cell),
                    None,
                )
                if activity_instance_class_uid is not None:
                    # There might be some duplicates in the CSV file
                    if (
                        row[headers.index("dataset_class")]
                        not in grouped_items[activity_instance_class_uid]
                    ):
                        grouped_items[activity_instance_class_uid].append(
                            row[headers.index("dataset_class")]
                        )

        for instance_class_uid, datasets in grouped_items.items():
            data = {
                "body": {
                    "dataset_class_uids": datasets,
                },
            }
            self.log.info(
                "Adding relationships to datasets for activity instance class '%s'",
                instance_class_uid,
            )
            api_tasks.append(
                self.api.patch_to_api_async(
                    path=f"{ACTIVITY_INSTANCE_CLASSES_PATH}/{instance_class_uid}/model-mappings",
                    body=data["body"],
                    session=session,
                )
            )

        # Finally, push all tasks
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_activity_item_class_relations(self, item_class_csvfile, session):
        api_tasks = []

        # Parse and PATCH ActivityItemClasses
        csv_reader = csv.reader(item_class_csvfile, delimiter=",")
        headers = next(csv_reader)
        existing_item_classes = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_ITEM_CLASSES_PATH),
            identifier="name",
            value="uid",
        )

        existing_item_classes = {
            self.parse_item_class_name(i): v for i, v in existing_item_classes.items()
        }

        grouped_items = defaultdict(list)

        for row in csv_reader:
            class_cell = row[headers.index("activity_item_class")]
            if class_cell:
                activity_item_class_uid = existing_item_classes.get(
                    self.parse_item_class_name(class_cell),
                    None,
                )
                if activity_item_class_uid is not None:
                    variable_class_uid = self.parse_variable_class_name(
                        row[headers.index("column")]
                    )
                    # There are some duplicates in the CSV file
                    if variable_class_uid not in grouped_items[activity_item_class_uid]:
                        grouped_items[activity_item_class_uid].append(
                            variable_class_uid
                        )

        for item_class_uid, variables in grouped_items.items():
            data = {
                "body": {
                    "variable_class_uids": variables,
                },
            }
            self.log.info(
                "Adding relationships to variables for activity item class '%s'",
                item_class_uid,
            )
            api_tasks.append(
                self.api.patch_to_api_async(
                    path=f"{ACTIVITY_ITEM_CLASSES_PATH}/{item_class_uid}/model-mappings",
                    body=data["body"],
                    session=session,
                )
            )

        # Finally, push all tasks
        await asyncio.gather(*api_tasks)

    async def handle_sponsor_model(self, session) -> bool:
        existing_sponsor_models = self.api.get_all_identifiers(
            self.api.get_all_from_api(SPONSOR_MODELS_PATH),
            identifier="name",
            value="uid",
        )

        sponsor_model_name = self._common_body_params["sponsor_model_name"]
        if sponsor_model_name in existing_sponsor_models:
            self.log.info(
                f"Sponsor model version {sponsor_model_name} already exists in database. Skipping import."
            )
            return False

        api_tasks = []

        data = {
            "body": self._model_body_params,
        }
        self.log.info(
            f"Add sponsor model for Implementation Guide '{data['body']['ig_uid']}' version '{data['body']['ig_version_number']}'"
        )

        api_tasks.append(
            self.api.post_to_api_async(
                url=SPONSOR_MODELS_PATH, body=data["body"], session=session
            )
        )
        await asyncio.gather(*api_tasks)

        return True

    @open_file_async()
    async def handle_dataset_classes(self, csvfile, session):
        # Populate sponsor model dataset classes
        csv_reader = csv.reader(csvfile, delimiter=",")
        headers = next(csv_reader)
        api_tasks = []

        for row in csv_reader:
            data = {
                "body": {
                    "dataset_class_uid": row[headers.index("table")],
                    "is_basic_std": self.parse_bool(row[headers.index("basic_std")]),
                    **self._common_body_params,
                }
            }
            self.log.info(
                f"Add sponsor model dataset class '{data['body']['dataset_class_uid']}' to sponsor model '{data['body']['sponsor_model_name']}'"
            )
            api_tasks.append(
                self.api.post_to_api_async(
                    url=SPONSOR_MODELS_DATASET_CLASSES_PATH,
                    body=data["body"],
                    session=session,
                )
            )
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_variable_classes(self, csvfile, session):
        # Populate sponsor model variable classes
        csv_reader = csv.reader(csvfile, delimiter=",")
        headers = next(csv_reader)
        api_tasks = []

        for row in csv_reader:
            data = {
                "body": {
                    "dataset_class_uid": row[headers.index("table")],
                    "variable_class_uid": row[headers.index("column")].replace(
                        "__", "--"
                    ),
                    "is_basic_std": self.parse_bool(row[headers.index("basic_std")]),
                    "label": row[headers.index("label")],
                    "order": row[headers.index("order")],
                    "variable_type": row[headers.index("type")],
                    "length": row[headers.index("length")],
                    "display_format": row[headers.index("displayformat")],
                    "xml_datatype": row[headers.index("xmldatatype")],
                    "xml_codelist": row[headers.index("xmlcodelist")],
                    "core": row[headers.index("core")],
                    "origin": row[headers.index("origin")],
                    "role": row[headers.index("role")],
                    "term": row[headers.index("term")],
                    "algorithm": row[headers.index("algorithm")],
                    "qualifiers": (
                        row[headers.index("qualifiers")].split(" ")
                        if row[headers.index("qualifiers")]
                        else None
                    ),
                    "comment": row[headers.index("comment")],
                    "ig_comment": row[headers.index("IGcomment")],
                    "map_var_flag": self.parse_bool(row[headers.index("map_var_flag")]),
                    "fixed_mapping": row[headers.index("fixed_mapping")],
                    "include_in_raw": self.parse_bool(
                        row[headers.index("include_in_raw")]
                    ),
                    "nn_internal": self.parse_bool(row[headers.index("nn_internal")]),
                    "incl_cre_domain": self.parse_bool(
                        row[headers.index("incl_cre_domain")]
                    ),
                    "xml_codelist_values": self.parse_bool(
                        row[headers.index("xmlcodelistvalues")]
                    ),
                    **self._common_body_params,
                }
            }
            self.log.info(
                f"Add sponsor model variable class '{data['body']['variable_class_uid']}' to dataset class '{data['body']['dataset_class_uid']}'"
            )
            api_tasks.append(
                self.api.post_to_api_async(
                    url=SPONSOR_MODELS_VARIABLE_CLASSES_PATH,
                    body=data["body"],
                    session=session,
                )
            )
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_datasets(self, csvfile, session):
        # Populate sponsor model datasets
        csv_reader = csv.reader(csvfile, delimiter=",")
        headers = next(csv_reader)
        api_tasks = []

        for row in csv_reader:
            if (
                row[headers.index("Standardref")].startswith("SDTMIG")
                or row[headers.index("Standardref")] == ""
            ):
                data = {
                    "body": {
                        "dataset_uid": row[headers.index("Table")],
                        "is_basic_std": self.parse_bool(
                            row[headers.index("basic_std")]
                        ),
                        "label": row[headers.index("Label")],
                        "xml_path": row[headers.index("XmlPath")],
                        "xml_title": row[headers.index("XmlTitle")],
                        "structure": row[headers.index("Structure")],
                        "purpose": row[headers.index("Purpose")],
                        "keys": (
                            row[headers.index("Keys")].split(" ")
                            if row[headers.index("Keys")]
                            else None
                        ),
                        "sort_keys": (
                            row[headers.index("SortKeys")]
                            if row[headers.index("SortKeys")]
                            else None
                        ),
                        "state": row[headers.index("State")],
                        "source_ig": row[headers.index("Standardref")],
                        "comment": row[headers.index("comment")],
                        "ig_comment": row[headers.index("IGcomment")],
                        "map_domain_flag": self.parse_bool(
                            row[headers.index("map_domain_flag")]
                        ),
                        "suppl_qual_flag": self.parse_bool(
                            row[headers.index("suppl_qual_flag")]
                        ),
                        "include_in_raw": self.parse_bool(
                            row[headers.index("include_in_raw")]
                        ),
                        "gen_raw_seqno_flag": self.parse_bool(
                            row[headers.index("gen_raw_seqno_flag")]
                        ),
                        "extended_domain": row[headers.index("extended_domain")],
                        "enrich_build_order": (
                            row[headers.index("enrich_build_order")]
                            if row[headers.index("enrich_build_order")]
                            else 0
                        ),
                        **self._common_body_params,
                    },
                }
                self.log.info(
                    f"Add sponsor model dataset '{data['body']['dataset_uid']}' to sponsor model '{data['body']['sponsor_model_name']}'"
                )
                api_tasks.append(
                    self.api.post_to_api_async(
                        url=SPONSOR_MODELS_DATASETS_PATH,
                        body=data["body"],
                        session=session,
                    )
                )
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_dataset_variables(self, csvfile, session):
        # Populate sponsor model dataset variables
        csv_reader = csv.reader(csvfile, delimiter=",")
        headers = next(csv_reader)
        api_tasks = []

        for row in csv_reader:
            data = {
                "body": {
                    "dataset_uid": row[headers.index("table")],
                    "dataset_variable_uid": row[headers.index("column")],
                    "is_basic_std": self.parse_bool(row[headers.index("basic_std")]),
                    "label": row[headers.index("label")],
                    "order": row[headers.index("order")],
                    "variable_type": row[headers.index("type")],
                    "length": row[headers.index("length")],
                    "display_format": row[headers.index("displayformat")],
                    "xml_datatype": row[headers.index("xmldatatype")],
                    "xml_codelist": row[headers.index("xmlcodelist")],
                    "xml_codelist_multi": row[headers.index("xmlcodelist_multi")].split(
                        " "
                    ),
                    "core": row[headers.index("core")],
                    "origin": row[headers.index("origin")],
                    "role": row[headers.index("role")],
                    "term": row[headers.index("term")],
                    "algorithm": row[headers.index("algorithm")],
                    "qualifiers": (
                        row[headers.index("qualifiers")].split(" ")
                        if row[headers.index("qualifiers")]
                        else None
                    ),
                    "comment": row[headers.index("comment")],
                    "ig_comment": row[headers.index("IGcomment")],
                    "map_var_flag": self.parse_bool(row[headers.index("map_var_flag")]),
                    "fixed_mapping": row[headers.index("fixed_mapping")],
                    "include_in_raw": self.parse_bool(
                        row[headers.index("include_in_raw")]
                    ),
                    "nn_internal": self.parse_bool(row[headers.index("nn_internal")]),
                    "value_lvl_where_cols": row[headers.index("value_lvl_where_cols")],
                    "value_lvl_label_col": row[headers.index("value_lvl_label_col")],
                    "value_lvl_collect_ct_val": row[
                        headers.index("value_lvl_collect_ct_val")
                    ],
                    "value_lvl_ct_codelist_id_col": row[
                        headers.index("value_lvl_ct_cdlist_id_col")
                    ],
                    "enrich_build_order": (
                        row[headers.index("enrich_build_order")]
                        if row[headers.index("enrich_build_order")]
                        else 0
                    ),
                    "enrich_rule": row[headers.index("enrich_rule")],
                    "xml_codelist_values": self.parse_bool(
                        row[headers.index("xmlcodelistvalues")]
                    ),
                    **self._common_body_params,
                },
            }
            self.log.info(
                f"Add sponsor model variable '{data['body']['dataset_variable_uid']}' to dataset '{data['body']['dataset_uid']}'"
            )
            api_tasks.append(
                self.api.post_to_api_async(
                    url=SPONSOR_MODELS_DATASET_VARIABLES_PATH,
                    body=data["body"],
                    session=session,
                )
            )
        await asyncio.gather(*api_tasks)

    async def async_run(self):
        timeout = aiohttp.ClientTimeout(None)
        conn = aiohttp.TCPConnector(limit=4, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
            await self.handle_activity_instance_class_relations(
                MDR_MIGRATION_ACTIVITY_INSTANCE_CLASS_MODEL_RELS,
                session,
            )

            # For each subfolder in the sponsor models folder, import the corresponding sponsor model
            for root, dirs, _ in os.walk(MDR_MIGRATION_SPONSOR_MODEL_DIRECTORY):
                dirs.sort()
                for dir_name in dirs:
                    sponsor_model_path = os.path.join(root, dir_name)

                    # Open file model_info.json in directory
                    with open(os.path.join(sponsor_model_path, "model_info.json")) as f:
                        model_info = json.load(f)
                        if "exclude" in model_info and model_info["exclude"]:
                            self.log.info(
                                f"Skipping sponsor model '{model_info['sponsor_model_name']}'"
                            )
                            continue
                        self._common_body_params = {
                            "sponsor_model_name": model_info["sponsor_model_name"],
                            "sponsor_model_version_number": model_info[
                                "sponsor_model_version_number"
                            ],
                        }

                        self._model_body_params = {
                            "ig_uid": model_info["ig_uid"],
                            "ig_version_number": model_info["ig_version_number"],
                            "version_number": model_info[
                                "sponsor_model_version_number"
                            ],
                        }

                    continue_import = await self.handle_sponsor_model(session)
                    if continue_import:
                        await self.handle_activity_item_class_relations(
                            os.path.join(
                                sponsor_model_path,
                                MDR_MIGRATION_SPONSOR_MODEL_VARIABLE_CLASSES,
                            ),
                            session,
                        )
                        await self.handle_dataset_classes(
                            os.path.join(
                                sponsor_model_path,
                                MDR_MIGRATION_SPONSOR_MODEL_DATASET_CLASSES,
                            ),
                            session,
                        )
                        await self.handle_variable_classes(
                            os.path.join(
                                sponsor_model_path,
                                MDR_MIGRATION_SPONSOR_MODEL_VARIABLE_CLASSES,
                            ),
                            session,
                        )
                        await self.handle_datasets(
                            os.path.join(
                                sponsor_model_path, MDR_MIGRATION_SPONSOR_MODEL_DATASETS
                            ),
                            session,
                        )
                        await self.handle_dataset_variables(
                            os.path.join(
                                sponsor_model_path,
                                MDR_MIGRATION_SPONSOR_MODEL_DATASET_VARIABLES,
                            ),
                            session,
                        )

    def run(self):
        self.log.info("Importing sponsor models")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_run())
        self.log.info("Done importing sponsor models")


def main():
    metr = Metrics()
    migrator = SponsorModels(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
