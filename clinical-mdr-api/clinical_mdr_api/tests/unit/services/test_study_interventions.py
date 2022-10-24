import datetime

from clinical_mdr_api.models import CompoundAlias, StudySelectionCompound
from clinical_mdr_api.models.compound import Compound, SimpleCompound
from clinical_mdr_api.models.concept import SimpleLagTime, SimpleNumericValueWithUnit
from clinical_mdr_api.models.ct_term import SimpleTermModel
from clinical_mdr_api.models.dictionary_term import CompoundSubstance
from clinical_mdr_api.models.table import Table, TableDimension
from clinical_mdr_api.services.study_interventions import StudyInterventionsService

COMPOUNDS = [
    StudySelectionCompound(
        studyUid="Study_000002",
        order=1,
        projectNumber="CDISC DEV",
        projectName="CDISC Dev",
        studyCompoundUid="StudyCompound_000001",
        compound=Compound(
            uid="Compound_000001",
            name="Metformin",
            nameSentenceCase="Metformin",
            definition="compound_definition",
            abbreviation="abbv",
            libraryName="Sponsor",
            startDate=datetime.datetime(2022, 7, 14, 11, 20, 57, 559993),
            endDate=None,
            status="Final",
            version="1.0",
            changeDescription="Approved version",
            userInitials="unknown-user",
            possibleActions=["inactivate", "newVersion"],
            analyteNumber=None,
            nncShortNumber=None,
            nncLongNumber=None,
            isSponsorCompound=True,
            isNameInn=True,
            substances=[
                CompoundSubstance(
                    substanceTermUid="DictionaryTerm_000918",
                    substanceName="METFORMIN",
                    substanceUnii="9100L32L2N",
                    pclassTermUid="DictionaryTerm_000057",
                    pclassName="ORAL HYPOGLYCEMIC AGENTS",
                    pclassId="N0000029185",
                )
            ],
            doseValues=[
                SimpleNumericValueWithUnit(
                    uid="NumericValueWithUnit_000001",
                    value=0.25,
                    unitDefinitionUid="UnitDefinition_000225",
                    unitLabel="mg",
                ),
                SimpleNumericValueWithUnit(
                    uid="NumericValueWithUnit_000002",
                    value=0.5,
                    unitDefinitionUid="UnitDefinition_000225",
                    unitLabel="mg",
                ),
                SimpleNumericValueWithUnit(
                    uid="NumericValueWithUnit_000003",
                    value=0.75,
                    unitDefinitionUid="UnitDefinition_000225",
                    unitLabel="mg",
                ),
            ],
            strengthValues=[
                SimpleNumericValueWithUnit(
                    uid="NumericValueWithUnit_000004",
                    value=10.0,
                    unitDefinitionUid="UnitDefinition_000135",
                    unitLabel="U/Kg",
                ),
                SimpleNumericValueWithUnit(
                    uid="NumericValueWithUnit_000005",
                    value=20.0,
                    unitDefinitionUid="UnitDefinition_000135",
                    unitLabel="U/Kg",
                ),
                SimpleNumericValueWithUnit(
                    uid="NumericValueWithUnit_000006",
                    value=50.0,
                    unitDefinitionUid="UnitDefinition_000135",
                    unitLabel="U/Kg",
                ),
            ],
            lagTimes=[
                SimpleLagTime(
                    value=7.0,
                    unitDefinitionUid="UnitDefinition_000151",
                    unitLabel="days",
                    sdtmDomainUid="C49562_AE",
                    sdtmDomainLabel="Adverse Event Domain",
                )
            ],
            deliveryDevices=[
                SimpleTermModel(termUid="CTTerm_000128", name="Insulin pump"),
                SimpleTermModel(termUid="CTTerm_000127", name="Pre-filled pen"),
                SimpleTermModel(termUid="CTTerm_000126", name="Syringe"),
            ],
            dispensers=[
                SimpleTermModel(termUid="CTTerm_000125", name="Blister"),
                SimpleTermModel(termUid="CTTerm_000123", name="Cartridge"),
            ],
            projects=[],
            brands=[],
            halfLife=SimpleNumericValueWithUnit(
                uid="NumericValueWithUnit_000007",
                value=12.0,
                unitDefinitionUid="UnitDefinition_000153",
                unitLabel="hours",
            ),
            doseFrequencies=[],
            dosageForms=[],
            routesOfAdministration=[],
        ),
        compoundAlias=CompoundAlias(
            uid="CompoundAlias_000002",
            name="Improved Metformin",
            nameSentenceCase="improved metformin",
            definition="A better drug based on Metformin",
            abbreviation=None,
            libraryName="Sponsor",
            startDate=datetime.datetime(2022, 9, 20, 7, 41, 58, 147845),
            endDate=None,
            status="Final",
            version="1.0",
            changeDescription="Approved version",
            userInitials="unknown-user",
            possibleActions=["inactivate", "newVersion"],
            compound=SimpleCompound(uid="Compound_000001", name="Metformin"),
            isPreferredSynonym=False,
        ),
        typeOfTreatment=SimpleTermModel(
            termUid="CTTerm_000120", name="Investigational Product"
        ),
        routeOfAdministration=None,
        strengthValue=SimpleNumericValueWithUnit(
            uid="NumericValueWithUnit_000004",
            value=10.0,
            unitDefinitionUid="UnitDefinition_000135",
            unitLabel="U/Kg",
        ),
        dosageForm=None,
        dispensedIn=SimpleTermModel(termUid="CTTerm_000123", name="Cartridge"),
        device=SimpleTermModel(termUid="CTTerm_000126", name="Syringe"),
        formulation=None,
        otherInfo=None,
        reasonForMissingNullValue=None,
        studyCompoundDosingCount=0,
        startDate=datetime.datetime(2022, 9, 20, 7, 42, 42, 384826),
        userInitials="unknown-user",
        endDate=None,
        status=None,
        changeType=None,
    ),
    StudySelectionCompound(
        studyUid="Study_000002",
        order=2,
        projectNumber="CDISC DEV",
        projectName="CDISC Dev",
        studyCompoundUid="StudyCompound_000003",
        compound=Compound(
            uid="Compound_000001",
            name="Metformin",
            nameSentenceCase="Metformin",
            definition="compound_definition",
            abbreviation="abbv",
            libraryName="Sponsor",
            startDate=datetime.datetime(2022, 7, 14, 11, 20, 57, 559993),
            endDate=None,
            status="Final",
            version="1.0",
            changeDescription="Approved version",
            userInitials="unknown-user",
            possibleActions=["inactivate", "newVersion"],
            analyteNumber=None,
            nncShortNumber=None,
            nncLongNumber=None,
            isSponsorCompound=True,
            isNameInn=True,
            substances=[
                CompoundSubstance(
                    substanceTermUid="DictionaryTerm_000918",
                    substanceName="METFORMIN",
                    substanceUnii="9100L32L2N",
                    pclassTermUid="DictionaryTerm_000057",
                    pclassName="ORAL HYPOGLYCEMIC AGENTS",
                    pclassId="N0000029185",
                )
            ],
            doseValues=[
                SimpleNumericValueWithUnit(
                    uid="NumericValueWithUnit_000001",
                    value=0.25,
                    unitDefinitionUid="UnitDefinition_000225",
                    unitLabel="mg",
                ),
                SimpleNumericValueWithUnit(
                    uid="NumericValueWithUnit_000002",
                    value=0.5,
                    unitDefinitionUid="UnitDefinition_000225",
                    unitLabel="mg",
                ),
                SimpleNumericValueWithUnit(
                    uid="NumericValueWithUnit_000003",
                    value=0.75,
                    unitDefinitionUid="UnitDefinition_000225",
                    unitLabel="mg",
                ),
            ],
            strengthValues=[
                SimpleNumericValueWithUnit(
                    uid="NumericValueWithUnit_000004",
                    value=10.0,
                    unitDefinitionUid="UnitDefinition_000135",
                    unitLabel="U/Kg",
                ),
                SimpleNumericValueWithUnit(
                    uid="NumericValueWithUnit_000005",
                    value=20.0,
                    unitDefinitionUid="UnitDefinition_000135",
                    unitLabel="U/Kg",
                ),
                SimpleNumericValueWithUnit(
                    uid="NumericValueWithUnit_000006",
                    value=50.0,
                    unitDefinitionUid="UnitDefinition_000135",
                    unitLabel="U/Kg",
                ),
            ],
            lagTimes=[
                SimpleLagTime(
                    value=7.0,
                    unitDefinitionUid="UnitDefinition_000151",
                    unitLabel="days",
                    sdtmDomainUid="C49562_AE",
                    sdtmDomainLabel="Adverse Event Domain",
                )
            ],
            deliveryDevices=[
                SimpleTermModel(termUid="CTTerm_000128", name="Insulin pump"),
                SimpleTermModel(termUid="CTTerm_000127", name="Pre-filled pen"),
                SimpleTermModel(termUid="CTTerm_000126", name="Syringe"),
            ],
            dispensers=[
                SimpleTermModel(termUid="CTTerm_000125", name="Blister"),
                SimpleTermModel(termUid="CTTerm_000123", name="Cartridge"),
            ],
            projects=[],
            brands=[],
            halfLife=SimpleNumericValueWithUnit(
                uid="NumericValueWithUnit_000007",
                value=12.0,
                unitDefinitionUid="UnitDefinition_000153",
                unitLabel="hours",
            ),
            doseFrequencies=[],
            dosageForms=[],
            routesOfAdministration=[],
        ),
        compoundAlias=CompoundAlias(
            uid="CompoundAlias_000001",
            name="Generic Metformin",
            nameSentenceCase="generic metformin",
            definition="Some typical generic Metformin",
            abbreviation=None,
            libraryName="Sponsor",
            startDate=datetime.datetime(2022, 9, 20, 7, 41, 57, 754160),
            endDate=None,
            status="Final",
            version="1.0",
            changeDescription="Approved version",
            userInitials="unknown-user",
            possibleActions=["inactivate", "newVersion"],
            compound=SimpleCompound(uid="Compound_000001", name="Metformin"),
            isPreferredSynonym=False,
        ),
        typeOfTreatment=SimpleTermModel(
            termUid="CTTerm_000121", name="Comparative Treatment"
        ),
        routeOfAdministration=None,
        strengthValue=SimpleNumericValueWithUnit(
            uid="NumericValueWithUnit_000004",
            value=10.0,
            unitDefinitionUid="UnitDefinition_000135",
            unitLabel="U/Kg",
        ),
        dosageForm=None,
        dispensedIn=SimpleTermModel(termUid="CTTerm_000123", name="Cartridge"),
        device=SimpleTermModel(termUid="CTTerm_000126", name="Syringe"),
        formulation=None,
        otherInfo=None,
        reasonForMissingNullValue=None,
        studyCompoundDosingCount=0,
        startDate=datetime.datetime(2022, 9, 20, 7, 42, 46, 144398),
        userInitials="unknown-user",
        endDate=None,
        status=None,
        changeType=None,
    ),
]

