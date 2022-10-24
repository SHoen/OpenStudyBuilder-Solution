# pylint:disable=broad-except
import logging
from random import randint
from typing import List, Optional, Sequence

from neomodel import db

from clinical_mdr_api import models
from clinical_mdr_api.models.compound import Compound, CompoundCreateInput
from clinical_mdr_api.models.compound_alias import (
    CompoundAlias,
    CompoundAliasCreateInput,
)
from clinical_mdr_api.models.concept import TextValue, TextValueInput
from clinical_mdr_api.models.criteria import CriteriaCreateInput
from clinical_mdr_api.models.criteria_template import (
    CriteriaTemplate,
    CriteriaTemplateCreateInput,
)
from clinical_mdr_api.models.endpoint import EndpointCreateInput
from clinical_mdr_api.models.endpoint_template import (
    EndpointTemplate,
    EndpointTemplateCreateInput,
)
from clinical_mdr_api.models.objective import ObjectiveCreateInput
from clinical_mdr_api.models.objective_template import (
    ObjectiveTemplate,
    ObjectiveTemplateCreateInput,
)
from clinical_mdr_api.models.study import Study, StudyCreateInput
from clinical_mdr_api.models.study_selection import (
    EndpointUnits,
    StudyCompoundDosing,
    StudyCompoundDosingInput,
    StudySelectionCompound,
    StudySelectionCompoundInput,
    StudySelectionCriteria,
    StudySelectionCriteriaCreateInput,
    StudySelectionElement,
    StudySelectionElementCreateInput,
    StudySelectionEndpoint,
    StudySelectionEndpointCreateInput,
    StudySelectionObjective,
    StudySelectionObjectiveCreateInput,
)
from clinical_mdr_api.models.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.template_parameter_value import MultiTemplateParameterValue
from clinical_mdr_api.models.timeframe import Timeframe, TimeframeCreateInput
from clinical_mdr_api.models.timeframe_template import (
    TimeframeTemplate,
    TimeframeTemplateCreateInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.services import libraries as library_service
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.brand import BrandService
from clinical_mdr_api.services.clinical_programme import (
    create as create_clinical_programme,
)
from clinical_mdr_api.services.concepts.compound_alias_service import (
    CompoundAliasService,
)
from clinical_mdr_api.services.concepts.compound_service import CompoundService
from clinical_mdr_api.services.concepts.simple_concepts.lag_time import LagTimeService
from clinical_mdr_api.services.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitService,
)
from clinical_mdr_api.services.concepts.simple_concepts.text_value import (
    TextValueService,
)
from clinical_mdr_api.services.criteria_templates import CriteriaTemplateService
from clinical_mdr_api.services.ct_codelist import CTCodelistService
from clinical_mdr_api.services.ct_term import CTTermService
from clinical_mdr_api.services.ct_term_attributes import CTTermAttributesService
from clinical_mdr_api.services.ct_term_name import CTTermNameService
from clinical_mdr_api.services.endpoint_templates import EndpointTemplateService
from clinical_mdr_api.services.objective_templates import ObjectiveTemplateService
from clinical_mdr_api.services.project import ProjectService
from clinical_mdr_api.services.study import StudyService
from clinical_mdr_api.services.study_compound_dosing_selection import (
    StudyCompoundDosingSelectionService,
)
from clinical_mdr_api.services.study_compound_selection import (
    StudyCompoundSelectionService,
)
from clinical_mdr_api.services.study_criteria_selection import (
    StudyCriteriaSelectionService,
)
from clinical_mdr_api.services.study_element_selection import (
    StudyElementSelectionService,
)
from clinical_mdr_api.services.study_endpoint_selection import (
    StudyEndpointSelectionService,
)
from clinical_mdr_api.services.study_objective_selection import (
    StudyObjectiveSelectionService,
)
from clinical_mdr_api.services.timeframe_templates import TimeframeTemplateService
from clinical_mdr_api.services.timeframes import TimeframeService
from clinical_mdr_api.services.unit_definition import UnitDefinitionService

log = logging.getLogger(__name__)

