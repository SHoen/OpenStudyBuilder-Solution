import datetime
from collections import OrderedDict

from clinical_mdr_api.models import (
    CTTermName,
    StudyDesignCell,
    StudySelectionArmWithConnectedBranchArms,
    StudySelectionElement,
)
from clinical_mdr_api.models.study_epoch import StudyEpoch
from clinical_mdr_api.services.study_design_figure import StudyDesignFigureService
from clinical_mdr_api.tests.unit.services.test_study_flowchart import (
    STUDY_VISITS as _STUDY_VISITS,
)

STUDY_UID = "Study_000001"

USER_INITIALS = "unknown-user"

STUDY_ARMS = OrderedDict(
    (
        (
            "StudyArm_000009",
            StudySelectionArmWithConnectedBranchArms(
                studyUid=STUDY_UID,
                order=1,
                armUid="StudyArm_000009",
                name="NPH insulin",
                shortName="NPH insulin",
                description=None,
                code="A",
                armColour="#FFFDE7FF",
                randomizationGroup="A",
                numberOfSubjects=50,
                armType=CTTermName(
                    termUid="CTTerm_000081",
                    codelistUid="CTCodelist_000022",
                    sponsorPreferredName="Investigational Arm",
                    sponsorPreferredNameSentenceCase="investigational arm",
                    order=1,
                    startDate=datetime.datetime(2022, 7, 14, 11, 18, 29, 635044),
                ),
                startDate=datetime.datetime(2022, 8, 25, 19, 32, 11, 640636),
                userInitials=USER_INITIALS,
            ),
        ),
        (
            "StudyArm_000011",
            StudySelectionArmWithConnectedBranchArms(
                studyUid=STUDY_UID,
                order=2,
                armUid="StudyArm_000011",
                name="Metformin",
                shortName="Metformin is longer",
                description=None,
                code="B",
                armColour="#FFEBEEFF",
                randomizationGroup="B",
                numberOfSubjects=50,
                armType=CTTermName(
                    termUid="CTTerm_000081",
                    codelistUid="CTCodelist_000022",
                    sponsorPreferredName="Investigational Arm",
                    sponsorPreferredNameSentenceCase="investigational arm",
                    order=1,
                    startDate=datetime.datetime(2022, 7, 14, 11, 18, 29, 635044),
                ),
                startDate=datetime.datetime(2022, 8, 25, 9, 33, 24, 232339),
                userInitials=USER_INITIALS,
            ),
        ),
        (
            "StudyArm_000045",
            StudySelectionArmWithConnectedBranchArms(
                studyUid=STUDY_UID,
                order=3,
                armUid="StudyArm_000045",
                name="Another arm",
                shortName="Another arm",
                description=None,
                code=None,
                armColour="#F3E5F5FF",
                randomizationGroup=None,
                numberOfSubjects=None,
                armType=None,
                startDate=datetime.datetime(2022, 8, 25, 19, 32, 0, 886693),
                userInitials=USER_INITIALS,
            ),
        ),
        (
            "StudyArm_000048",
            StudySelectionArmWithConnectedBranchArms(
                studyUid=STUDY_UID,
                order=4,
                armUid="StudyArm_000048",
                name="More arms",
                shortName="More arms",
                description=None,
                code=None,
                armColour="#E8EAF6FF",
                randomizationGroup=None,
                numberOfSubjects=None,
                armType=None,
                startDate=datetime.datetime(2022, 8, 25, 19, 46, 11, 300649),
                userInitials=USER_INITIALS,
            ),
        ),
    )
)