TABLE = Table(
    data=TableDimension(
        [
            (0, TableDimension([(0, "Intervention/Arm name"), (1, "?"), (2, "?")])),
            (
                1,
                TableDimension(
                    [(0, "Intervention name"), (1, "Metformin"), (2, "Metformin")]
                ),
            ),
            (
                2,
                TableDimension(
                    [
                        (0, "Intervention type"),
                        (1, "Investigational Product"),
                        (2, "Comparative Treatment"),
                    ]
                ),
            ),
            (
                3,
                TableDimension(
                    [(0, "Investigational or non-investigational"), (1, "?"), (2, "?")]
                ),
            ),
            (4, TableDimension([(0, "Pharmaceutical form"), (1, ""), (2, "")])),
            (5, TableDimension([(0, "Route of administration"), (1, ""), (2, "")])),
            (
                6,
                TableDimension(
                    [
                        (0, "Medical-device (if applicable)"),
                        (1, "Administered using Syringe with a Cartridge"),
                        (2, "Administered using Syringe with a Cartridge"),
                    ]
                ),
            ),
            (
                7,
                TableDimension(
                    [(0, "Trial product strength"), (1, "10.0 U/Kg"), (2, "10.0 U/Kg")]
                ),
            ),
            (8, TableDimension([(0, "Dose and dose frequency"), (1, "?"), (2, "?")])),
            (
                9,
                TableDimension(
                    [(0, "Dosing instructions and administration"), (1, "?"), (2, "?")]
                ),
            ),
            (
                10,
                TableDimension(
                    [(0, "Transfer from other therapy"), (1, "?"), (2, "?")]
                ),
            ),
            (11, TableDimension([(0, "Sourcing"), (1, "?"), (2, "?")])),
            (12, TableDimension([(0, "Packaging and labelling"), (1, "?"), (2, "?")])),
            (13, TableDimension([(0, "Authorisation status in"), (1, "?"), (2, "?")])),
        ]
    ),
    meta=TableDimension(
        [
            (
                0,
                TableDimension(
                    [
                        (0, {"class": "header1"}),
                        (1, {"class": "header2"}),
                        (2, {"class": "header2"}),
                    ]
                ),
            ),
            (1, TableDimension([(0, {"class": "header2"})])),
            (2, TableDimension([(0, {"class": "header2"})])),
            (3, TableDimension([(0, {"class": "header2"})])),
            (4, TableDimension([(0, {"class": "header2"})])),
            (5, TableDimension([(0, {"class": "header2"})])),
            (6, TableDimension([(0, {"class": "header2"})])),
            (7, TableDimension([(0, {"class": "header2"})])),
            (8, TableDimension([(0, {"class": "header2"})])),
            (9, TableDimension([(0, {"class": "header2"})])),
            (10, TableDimension([(0, {"class": "header2"})])),
            (11, TableDimension([(0, {"class": "header2"})])),
            (12, TableDimension([(0, {"class": "header2"})])),
            (13, TableDimension([(0, {"class": "header2"})])),
        ]
    ),
    num_header_rows=1,
    num_header_columns=1,
)


def test_mk_table():
    table = StudyInterventionsService().mk_table(COMPOUNDS)

    assert table.data.size == 14
    assert table.data[0].size == 3

    assert table.num_header_rows == 1
    assert table.num_header_columns == 1