AUTHOR = "test"
STUDY_UID = "study_root"
PROJECT_NUMBER = "123"
LIBRARY_NAME = "Sponsor"
CT_CATALOGUE_NAME = "SDTM CT"
CT_CODELIST_NAME = "CT Codelist"
CT_CODELIST_UID = "C66737"
CT_CODELIST_LIBRARY = "CDISC"


class TestUtils:
    """Class containg methods that create all kinds of entities, e.g. library compounds"""

    @classmethod
    def random_str(cls, max_length: int, prefix: str = ""):
        return prefix + str(randint(1, 10**max_length - 1))

    @classmethod
    def random_if_none(cls, val, max_length: int = 10, prefix: str = ""):
        """Return supplied `val` if its value is not None.
        Otherwise return random string with optional prefix."""
        return val if val else cls.random_str(max_length, prefix)

    # region Syntax templates
    @classmethod
    def create_template_parameter(cls, name: str) -> None:
        db.cypher_query(f"CREATE (:TemplateParameter {{name:'{name}'}})")

    @classmethod
    def create_text_value(
        cls,
        libraryName: Optional[str] = LIBRARY_NAME,
        name: Optional[str] = None,
        nameSentenceCase: Optional[str] = None,
        definition: Optional[str] = None,
        abbreviation: Optional[str] = None,
        templateParameter: Optional[bool] = True,
    ) -> TextValue:
        service = TextValueService()
        payload: TextValueInput = TextValueInput(
            name=cls.random_if_none(name, prefix="name-"),
            nameSentenceCase=cls.random_if_none(
                nameSentenceCase, prefix="nameSentenceCase-"
            ),
            definition=cls.random_if_none(definition, prefix="def-"),
            abbreviation=cls.random_if_none(abbreviation, prefix="abbr-"),
            libraryName=libraryName,
            templateParameter=templateParameter,
        )

        result: TextValue = service.create(payload)
        return result

    @classmethod
    def create_objective_template(
        cls,
        name: Optional[str] = None,
        guidanceText: Optional[str] = None,
        studyUid: Optional[str] = None,
        libraryName: Optional[str] = LIBRARY_NAME,
        defaultParameterValues: Optional[MultiTemplateParameterValue] = None,
        editableInstance: Optional[bool] = False,
        indicationUids: Optional[List[str]] = None,
        confirmatoryTesting: Optional[bool] = False,
        categoryUids: Optional[List[str]] = None,
        approve: bool = True,
    ) -> ObjectiveTemplate:
        service = ObjectiveTemplateService()
        payload: ObjectiveTemplateCreateInput = ObjectiveTemplateCreateInput(
            name=cls.random_if_none(name, prefix="ot-"),
            guidanceText=guidanceText,
            studyUid=studyUid,
            libraryName=libraryName,
            defaultParameterValues=defaultParameterValues,
            editableInstance=editableInstance,
            indicationUids=indicationUids,
            confirmatoryTesting=confirmatoryTesting,
            categoryUids=categoryUids,
        )

        result: ObjectiveTemplate = service.create(payload)
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_endpoint_template(
        cls,
        name: Optional[str] = None,
        guidanceText: Optional[str] = None,
        studyUid: Optional[str] = None,
        libraryName: Optional[str] = LIBRARY_NAME,
        defaultParameterValues: Optional[MultiTemplateParameterValue] = None,
        editableInstance: Optional[bool] = False,
        indicationUids: Optional[List[str]] = None,
        confirmatoryTesting: Optional[bool] = False,
        categoryUids: Optional[List[str]] = None,
        subCategoryUids: Optional[List[str]] = None,
        approve: bool = True,
    ) -> EndpointTemplate:
        service = EndpointTemplateService()
        payload: EndpointTemplateCreateInput = EndpointTemplateCreateInput(
            name=cls.random_if_none(name, prefix="et-"),
            guidanceText=guidanceText,
            studyUid=studyUid,
            libraryName=libraryName,
            defaultParameterValues=defaultParameterValues,
            editableInstance=editableInstance,
            indicationUids=indicationUids,
            confirmatoryTesting=confirmatoryTesting,
            categoryUids=categoryUids,
            subCategoryUids=subCategoryUids,
        )

        result: ObjectiveTemplate = service.create(payload)
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_criteria_template(
        cls,
        name: Optional[str] = None,
        guidanceText: Optional[str] = None,
        studyUid: Optional[str] = None,
        libraryName: Optional[str] = LIBRARY_NAME,
        defaultParameterValues: Optional[MultiTemplateParameterValue] = None,
        editableInstance: Optional[bool] = False,
        typeUid: Optional[str] = None,
        indicationUids: Optional[List[str]] = None,
        categoryUids: Optional[List[str]] = None,
        subCategoryUids: Optional[List[str]] = None,
        approve: bool = True,
    ) -> CriteriaTemplate:
        service = CriteriaTemplateService()
        payload: CriteriaTemplateCreateInput = CriteriaTemplateCreateInput(
            name=cls.random_if_none(name, prefix="ct-"),
            guidanceText=cls.random_if_none(guidanceText),
            studyUid=studyUid,
            libraryName=libraryName,
            defaultParameterValues=defaultParameterValues,
            editableInstance=editableInstance,
            typeUid=typeUid,
            indicationUids=indicationUids,
            categoryUids=categoryUids,
            subCategoryUids=subCategoryUids,
        )

        result: CriteriaTemplate = service.create(payload)
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_timeframe_template(
        cls,
        name: Optional[str] = None,
        guidanceText: Optional[str] = None,
        libraryName: Optional[str] = LIBRARY_NAME,
        editableInstance: Optional[bool] = False,
        approve: bool = True,
    ) -> TimeframeTemplate:
        service = TimeframeTemplateService()
        payload: TimeframeTemplateCreateInput = TimeframeTemplateCreateInput(
            name=cls.random_if_none(name, prefix="tt-"),
            guidanceText=guidanceText,
            libraryName=libraryName,
            editableInstance=editableInstance,
        )

        result: TimeframeTemplate = service.create(payload)
        if approve:
            service.approve(result.uid)
        return result

    # endregion

    @classmethod
    def create_compound(
        cls,
        name=None,
        nameSentenceCase=None,
        definition=None,
        abbreviation=None,
        libraryName=LIBRARY_NAME,
        analyteNumber=None,
        nncLongNumber=None,
        nncShortNumber=None,
        isSponsorCompound=True,
        isNameInn=False,
        substanceTermsUids=None,
        doseValuesUids=None,
        lagTimesUids=None,
        strengthValuesUids=None,
        deliveryDevicesUids=None,
        dispensersUids=None,
        projectsUids=None,
        brandsUids=None,
        doseFrequencyUids=None,
        dosageFormUids=None,
        routeOfAdministrationUids=None,
        halfLifeUid=None,
    ) -> Compound:
        service = CompoundService()
        payload: CompoundCreateInput = CompoundCreateInput(
            name=cls.random_if_none(name, prefix="name-"),
            nameSentenceCase=cls.random_if_none(
                nameSentenceCase, prefix="nameSentenceCase-"
            ),
            definition=cls.random_if_none(definition, prefix="definition-"),
            abbreviation=cls.random_if_none(abbreviation, prefix="abbreviation-"),
            libraryName=libraryName,
            analyteNumber=cls.random_if_none(analyteNumber, prefix="analyteNumber-"),
            nncLongNumber=cls.random_if_none(nncLongNumber, prefix="nncLongNumber-"),
            nncShortNumber=cls.random_if_none(nncShortNumber, prefix="nncShortNumber-"),
            isSponsorCompound=isSponsorCompound if isSponsorCompound else True,
            isNameInn=isNameInn if isNameInn else False,
            substanceTermsUids=substanceTermsUids if substanceTermsUids else [],
            doseValuesUids=doseValuesUids if doseValuesUids else [],
            lagTimesUids=lagTimesUids if lagTimesUids else [],
            strengthValuesUids=strengthValuesUids if strengthValuesUids else [],
            deliveryDevicesUids=deliveryDevicesUids if deliveryDevicesUids else [],
            dispensersUids=dispensersUids if dispensersUids else [],
            projectsUids=projectsUids if projectsUids else [],
            brandsUids=brandsUids if brandsUids else [],
            doseFrequencyUids=doseFrequencyUids if doseFrequencyUids else [],
            dosageFormUids=dosageFormUids if dosageFormUids else [],
            routeOfAdministrationUids=routeOfAdministrationUids
            if routeOfAdministrationUids
            else [],
            halfLifeUid=halfLifeUid if halfLifeUid else None,
        )

        result: Compound = service.create(payload)
        return result

    @classmethod
    def create_compound_alias(
        cls,
        name=None,
        nameSentenceCase=None,
        definition=None,
        abbreviation=None,
        libraryName=LIBRARY_NAME,
        isPreferredSynonym=None,
        compoundUid=None,
    ) -> CompoundAlias:
        service = CompoundAliasService()
        payload: CompoundAliasCreateInput = CompoundAliasCreateInput(
            name=cls.random_if_none(name, prefix="name-"),
            nameSentenceCase=cls.random_if_none(
                nameSentenceCase, prefix="nameSentenceCase-"
            ),
            definition=cls.random_if_none(definition, prefix="definition-"),
            abbreviation=cls.random_if_none(abbreviation, prefix="abbreviation-"),
            libraryName=libraryName,
            isPreferredSynonym=isPreferredSynonym if isPreferredSynonym else False,
            compoundUid=compoundUid if compoundUid else None,
        )

        result: CompoundAlias = service.create(payload)
        return result

    # region Study selection
    @classmethod
    def _complete_parameter_values(
        cls, parameterValues: List[TemplateParameterMultiSelectInput]
    ):
        for value in parameterValues:
            if value.conjunction is None:
                value.conjunction = ""
        return parameterValues

    @classmethod
    def create_study_objective(
        cls,
        study_uid: str,
        objectiveTemplateUid: str,
        libraryName: Optional[str] = LIBRARY_NAME,
        nameOverride: Optional[str] = None,
        objectiveLevelUid: Optional[str] = None,
        parameterValues: Optional[List[TemplateParameterMultiSelectInput]] = None,
    ) -> StudySelectionObjective:
        service = StudyObjectiveSelectionService(AUTHOR)
        objective_create_input: StudySelectionObjectiveCreateInput = (
            StudySelectionObjectiveCreateInput(
                objectiveLevelUid=objectiveLevelUid,
                objectiveData=ObjectiveCreateInput(
                    objectiveTemplateUid=objectiveTemplateUid,
                    libraryName=libraryName,
                    nameOverride=nameOverride,
                    parameterValues=cls._complete_parameter_values(parameterValues),
                ),
            )
        )

        result: StudySelectionObjective = service.make_selection_create_objective(
            study_uid=study_uid, selection_create_input=objective_create_input
        )
        return result

    @classmethod
    def create_study_endpoint(
        cls,
        study_uid: str,
        endpointTemplateUid: str,
        libraryName: Optional[str] = LIBRARY_NAME,
        studyObjectiveUid: Optional[str] = None,
        endpointLevelUid: Optional[str] = None,
        endpointSubLevelUid: Optional[str] = None,
        nameOverride: Optional[str] = None,
        parameterValues: Optional[List[TemplateParameterMultiSelectInput]] = None,
        endpointUnits: Optional[EndpointUnits] = None,
        timeframeUid: Optional[str] = None,
    ) -> StudySelectionEndpoint:
        service = StudyEndpointSelectionService(AUTHOR)
        if parameterValues is None:
            parameterValues = []
        endpoint_create_input: StudySelectionEndpointCreateInput = (
            StudySelectionEndpointCreateInput(
                studyObjectiveUid=studyObjectiveUid,
                endpointLevelUid=endpointLevelUid,
                endpointSubLevelUid=endpointSubLevelUid,
                endpointData=EndpointCreateInput(
                    endpointTemplateUid=endpointTemplateUid,
                    libraryName=libraryName,
                    nameOverride=nameOverride,
                    parameterValues=cls._complete_parameter_values(parameterValues),
                ),
                endpointUnits=endpointUnits,
                timeframeUid=timeframeUid,
            )
        )

        result: StudySelectionEndpoint = service.make_selection_create_endpoint(
            study_uid=study_uid, selection_create_input=endpoint_create_input
        )
        return result

    @classmethod
    def create_study_criteria(
        cls,
        study_uid: str,
        criteriaTemplateUid: str,
        libraryName: Optional[str] = LIBRARY_NAME,
        nameOverride: Optional[str] = None,
        parameterValues: Optional[List[TemplateParameterMultiSelectInput]] = None,
    ) -> StudySelectionCriteria:
        service = StudyCriteriaSelectionService(AUTHOR)
        if parameterValues is None:
            parameterValues = []
        criteria_create_input: StudySelectionCriteriaCreateInput = (
            StudySelectionCriteriaCreateInput(
                criteriaData=CriteriaCreateInput(
                    criteriaTemplateUid=criteriaTemplateUid,
                    libraryName=libraryName,
                    nameOverride=nameOverride,
                    parameterValues=cls._complete_parameter_values(parameterValues),
                )
            )
        )

        result: StudySelectionCriteria = service.make_selection_create_criteria(
            study_uid=study_uid, selection_create_input=criteria_create_input
        )
        return result

    @classmethod
    def create_timeframe(
        cls,
        timeframeTemplateUid: str,
        libraryName: Optional[str] = LIBRARY_NAME,
        nameOverride: Optional[str] = None,
        parameterValues: Optional[List[TemplateParameterMultiSelectInput]] = None,
    ) -> Timeframe:
        service = TimeframeService(AUTHOR)
        if parameterValues is None:
            parameterValues = []
        timeframe_create_input: TimeframeCreateInput = TimeframeCreateInput(
            timeframeTemplateUid=timeframeTemplateUid,
            libraryName=libraryName,
            nameOverride=nameOverride,
            parameterValues=cls._complete_parameter_values(parameterValues),
        )

        result: Timeframe = service.create(timeframe_create_input)
        return result

    @classmethod
    def create_study_compound(
        cls,
        compoundAliasUid=None,
        typeOfTreatmentUid=None,
        otherInfo=None,
        reasonForMissingNullValueUid=None,
        deviceUid=None,
        dispensedInUid=None,
        dosageFormUid=None,
        routeOfAdministrationUid=None,
        strengthValueUid=None,
    ) -> StudySelectionCompound:
        service = StudyCompoundSelectionService(AUTHOR)
        payload: StudySelectionCompoundInput = StudySelectionCompoundInput(
            compoundAliasUid=compoundAliasUid,
            typeOfTreatmentUid=typeOfTreatmentUid,
            otherInfo=cls.random_if_none(otherInfo, prefix="otherInfo-"),
            reasonForMissingNullValueUid=reasonForMissingNullValueUid,
            deviceUid=deviceUid if deviceUid else None,
            dispensedInUid=dispensedInUid if dispensedInUid else None,
            dosageFormUid=dosageFormUid if dosageFormUid else None,
            routeOfAdministrationUid=routeOfAdministrationUid
            if routeOfAdministrationUid
            else None,
            strengthValueUid=strengthValueUid if strengthValueUid else None,
        )

        result: StudySelectionCompound = service.make_selection(
            study_uid=STUDY_UID, selection_create_input=payload
        )
        return result

    @classmethod
    def create_study_compound_dosing(
        cls,
        studyCompoundUid=None,
        studyElementUid=None,
        doseValueUid=None,
        doseFrequencyUid=None,
    ) -> StudyCompoundDosing:
        service = StudyCompoundDosingSelectionService(AUTHOR)
        payload: StudyCompoundDosingInput = StudyCompoundDosingInput(
            studyCompoundUid=studyCompoundUid,
            studyElementUid=studyElementUid,
            doseValueUid=doseValueUid,
            doseFrequencyUid=doseFrequencyUid,
        )

        result: StudyCompoundDosing = service.make_selection(
            study_uid=STUDY_UID, selection_create_input=payload
        )
        return result

    @classmethod
    def create_study_element(
        cls,
        name=None,
        shortName=None,
        code=None,
        description=None,
        plannedDuration=None,
        startRule=None,
        endRule=None,
        elementColour=None,
        elementSubTypeUid=None,
    ) -> StudySelectionElement:
        service = StudyElementSelectionService(AUTHOR)
        payload: StudySelectionElementCreateInput = StudySelectionElementCreateInput(
            name=name,
            shortName=shortName,
            code=code,
            description=description,
            plannedDuration=plannedDuration,
            startRule=startRule,
            endRule=endRule,
            elementColour=elementColour,
            elementSubTypeUid=elementSubTypeUid,
        )

        result: StudySelectionElement = service.make_selection(
            study_uid=STUDY_UID, selection_create_input=payload
        )
        return result

    # endregion

    @classmethod
    def create_unit_definition(
        cls,
        name=None,
        libraryName=LIBRARY_NAME,
        convertibleUnit=False,
        displayUnit=True,
        masterUnit=False,
        siUnit=False,
        usConventionalUnit=False,
        ctUnits=None,
        unitSubsets=None,
        ucum=None,
        unitDimension=None,
        legacyCode=None,
        molecularWeightConvExpon=0,
        conversionFactorToMaster=0.001,
        comment=None,
        order=None,
        definition=None,
        templateParameter=False,
        approve: bool = True,
    ) -> models.UnitDefinitionModel:
        user_id = AUTHOR
        service = UnitDefinitionService(
            user_id=user_id, meta_repository=MetaRepository(user_id)
        )

        payload: models.UnitDefinitionPostInput = models.UnitDefinitionPostInput(
            name=name,
            libraryName=libraryName,
            convertibleUnit=convertibleUnit,
            displayUnit=displayUnit,
            masterUnit=masterUnit,
            siUnit=siUnit,
            usConventionalUnit=usConventionalUnit,
            ctUnits=ctUnits if ctUnits else [],
            unitSubsets=unitSubsets if unitSubsets else [],
            ucum=ucum,
            unitDimension=unitDimension,
            legacyCode=legacyCode,
            molecularWeightConvExpon=molecularWeightConvExpon,
            conversionFactorToMaster=conversionFactorToMaster,
            comment=comment,
            order=order,
            definition=definition,
            templateParameter=templateParameter,
        )

        result: models.UnitDefinitionModel = service.post(post_input=payload)
        if approve:
            service.approve(result.uid)
        return result

    @classmethod
    def create_library(cls, name: str = LIBRARY_NAME, is_editable: bool = True) -> dict:
        return library_service.create(name, is_editable)

    @classmethod
    def create_project(
        cls,
        name="Project ABC",
        project_number=PROJECT_NUMBER,
        description="Base project",
        clinical_programme_uid=None,
    ) -> models.Project:
        service = ProjectService()
        payload = models.ProjectCreateInput(
            name=name,
            projectNumber=project_number,
            description=description,
            clinicalProgrammeUid=clinical_programme_uid,
        )
        return service.create(payload)

    @classmethod
    def create_clinical_programme(cls, name: str = "CP") -> models.ClinicalProgramme:
        return create_clinical_programme(models.ClinicalProgrammeInput(name=name))

    @classmethod
    def create_study(
        cls,
        number: Optional[str] = None,
        acronym: Optional[str] = None,
        project_number: Optional[str] = PROJECT_NUMBER,
    ) -> Study:
        service = StudyService()
        payload = StudyCreateInput(
            studyNumber=cls.random_if_none(number, max_length=4),
            studyAcronym=cls.random_if_none(acronym, prefix="st-"),
            projectNumber=project_number,
        )
        return service.create(payload)

    @classmethod
    def create_ct_term(
        cls,
        catalogueName: str = CT_CATALOGUE_NAME,
        codelistUid: str = CT_CODELIST_UID,
        codeSubmissionValue: str = None,
        nameSubmissionValue: str = None,
        nciPreferredName: str = None,
        definition: str = None,
        sponsorPreferredName: str = None,
        sponsorPreferredNameSentenceCase: str = None,
        order: int = None,
        library_name: str = CT_CODELIST_LIBRARY,
        approve: bool = True,
    ) -> models.CTTerm:
        service = CTTermService()
        payload = models.CTTermCreateInput(
            catalogueName=catalogueName,
            codelistUid=codelistUid,
            codeSubmissionValue=cls.random_if_none(
                codeSubmissionValue, prefix="codeSubmissionValue-"
            ),
            nameSubmissionValue=cls.random_if_none(
                nameSubmissionValue, prefix="nameSubmissionValue-"
            ),
            nciPreferredName=cls.random_if_none(nciPreferredName, prefix="nciName-"),
            definition=cls.random_if_none(definition, prefix="definition-"),
            sponsorPreferredName=cls.random_if_none(
                sponsorPreferredName, prefix="name-"
            ),
            sponsorPreferredNameSentenceCase=cls.random_if_none(
                sponsorPreferredNameSentenceCase,
                prefix="nameSentCase-",
            ),
            order=order,
            libraryName=library_name,
        )
        ct_term: models.CTTerm = service.create(payload)
        if approve:
            CTTermAttributesService().approve(term_uid=ct_term.termUid)
            CTTermNameService().approve(term_uid=ct_term.termUid)
        return ct_term

    @classmethod
    def create_ct_codelist(
        cls,
        catalogueName: str = CT_CATALOGUE_NAME,
        name: str = CT_CODELIST_NAME,
        submissionValue: str = None,
        nciPreferredName: str = None,
        sponsorPreferredName: str = None,
        definition: str = None,
        extensible: bool = False,
        templateParameter: bool = False,
        parentCodelistUid: str = None,
        terms: Sequence[models.CTCodelistTermInput] = None,
        library_name: str = LIBRARY_NAME,
    ) -> models.CTCodelist:
        if terms is None:
            terms = []

        service = CTCodelistService()
        payload = models.CTCodelistCreateInput(
            catalogueName=catalogueName,
            name=cls.random_if_none(name, prefix="name-"),
            submissionValue=cls.random_if_none(
                submissionValue, prefix="submissionValue-"
            ),
            nciPreferredName=cls.random_if_none(nciPreferredName, prefix="nciName-"),
            definition=cls.random_if_none(definition, prefix="definition-"),
            extensible=extensible,
            sponsorPreferredName=cls.random_if_none(
                sponsorPreferredName, prefix="name-"
            ),
            templateParameter=templateParameter,
            parentCodelistUid=parentCodelistUid,
            terms=terms,
            libraryName=library_name,
        )
        return service.create(payload)

    @classmethod
    def create_numeric_value_with_unit(
        cls,
        unit: str = None,
        name: str = None,
        nameSentenceCase: str = None,
        definition: str = None,
        abbreviation: str = None,
        libraryName: str = LIBRARY_NAME,
        templateParameter: bool = False,
        value: float = None,
        unitDefinitionUid: str = None,
    ) -> models.NumericValueWithUnit:

        # First make sure that the specified unit exists
        if unitDefinitionUid is None:
            try:
                unit_definition = cls.create_unit_definition(
                    name=unit,
                    libraryName=libraryName,
                    convertibleUnit=False,
                    displayUnit=True,
                    masterUnit=False,
                    siUnit=True,
                    usConventionalUnit=True,
                    ctUnits=[],
                    unitSubsets=[],
                    ucum=None,
                    unitDimension=None,
                    legacyCode=None,
                    molecularWeightConvExpon=0,
                    conversionFactorToMaster=0.001,
                    comment=unit,
                    order=0,
                    definition=unit,
                    templateParameter=True,
                    approve=True,
                )
                unitDefinitionUid = unit_definition.uid
            except Exception as _:
                log.info("Unit '%s' already exists", unit)
                unitDefinitionUid = cls.get_unit_uid_by_name(unit_name=unit)

        service = NumericValueWithUnitService()
        payload = models.NumericValueWithUnitInput(
            name=cls.random_if_none(name, prefix="name-"),
            nameSentenceCase=cls.random_if_none(
                nameSentenceCase, prefix="nameSentenceCase-"
            ),
            definition=cls.random_if_none(definition, prefix="definition-"),
            abbreviation=cls.random_if_none(abbreviation, prefix="abbreviation-"),
            libraryName=libraryName,
            templateParameter=templateParameter,
            value=value,
            unitDefinitionUid=unitDefinitionUid,
        )

        result: models.NumericValueWithUnit = service.create(payload)
        return result

    @classmethod
    def create_lag_time(
        cls,
        unit: str = None,
        sdtmDomainLabel: str = "Adverse Event Domain",
        name: str = None,
        nameSentenceCase: str = None,
        definition: str = None,
        abbreviation: str = None,
        libraryName: str = LIBRARY_NAME,
        templateParameter: bool = False,
        value: float = None,
        unitDefinitionUid: str = None,
        sdtmDomainUid: str = None,
    ) -> models.LagTime:

        # First make sure that the specified unit exists
        if unitDefinitionUid is None:
            try:
                unit_definition = cls.create_unit_definition(
                    name=unit,
                    libraryName=libraryName,
                    convertibleUnit=False,
                    displayUnit=True,
                    masterUnit=False,
                    siUnit=True,
                    usConventionalUnit=True,
                    ctUnits=[],
                    unitSubsets=[],
                    ucum=None,
                    unitDimension=None,
                    legacyCode=None,
                    molecularWeightConvExpon=0,
                    conversionFactorToMaster=0.001,
                    comment=unit,
                    order=0,
                    definition=unit,
                    templateParameter=True,
                    approve=True,
                )
                unitDefinitionUid = unit_definition.uid
            except Exception as _:
                log.info("Unit '%s' already exists", unit)
                unitDefinitionUid = cls.get_unit_uid_by_name(unit_name=unit)

        # Make sure that the specified SDTM domain exists
        if sdtmDomainUid is None:
            try:
                sdtm_domain: models.CTTerm = cls.create_ct_term(
                    sponsorPreferredName=sdtmDomainLabel, approve=True
                )
                sdtmDomainUid = sdtm_domain.termUid
            except Exception as _:
                log.info("SDTM domain '%s' already exists", sdtmDomainLabel)
                sdtmDomains: GenericFilteringReturn[
                    models.CTTermNameAndAttributes
                ] = cls.get_ct_terms_by_name(name=sdtmDomainLabel)
                sdtmDomainUid = sdtmDomains.items[0].termUid

        service = LagTimeService()
        payload = models.LagTimeInput(
            name=cls.random_if_none(name, prefix="name-"),
            nameSentenceCase=cls.random_if_none(
                nameSentenceCase, prefix="nameSentenceCase-"
            ),
            definition=cls.random_if_none(definition, prefix="definition-"),
            abbreviation=cls.random_if_none(abbreviation, prefix="abbreviation-"),
            libraryName=libraryName,
            templateParameter=templateParameter,
            value=value,
            unitDefinitionUid=unitDefinitionUid,
            sdtmDomainUid=sdtmDomainUid,
        )

        result: models.NumericValueWithUnit = service.create(payload)
        return result

    @classmethod
    def get_unit_uid_by_name(cls, unit_name) -> str:
        unit_uid = MetaRepository().unit_definition_repository.find_uid_by_name(
            unit_name
        )
        return unit_uid

    @classmethod
    def get_ct_terms_by_name(
        cls, name
    ) -> GenericFilteringReturn[models.CTTermNameAndAttributes]:
        return CTTermService().get_all_terms(
            codelist_name=None,
            codelist_uid=None,
            library=None,
            package=None,
            filter_by={"name.sponsorPreferredName": {"v": [name]}},
        )

    @classmethod
    def create_brand(
        cls,
        name: str = None,
    ) -> models.Brand:
        service = BrandService()
        return service.create(models.BrandCreateInput(name=name))