STUDY_EPOCHS = OrderedDict(
    (
        (
            "StudyEpoch_000001",
            StudyEpoch(
                studyUid=STUDY_UID,
                startRule="Subject must sign informed consent",
                epoch="C48262_SCREENING",
                epochSubType="C48262_SCREENING",
                order=1,
                duration=15,
                colorHash="#A5D6A7FF",
                uid="StudyEpoch_000001",
                epochName="Screening",
                epochSubTypeName="Screening",
                epochType="CTTerm_000001",
                startDay=-14,
                endDay=1,
                startDate="2022-07-16 09:13:42",
                status="DRAFT",
                userInitials="TODO Initials",
                possibleActions=["edit", "delete", "lock"],
                changeDescription="Initial Version",
                studyVisitCount=1,
            ),
        ),
        (
            "StudyEpoch_000002",
            StudyEpoch(
                studyUid=STUDY_UID,
                startRule="Subject must fulfil randomisation criteria",
                epoch="C101526_TREATMENT",
                epochSubType="C101526_TREATMENT",
                order=2,
                duration=63,
                colorHash="#2E7D32FF",
                uid="StudyEpoch_000002",
                epochName="Treatment",
                epochSubTypeName="Treatment",
                epochType="C101526_TREATMENT",
                startDay=1,
                endDay=64,
                startDate="2022-07-16 09:13:42",
                status="DRAFT",
                userInitials="TODO Initials",
                possibleActions=["edit", "delete", "lock"],
                changeDescription="Initial Version",
                studyVisitCount=9,
            ),
        ),
        (
            "StudyEpoch_000042",
            StudyEpoch(
                studyUid=STUDY_UID,
                startRule="",
                epoch="CTTerm_000007",
                epochSubType="CTTerm_000007",
                order=3,
                description="Treatment Extension",
                duration=119,
                colorHash="#80DEEAFF",
                uid="StudyEpoch_000042",
                epochName="Extension",
                epochSubTypeName="Extension",
                epochType="C101526_TREATMENT",
                startDay=64,
                endDay=183,
                startDate="2022-08-26 02:06:50",
                status="DRAFT",
                userInitials="TODO Initials",
                possibleActions=["edit", "delete", "lock"],
                changeDescription="Initial Version",
                studyVisitCount=1,
            ),
        ),
        (
            "StudyEpoch_000003",
            StudyEpoch(
                studyUid=STUDY_UID,
                startRule="Subject must attend follow-up visit",
                epoch="C99158_FOLLOW-UP",
                epochSubType="C99158_FOLLOW-UP",
                order=4,
                duration=183,
                colorHash="#009688FF",
                uid="StudyEpoch_000003",
                epochName="Follow-up",
                epochSubTypeName="Follow-up",
                epochType="CTTerm_000003",
                startDay=183,
                endDay=366,
                startDate="2022-08-26 02:06:50",
                status="DRAFT",
                userInitials="TODO Initials",
                possibleActions=["edit", "delete", "lock"],
                changeDescription="Initial Version",
                studyVisitCount=1,
            ),
        ),
        (
            "StudyEpoch_000034",
            StudyEpoch(
                studyUid=STUDY_UID,
                epoch="CTTerm_000008",
                epochSubType="CTTerm_000008",
                order=5,
                description="Hula lula",
                duration=7,
                colorHash="#C5CAE9FF",
                uid="StudyEpoch_000034",
                epochName="Elimination",
                epochSubTypeName="Elimination",
                epochType="CTTerm_000003",
                startDay=366,
                endDay=373,
                startDate="2022-08-26 02:06:50",
                status="DRAFT",
                userInitials="TODO Initials",
                possibleActions=["edit", "delete", "lock"],
                changeDescription="Initial Version",
                studyVisitCount=1,
            ),
        ),
        (
            "StudyEpoch_000041",
            StudyEpoch(
                studyUid=STUDY_UID,
                epoch="CTTerm_000005",
                epochSubType="CTTerm_000005",
                order=6,
                duration=0,
                colorHash="#80CBC4FF",
                uid="StudyEpoch_000041",
                epochName="Dose Escalation",
                epochSubTypeName="Dose Escalation",
                epochType="C101526_TREATMENT",
                startDate="2022-08-26 02:06:50",
                status="DRAFT",
                userInitials="TODO Initials",
                possibleActions=["edit", "delete", "lock", "reorder"],
                changeDescription="Initial Version",
                studyVisitCount=0,
            ),
        ),
    )
)

