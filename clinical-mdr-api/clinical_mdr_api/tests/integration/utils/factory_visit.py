from clinical_mdr_api.config import (
    DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
    WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER,
)
from clinical_mdr_api.models import StudyVisit
from clinical_mdr_api.models.study_visit import (
    StudyVisitCreateInput,
    StudyVisitEditInput,
)
from clinical_mdr_api.models.unit_definition import UnitDefinitionPostInput
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.study_visit import StudyVisitService
from clinical_mdr_api.services.unit_definition import UnitDefinitionService
from clinical_mdr_api.tests.integration.utils.factory_controlled_terminology import (
    create_codelist,
    create_ct_term,
    get_catalogue_name_library_name,
    get_unit_uid_by_name,
)
from clinical_mdr_api.tests.integration.utils.factory_epoch import (
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
)

DAY = {
    "name": "day",
    "libraryName": "Sponsor",
    "ctUnits": ["unit1-ct-uid"],
    "convertibleUnit": True,
    "displayUnit": True,
    "masterUnit": False,
    "siUnit": True,
    "usConventionalUnit": True,
    "unitDimension": "TIME_UID",
    "legacyCode": "unit1-legacy-code",
    "molecularWeightConvExpon": 0,
    "conversionFactorToMaster": DAY_UNIT_CONVERSION_FACTOR_TO_MASTER,
}

WEEK = {
    "name": "week",
    "libraryName": "Sponsor",
    "ctUnits": ["unit2-ct-uid"],
    "convertibleUnit": True,
    "displayUnit": True,
    "masterUnit": False,
    "siUnit": False,
    "usConventionalUnit": True,
    "unitDimension": "TIME_UID",
    "legacyCode": "unit2-legacy-code",
    "molecularWeightConvExpon": 0,
    "conversionFactorToMaster": WEEK_UNIT_CONVERSION_FACTOR_TO_MASTER,
}


def generate_default_input_data_for_visit():
    DAYUID = get_unit_uid_by_name("day")
    WEEKUID = get_unit_uid_by_name("week")
    return {
        "legacyVisitId": "legacyVisit",
        "legacyVisitTypeAlias": "legacyVT",
        "legacyName": "legacyN",
        "legacySubVisitName": "",
        "visitSubLabelCodelistUid": "",
        "visitSubLabelReference": "",
        "consecutiveVisitGroup": "",
        "showVisit": True,
        "minVisitWindowValue": -1,
        "maxVisitWindowValue": 1,
        "visitWindowUnitUid": DAYUID,
        "timeUnitUid": WEEKUID,
        "timeValue": 12,
        "description": "description",
        "startRule": "startRule",
        "endRule": "endRule",
        "note": "note",
        "visitContactModeUid": "VisitContactMode_0001",
        "visitTypeUid": "VisitType_0003",
        "timeReferenceUid": WEEKUID,
        "isGlobalAnchorVisit": False,
        "visitClass": "SINGLE_VISIT",
        "visitSubclass": "SINGLE_VISIT",
    }


def create_study_visit_codelists():
    catalogue_name, library_name = get_catalogue_name_library_name()
    create_study_epoch_codelists_ret_cat_and_lib()

    unit_dim_codelist = create_codelist(
        "Unit Dimension", "CTCodelist_UnitDim", catalogue_name, library_name
    )
    create_ct_term(
        unit_dim_codelist.codelistUid,
        "TIME",
        "TIME_UID",
        1,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        unit_dim_codelist.codelistUid,
        "WEEK",
        "WEEK_UID",
        2,
        catalogue_name,
        library_name,
    )

    ct_unit_codelist = create_codelist(
        "CT Unit", "CTCodelist_CTUnit", catalogue_name, library_name
    )
    create_ct_term(
        ct_unit_codelist.codelistUid,
        "ct unit 1",
        "unit1-ct-uid",
        1,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        ct_unit_codelist.codelistUid,
        "ct unit 2",
        "unit2-ct-uid",
        2,
        catalogue_name,
        library_name,
    )

    unit_service = UnitDefinitionService(
        user_id="some-user", meta_repository=MetaRepository()
    )
    unit_service.post(UnitDefinitionPostInput(**WEEK))
    unit_service.post(UnitDefinitionPostInput(**DAY))

    codelist = create_codelist(
        "VisitType", "CTCodelist_00004", catalogue_name, library_name
    )
    create_ct_term(
        codelist.codelistUid,
        "BASELINE",
        "VisitType_0001",
        1,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelistUid,
        "BASELINE2",
        "VisitType_0002",
        2,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelistUid,
        "Visit Type2",
        "VisitType_0003",
        3,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelistUid,
        "Visit Type3",
        "VisitType_0004",
        4,
        catalogue_name,
        library_name,
    )

    codelist = create_codelist(
        "Time Point Reference", "CTCodelist_00005", catalogue_name, library_name
    )
    create_ct_term(
        codelist.codelistUid,
        "BASELINE",
        "VisitSubType_0001",
        1,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelistUid,
        "BASELINE2",
        "VisitSubType_0002",
        2,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelistUid,
        "Visit Sub Type2",
        "VisitSubType_0003",
        3,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelistUid,
        "Visit Sub Type3",
        "VisitSubType_0004",
        4,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelistUid,
        "Global anchor visit",
        "VisitSubType_0005",
        5,
        catalogue_name,
        library_name,
    )

    codelist = create_codelist(
        "Visit Sub Label", "CTCodelist_00006", catalogue_name, library_name
    )
    create_ct_term(
        codelist.codelistUid,
        "Visit Sub Label",
        "VisitSubLabel_0001",
        1,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelistUid,
        "Visit Sub Label1",
        "VisitSubLabel_0002",
        2,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelistUid,
        "Visit Sub Label2",
        "VisitSubLabel_0003",
        3,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelistUid,
        "Visit Sub Label3",
        "VisitSubLabel_0004",
        4,
        catalogue_name,
        library_name,
    )

    codelist = create_codelist(
        "Visit Contact Mode", "CTCodelist_00007", catalogue_name, library_name
    )
    create_ct_term(
        codelist.codelistUid,
        "On Site Visit",
        "VisitContactMode_0001",
        1,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelistUid,
        "Phone Contact",
        "VisitContactMode_0002",
        2,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelistUid,
        "Virtual Visit",
        "VisitContactMode_0003",
        3,
        catalogue_name,
        library_name,
    )

    codelist = create_codelist(
        "Epoch Allocation", "CTCodelist_00008", catalogue_name, library_name
    )
    create_ct_term(
        codelist.codelistUid,
        "Previous Visit",
        "EpochAllocation_0001",
        1,
        catalogue_name,
        library_name,
    )
    create_ct_term(
        codelist.codelistUid,
        "Current Visit",
        "EpochAllocation_0002",
        2,
        catalogue_name,
        library_name,
    )