STUDY_ELEMENTS = OrderedDict(
    (
        (
            "StudyElement_000018",
            StudySelectionElement(
                studyUid=STUDY_UID,
                order=1,
                startRule=None,
                endRule=None,
                description=None,
                elementUid="StudyElement_000018",
                name="Screening",
                shortName="Screening",
                code="CTTerm_000130",
                plannedDuration=None,
                elementColour=None,
                elementSubType=CTTermName(
                    termUid="CTTerm_000135",
                    codelistUid="CTCodelist_000024",
                    sponsorPreferredName="Screening",
                    sponsorPreferredNameSentenceCase="screening",
                    order=1,
                    startDate=datetime.datetime(2022, 7, 14, 11, 18, 43, 459307),
                ),
                studyCompoundDosingCount=0,
                startDate=datetime.datetime(2022, 7, 22, 9, 57, 9, 373874),
                userInitials=USER_INITIALS,
            ),
        ),
        (
            "StudyElement_000020",
            StudySelectionElement(
                studyUid=STUDY_UID,
                order=2,
                startRule=None,
                endRule=None,
                description=None,
                elementUid="StudyElement_000020",
                name="NPH insulin",
                shortName="NPH insulin",
                code="CTTerm_000129",
                plannedDuration=None,
                elementColour=None,
                elementSubType=CTTermName(
                    termUid="CTTerm_000131",
                    codelistUid="CTCodelist_000024",
                    sponsorPreferredName="Treatment",
                    sponsorPreferredNameSentenceCase="treatment",
                    order=3,
                    startDate=datetime.datetime(2022, 7, 14, 11, 18, 42, 889737),
                ),
                studyCompoundDosingCount=0,
                startDate=datetime.datetime(2022, 7, 22, 9, 57, 10, 406127),
                userInitials=USER_INITIALS,
            ),
        ),
        (
            "StudyElement_000022",
            StudySelectionElement(
                studyUid=STUDY_UID,
                order=3,
                startRule=None,
                endRule=None,
                description=None,
                elementUid="StudyElement_000022",
                name="Metformin",
                shortName="Metformin",
                code="CTTerm_000129",
                plannedDuration=None,
                elementColour=None,
                elementSubType=CTTermName(
                    termUid="CTTerm_000131",
                    codelistUid="CTCodelist_000024",
                    sponsorPreferredName="Treatment",
                    sponsorPreferredNameSentenceCase="treatment",
                    order=3,
                    startDate=datetime.datetime(2022, 7, 14, 11, 18, 42, 889737),
                ),
                studyCompoundDosingCount=0,
                startDate=datetime.datetime(2022, 7, 22, 9, 57, 10, 503358),
                userInitials=USER_INITIALS,
            ),
        ),
        (
            "StudyElement_000024",
            StudySelectionElement(
                studyUid=STUDY_UID,
                order=4,
                startRule=None,
                endRule=None,
                description=None,
                elementUid="StudyElement_000024",
                name="Follow-up",
                shortName="Follow-up",
                code="CTTerm_000130",
                plannedDuration=None,
                elementColour=None,
                elementSubType=CTTermName(
                    termUid="CTTerm_000134",
                    codelistUid="CTCodelist_000024",
                    sponsorPreferredName="Follow-up",
                    sponsorPreferredNameSentenceCase="follow-up",
                    order=5,
                    startDate=datetime.datetime(2022, 7, 14, 11, 18, 43, 264949),
                ),
                studyCompoundDosingCount=0,
                startDate=datetime.datetime(2022, 7, 22, 9, 57, 10, 985130),
                userInitials=USER_INITIALS,
            ),
        ),
    )
)

STUDY_DESIGN_CELLS = (
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000011",
        studyArmUid="StudyArm_000009",
        studyArmName="NPH insulin",
        studyEpochUid="StudyEpoch_000001",
        studyEpochName="Screening",
        studyElementUid="StudyElement_000018",
        studyElementName="Screening",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 16, 9, 37, 25, 904287),
        userInitials=USER_INITIALS,
        order=1,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000012",
        studyArmUid="StudyArm_000009",
        studyArmName="NPH insulin",
        studyEpochUid="StudyEpoch_000002",
        studyEpochName="Treatment",
        studyElementUid="StudyElement_000020",
        studyElementName="NPH insulin",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 16, 9, 37, 25, 749029),
        userInitials=USER_INITIALS,
        order=2,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000013",
        studyArmUid="StudyArm_000009",
        studyArmName="NPH insulin",
        studyEpochUid="StudyEpoch_000003",
        studyEpochName="Follow-up",
        studyElementUid="StudyElement_000024",
        studyElementName="Follow-up",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 16, 9, 37, 25, 583916),
        userInitials=USER_INITIALS,
        order=3,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000014",
        studyArmUid="StudyArm_000009",
        studyArmName="NPH insulin",
        studyEpochUid="StudyEpoch_000034",
        studyEpochName="Elimination",
        studyElementUid="StudyElement_000020",
        studyElementName="NPH insulin",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 16, 9, 37, 25, 309418),
        userInitials=USER_INITIALS,
        order=4,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000015",
        studyArmUid="StudyArm_000011",
        studyArmName="Metformin",
        studyEpochUid="StudyEpoch_000001",
        studyEpochName="Screening",
        studyElementUid="StudyElement_000018",
        studyElementName="Screening",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 16, 9, 35, 11, 107228),
        userInitials=USER_INITIALS,
        order=5,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000016",
        studyArmUid="StudyArm_000011",
        studyArmName="Metformin",
        studyEpochUid="StudyEpoch_000002",
        studyEpochName="Treatment",
        studyElementUid="StudyElement_000022",
        studyElementName="Metformin",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 16, 9, 35, 12, 69303),
        userInitials=USER_INITIALS,
        order=6,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000017",
        studyArmUid="StudyArm_000011",
        studyArmName="Metformin",
        studyEpochUid="StudyEpoch_000003",
        studyEpochName="Follow-up",
        studyElementUid="StudyElement_000024",
        studyElementName="Follow-up",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 16, 9, 35, 12, 323734),
        userInitials=USER_INITIALS,
        order=7,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000018",
        studyArmUid="StudyArm_000011",
        studyArmName="Metformin",
        studyEpochUid="StudyEpoch_000034",
        studyEpochName="Elimination",
        studyElementUid="StudyElement_000022",
        studyElementName="Metformin",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 16, 9, 35, 12, 591836),
        userInitials=USER_INITIALS,
        order=8,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000039",
        studyArmUid="StudyArm_000045",
        studyArmName="Another arm",
        studyEpochUid="StudyEpoch_000002",
        studyEpochName="Treatment",
        studyElementUid="StudyElement_000020",
        studyElementName="NPH insulin",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 25, 22, 54, 8, 133786),
        userInitials=USER_INITIALS,
        order=9,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000042",
        studyArmUid="StudyArm_000045",
        studyArmName="Another arm",
        studyEpochUid="StudyEpoch_000003",
        studyEpochName="Follow-up",
        studyElementUid="StudyElement_000020",
        studyElementName="NPH insulin",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 26, 2, 7, 34, 231184),
        userInitials=USER_INITIALS,
        order=10,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000044",
        studyArmUid="StudyArm_000009",
        studyArmName="NPH insulin",
        studyEpochUid="StudyEpoch_000042",
        studyEpochName="Extension",
        studyElementUid="StudyElement_000020",
        studyElementName="NPH insulin",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 26, 2, 7, 34, 318480),
        userInitials=USER_INITIALS,
        order=11,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000045",
        studyArmUid="StudyArm_000011",
        studyArmName="Metformin",
        studyEpochUid="StudyEpoch_000042",
        studyEpochName="Extension",
        studyElementUid="StudyElement_000022",
        studyElementName="Metformin",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 26, 2, 8, 31, 590352),
        userInitials=USER_INITIALS,
        order=12,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000046",
        studyArmUid="StudyArm_000045",
        studyArmName="Another arm",
        studyEpochUid="StudyEpoch_000042",
        studyEpochName="Extension",
        studyElementUid="StudyElement_000022",
        studyElementName="Metformin",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 26, 2, 8, 31, 765647),
        userInitials=USER_INITIALS,
        order=13,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000047",
        studyArmUid="StudyArm_000009",
        studyArmName="NPH insulin",
        studyEpochUid="StudyEpoch_000042",
        studyEpochName="Extension",
        studyElementUid="StudyElement_000020",
        studyElementName="NPH insulin",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 26, 2, 7, 59, 750359),
        userInitials=USER_INITIALS,
        order=14,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000048",
        studyArmUid="StudyArm_000011",
        studyArmName="Metformin",
        studyEpochUid="StudyEpoch_000042",
        studyEpochName="Extension",
        studyElementUid="StudyElement_000020",
        studyElementName="NPH insulin",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 26, 2, 8, 0, 315389),
        userInitials=USER_INITIALS,
        order=15,
    ),
    StudyDesignCell(
        studyUid=STUDY_UID,
        designCellUid="StudyDesignCell_000049",
        studyArmUid="StudyArm_000045",
        studyArmName="Another arm",
        studyEpochUid="StudyEpoch_000042",
        studyEpochName="Extension",
        studyElementUid="StudyElement_000020",
        studyElementName="NPH insulin",
        transitionRule=None,
        startDate=datetime.datetime(2022, 8, 26, 2, 8, 0, 807474),
        userInitials=USER_INITIALS,
        order=16,
    ),
)