def create_visit_with_update(**inputs) -> StudyVisit:
    visit_service: StudyVisitService = StudyVisitService()
    datadict = generate_default_input_data_for_visit().copy()
    datadict.update(inputs)
    visit_input = StudyVisitCreateInput(**datadict)
    visit = visit_service.create(study_uid="study_root", study_visit_input=visit_input)
    return visit


def update_visit_with_update(visit_uid: str, **inputs) -> StudyVisit:
    visit_service: StudyVisitService = StudyVisitService()
    datadict = generate_default_input_data_for_visit().copy()
    datadict.update(inputs)
    visit_input = StudyVisitEditInput(**datadict)
    visit = visit_service.edit(
        study_uid="study_root",
        study_visit_uid=visit_uid,
        study_visit_input=visit_input,
    )
    return visit


def preview_visit_with_update(study_uid, **inputs) -> StudyVisit:
    visit_service: StudyVisitService = StudyVisitService()
    datadict = generate_default_input_data_for_visit().copy()
    datadict.update(inputs)
    del datadict["visitWindowUnitUid"]
    visit_input = StudyVisitCreateInput(**datadict)
    preview: StudyVisit = visit_service.preview(study_uid, visit_input)
    return preview


def create_some_visits():
    create_study_visit_codelists()
    epoch1 = create_study_epoch("EpochSubType_0001")
    epoch2 = create_study_epoch("EpochSubType_0002")
    DAYUID = get_unit_uid_by_name("day")
    create_visit_with_update(
        studyEpochUid=epoch1.uid,
        visitTypeUid="VisitType_0001",
        timeReferenceUid="VisitSubType_0001",
        timeValue=0,
        timeUnitUid=DAYUID,
    )
    create_visit_with_update(
        studyEpochUid=epoch1.uid,
        visitTypeUid="VisitType_0003",
        timeReferenceUid="VisitSubType_0001",
        timeValue=12,
        timeUnitUid=DAYUID,
    )
    create_visit_with_update(
        studyEpochUid=epoch1.uid,
        visitTypeUid="VisitType_0003",
        timeReferenceUid="VisitSubType_0001",
        timeValue=10,
        timeUnitUid=DAYUID,
    )

    v3 = create_visit_with_update(
        studyEpochUid=epoch1.uid,
        visitTypeUid="VisitType_0004",
        timeReferenceUid="VisitSubType_0001",
        timeValue=20,
        timeUnitUid=DAYUID,
    )
    v4 = create_visit_with_update(
        studyEpochUid=epoch2.uid,
        visitTypeUid="VisitType_0002",
        timeReferenceUid="VisitSubType_0001",
        timeValue=30,
        timeUnitUid=DAYUID,
        visitSubLabelCodelistUid="VisitSubLabel_0001",
        visitSubLabelReference=None,
        visitClass="SINGLE_VISIT",
        visitSubclass="ANCHOR_VISIT_IN_GROUP_OF_SUBV",
    )
    create_visit_with_update(
        studyEpochUid=epoch2.uid,
        visitTypeUid="VisitType_0003",
        timeReferenceUid="VisitSubType_0002",
        timeValue=31,
        timeUnitUid=DAYUID,
        visitSubLabelCodelistUid="VisitSubLabel_0002",
        visitSubLabelReference=v4.uid,
        visitClass="SINGLE_VISIT",
        visitSubclass="ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
    )

    update_visit_with_update(
        v3.uid,
        uid=v3.uid,
        studyEpochUid=epoch1.uid,
        visitTypeUid="VisitType_0004",
        timeReferenceUid="VisitSubType_0001",
        timeValue=35,
        timeUnitUid=DAYUID,
    )