STUDY_VISITS = OrderedDict((visit.uid, visit) for visit in _STUDY_VISITS.items)

MATRIX = [
    [
        {},
        {
            "klass": "epoch",
            "id": "StudyEpoch_000001",
            "text": "Screening",
            "colors": ("#a5d6a7", "#204621", "#000"),
            "margin": 10,
            "paddings": (3, 3),
        },
        {
            "klass": "epoch",
            "id": "StudyEpoch_000002",
            "text": "Treatment",
            "colors": ("#2e7d32", "#1b4b1e", "#fff"),
            "margin": 10,
            "paddings": (3, 3),
        },
        {
            "klass": "epoch",
            "id": "StudyEpoch_000042",
            "text": "Extension",
            "colors": ("#80deea", "#0e4f58", "#000"),
            "margin": 10,
            "paddings": (3, 3),
        },
        {
            "klass": "epoch",
            "id": "StudyEpoch_000003",
            "text": "Follow-up",
            "colors": ("#009688", "#00665c", "#fff"),
            "margin": 10,
            "paddings": (3, 3),
        },
        {
            "klass": "epoch",
            "id": "StudyEpoch_000034",
            "text": "Elimination",
            "colors": ("#c5cae9", "#1c224a", "#000"),
            "margin": 10,
            "paddings": (3, 3),
        },
        {
            "klass": "epoch",
            "id": "StudyEpoch_000041",
            "text": "Dose Escalation",
            "colors": ("#80cbc4", "#1e4844", "#000"),
            "margin": 10,
            "paddings": (3, 3),
        },
    ],
    [
        {
            "klass": "arm",
            "id": "StudyArm_000009",
            "text": "NPH insulin",
            "colors": ("#fffde7", "#665d00", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000018",
            "text": "Screening",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000024",
            "text": "Follow-up",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {},
    ],
    [
        {
            "klass": "arm",
            "id": "StudyArm_000011",
            "text": "Metformin is longer",
            "colors": ("#ffebee", "#66000f", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000018",
            "text": "Screening",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000022",
            "text": "Metformin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000024",
            "text": "Follow-up",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000022",
            "text": "Metformin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {},
    ],
    [
        {
            "klass": "arm",
            "id": "StudyArm_000045",
            "text": "Another arm",
            "colors": ("#f3e5f5", "#441c4a", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {},
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {
            "klass": "element",
            "id": "StudyElement_000020",
            "text": "NPH insulin",
            "colors": ("#d2e4f3", "#153651", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {},
        {},
    ],
    [
        {
            "klass": "arm",
            "id": "StudyArm_000048",
            "text": "More arms",
            "colors": ("#e8eaf6", "#1d2349", "#000"),
            "margin": 5,
            "paddings": (5, 5),
        },
        {},
        {},
        {},
        {},
        {},
        {},
    ],
]

VISIT_IDS = {
    "StudyVisit_000021",
    "StudyVisit_000022",
    "StudyVisit_000044",
    "StudyVisit_000031",
    "StudyVisit_000045",
}

TIMELINE = {
    "labels": [
        [
            {
                "id": "CTTerm_000171",
                "klass": "visit-type",
                "paddings": (0, 0),
                "text": "Screening",
                "width": 114,
                "x": 175,
                "y": 227,
                "height": 20,
                "lines": ((25, 16, "Screening"),),
            },
            {
                "id": "CTTerm_000176",
                "klass": "visit-type",
                "paddings": (0, 0),
                "text": "Treatment",
                "width": 270,
                "x": 299,
                "y": 227,
                "height": 20,
                "lines": ((102, 16, "Treatment"),),
            },
            {
                "id": "CTTerm_000161",
                "klass": "visit-type",
                "paddings": (0, 0),
                "text": "Follow-up",
                "width": 130,
                "x": 579,
                "y": 227,
                "height": 20,
                "lines": ((31, 16, "Follow-up"),),
            },
            {
                "id": "CTTerm_000164",
                "klass": "visit-type",
                "paddings": (0, 0),
                "text": "Post treatment activity",
                "width": 130,
                "x": 719,
                "y": 218,
                "height": 39,
                "lines": ((18, 16, "Post treatment"), (41, 35, "activity")),
            },
        ],
        [
            {
                "id": "StudyVisit_000021",
                "klass": "visit-timing",
                "paddings": (0, 0),
                "text": "Week -2",
                "x": 175,
                "y": 279,
                "width": 53,
                "height": 15,
                "lines": ((0, 16, "Week -2"),),
            },
            {
                "id": "StudyVisit_000022",
                "klass": "visit-timing",
                "paddings": (0, 0),
                "text": "Week 1",
                "x": 299,
                "y": 279,
                "width": 48,
                "height": 15,
                "lines": ((0, 16, "Week 1"),),
            },
            {
                "id": "StudyVisit_000044",
                "klass": "visit-timing",
                "paddings": (0, 0),
                "text": "Week 10",
                "x": 439,
                "y": 279,
                "width": 56,
                "height": 15,
                "lines": ((0, 16, "Week 10"),),
            },
            {
                "id": "StudyVisit_000031",
                "klass": "visit-timing",
                "paddings": (0, 0),
                "text": "Week 27",
                "x": 579,
                "y": 279,
                "width": 56,
                "height": 15,
                "lines": ((0, 16, "Week 27"),),
            },
            {
                "id": "StudyVisit_000045",
                "klass": "visit-timing",
                "paddings": (0, 0),
                "text": "Week 53",
                "x": 719,
                "y": 279,
                "width": 56,
                "height": 15,
                "lines": ((0, 16, "Week 53"),),
            },
        ],
    ],
    "arrows": [
        {"klass": "timeline-arrow", "x1": 175, "x2": 299, "y1": 262, "y2": 262},
        {"klass": "timeline-arrow", "x1": 299, "x2": 579, "y1": 262, "y2": 262},
        {"klass": "timeline-arrow", "x1": 579, "x2": 719, "y1": 262, "y2": 262},
        {"klass": "timeline-arrow", "x1": 719, "x2": 859, "y1": 262, "y2": 262},
        {"klass": "visit-arrow", "x1": 175, "x2": 175, "y1": 276, "y2": 264},
        {"klass": "visit-arrow", "x1": 299, "x2": 299, "y1": 276, "y2": 264},
        {"klass": "visit-arrow", "x1": 439, "x2": 439, "y1": 276, "y2": 264},
        {"klass": "visit-arrow", "x1": 579, "x2": 579, "y1": 276, "y2": 264},
        {"klass": "visit-arrow", "x1": 719, "x2": 719, "y1": 276, "y2": 264},
    ],
}


class MockStudyDesignFigureService(StudyDesignFigureService):
    @staticmethod
    def _get_study_arms(*_args, **_kwargs):
        return STUDY_ARMS

    @staticmethod
    def _get_study_epochs(*_args, **_kwargs):
        return STUDY_EPOCHS

    @staticmethod
    def _get_study_elements(*_args, **_kwargs):
        return STUDY_ELEMENTS

    @staticmethod
    def _get_study_design_cells(*_args, **_kwargs):
        return STUDY_DESIGN_CELLS

    @staticmethod
    def _get_study_visits(*_args, **_kwargs):
        return STUDY_VISITS


def test_mk_data_matrix():
    table = MockStudyDesignFigureService()._mk_data_matrix(
        STUDY_ARMS, STUDY_EPOCHS, STUDY_ELEMENTS, STUDY_DESIGN_CELLS
    )
    assert table == MATRIX


def test_select_first_visits():
    visits = MockStudyDesignFigureService()._select_first_visits(
        STUDY_VISITS, STUDY_EPOCHS
    )
    visit_ids = {visit["id"] for visit in visits if visit}
    assert visit_ids == VISIT_IDS


def test_mk_timeline():
    # pylint: disable=unused-argument
    def draw_svg(table, timeline, doc_width, doc_height):
        # pylint: disable=unused-variable
        __tracebackhide__ = True
        assert timeline == TIMELINE

    service = MockStudyDesignFigureService()
    service.draw_svg = draw_svg
    service.get_svg_document("")


# pylint: disable=unsupported-membership-test
def test_get_svg_document():
    service = MockStudyDesignFigureService()
    doc: str = service.get_svg_document("")

    assert "</svg>" in doc, "no </svg> tag in document, not an SVG?"
    assert "</defs>" in doc, "no </defs> tag in document, missing defs?"
    assert "</style>" in doc, "no </style> tag in document, missing styles?"

    assert 'class="arm"' in doc, 'class="arm" found, missing arms?'
    assert 'class="epoch"' in doc, 'class="epoch" found, missing epochs?'
    assert (
        'class="element"' in doc
    ), 'class="element" found, missing study design cells?'

    for id_ in STUDY_ARMS.keys():
        assert f'id="{id_}"' in doc, f'arm id="{id_}" not found in document'
    for id_ in STUDY_EPOCHS.keys():
        assert f'id="{id_}"' in doc, f'epoch id="{id_}" not found in document'
    for id_ in STUDY_ELEMENTS.keys():
        assert f'id="{id_}"' in doc, f'element id="{id_}" not found in document'

    assert (
        'class="visit-type"' in doc
    ), 'class="visit-type" found, missing visit type labels?'
    assert (
        'class="visit-timing"' in doc
    ), 'class="visit-timing" found, missing visit milestones?'

    assert (
        'class="timeline-arrow"' in doc
    ), 'class="timeline-arrow" not found, missing timeline arrows?'
    assert (
        'class="timeline-arrow"' in doc
    ), 'class="visit-arrow" not found, missing visit arrows?'
    assert "markerWidth" in doc, '"markerWidth" found, missing arrowhead markers?'
