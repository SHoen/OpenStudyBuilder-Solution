clinical_programme = {"name": "string"}

brands = {"name": "string"}

project = {
    "projectNumber": "string",
    "name": "string",
    "description": "string",
    "clinicalProgrammeUid": "string",
}

study = {
    "studyNumber": "string",
    "studyAcronym": "string",
    "projectNumber": "string",
}


study_patch = {
    "currentMetadata": {
        "identificationMetadata": {
            "studyNumber": "string",
            "studyAcronym": "string",
            "projectNumber": "string",
            "projectName": "string",
            "clinicalProgrammeName": "string",
            "studyId": "string",
            "registryIdentifiers": {
                "ctGovId": "string",
                "ctGovIdNullValueCode": {"termUid": "string", "name": "string"},
                "eudractId": "string",
                "eudractIdNullValueCode": {"termUid": "string", "name": "string"},
                "universalTrialNumberUTN": "string",
                "universalTrialNumberUTNNullValueCode": {
                    "termUid": "string",
                    "name": "string",
                },
                "japaneseTrialRegistryIdJAPIC": "string",
                "japaneseTrialRegistryIdJAPICNullValueCode": {
                    "termUid": "string",
                    "name": "string",
                },
                "investigationalNewDrugApplicationNumberIND": "string",
                "investigationalNewDrugApplicationNumberINDNullValueCode": {
                    "termUid": "string",
                    "name": "string",
                },
            },
        },
        "versionMetadata": {
            "studyStatus": "string",
            "lockedVersionNumber": 0,
            "versionTimestamp": "2022-06-10T13:15:22.182Z",
            "lockedVersionAuthor": "string",
            "lockedVersionInfo": "string",
        },
        "highLevelStudyDesign": {
            "studyTypeCode": {"termUid": "string", "name": "string"},
            "studyTypeNullValueCode": {"termUid": "string", "name": "string"},
            "trialTypesCodes": [{"termUid": "string", "name": "string"}],
            "trialTypesNullValueCode": {"termUid": "string", "name": "string"},
            "trialPhaseCode": {"termUid": "string", "name": "string"},
            "trialPhaseNullValueCode": {"termUid": "string", "name": "string"},
            "isExtensionTrial": True,
            "isExtensionTrialNullValueCode": {"termUid": "string", "name": "string"},
            "isAdaptiveDesign": True,
            "isAdaptiveDesignNullValueCode": {"termUid": "string", "name": "string"},
            "studyStopRules": "string",
            "studyStopRulesNullValueCode": {"termUid": "string", "name": "string"},
            "confirmedResponseMinimumDuration": {
                "durationValue": 0,
                "durationUnitCode": {"termUid": "string", "name": "string"},
            },
            "confirmedResponseMinimumDurationNullValueCode": {
                "termUid": "string",
                "name": "string",
            },
            "postAuthIndicator": True,
            "postAuthIndicatorNullValueCode": {"termUid": "string", "name": "string"},
        },
        "studyPopulation": {
            "therapeuticAreasCodes": [{"termUid": "string", "name": "string"}],
            "therapeuticAreasNullValueCode": {"termUid": "string", "name": "string"},
            "diseaseConditionsOrIndicationsCodes": [
                {"termUid": "string", "name": "string"}
            ],
            "diseaseConditionsOrIndicationsNullValueCode": {
                "termUid": "string",
                "name": "string",
            },
            "diagnosisGroupsCodes": [{"termUid": "string", "name": "string"}],
            "diagnosisGroupsNullValueCode": {"termUid": "string", "name": "string"},
            "sexOfParticipantsCode": {"termUid": "string", "name": "string"},
            "sexOfParticipantsNullValueCode": {"termUid": "string", "name": "string"},
            "rareDiseaseIndicator": True,
            "rareDiseaseIndicatorNullValueCode": {
                "termUid": "string",
                "name": "string",
            },
            "healthySubjectIndicator": True,
            "healthySubjectIndicatorNullValueCode": {
                "termUid": "string",
                "name": "string",
            },
            "plannedMinimumAgeOfSubjects": {
                "durationValue": 0,
                "durationUnitCode": {"termUid": "string", "name": "string"},
            },
            "plannedMinimumAgeOfSubjectsNullValueCode": {
                "termUid": "string",
                "name": "string",
            },
            "plannedMaximumAgeOfSubjects": {
                "durationValue": 0,
                "durationUnitCode": {"termUid": "string", "name": "string"},
            },
            "plannedMaximumAgeOfSubjectsNullValueCode": {
                "termUid": "string",
                "name": "string",
            },
            "stableDiseaseMinimumDuration": {
                "durationValue": 0,
                "durationUnitCode": {"termUid": "string", "name": "string"},
            },
            "stableDiseaseMinimumDurationNullValueCode": {
                "termUid": "string",
                "name": "string",
            },
            "pediatricStudyIndicator": True,
            "pediatricStudyIndicatorNullValueCode": {
                "termUid": "string",
                "name": "string",
            },
            "pediatricPostmarketStudyIndicator": True,
            "pediatricPostmarketStudyIndicatorNullValueCode": {
                "termUid": "string",
                "name": "string",
            },
            "pediatricInvestigationPlanIndicator": True,
            "pediatricInvestigationPlanIndicatorNullValueCode": {
                "termUid": "string",
                "name": "string",
            },
            "relapseCriteria": "string",
            "relapseCriteriaNullValueCode": {"termUid": "string", "name": "string"},
        },
        "studyIntervention": {
            "interventionTypeCode": {"termUid": "string", "name": "string"},
            "interventionTypeNullValueCode": {"termUid": "string", "name": "string"},
            "addOnToExistingTreatments": True,
            "addOnToExistingTreatmentsNullValueCode": {
                "termUid": "string",
                "name": "string",
            },
            "controlTypeCode": {"termUid": "string", "name": "string"},
            "controlTypeNullValueCode": {"termUid": "string", "name": "string"},
            "interventionModelCode": {"termUid": "string", "name": "string"},
            "interventionModelNullValueCode": {"termUid": "string", "name": "string"},
            "isTrialRandomised": True,
            "isTrialRandomisedNullValueCode": {"termUid": "string", "name": "string"},
            "stratificationFactor": "string",
            "stratificationFactorNullValueCode": {
                "termUid": "string",
                "name": "string",
            },
            "trialBlindingSchemaCode": {"termUid": "string", "name": "string"},
            "trialBlindingSchemaNullValueCode": {"termUid": "string", "name": "string"},
            "plannedStudyLength": {
                "durationValue": 0,
                "durationUnitCode": {"termUid": "string", "name": "string"},
            },
            "plannedStudyLengthNullValueCode": {"termUid": "string", "name": "string"},
            "drugStudyIndication": True,
            "drugStudyIndicationNullValueCode": {"termUid": "string", "name": "string"},
            "deviceStudyIndication": "string",
            "deviceStudyIndicationNullValueCode": {
                "termUid": "string",
                "name": "string",
            },
            "trialIntentTypesCodes": [{"termUid": "string", "name": "string"}],
            "trialIntentTypesNullValueCode": {"termUid": "string", "name": "string"},
        },
        "studyDescription": {"studyTitle": "string"},
    }
}

study_arm = {
    "name": "string",
    "shortName": "string",
    "code": "string",
    "description": "string",
    "randomizationGroup": "string",
    "numberOfSubjects": 0,
    "armTypeUid": "string",
}

study_element = {
    "name": "string",
    "shortName": "string",
    "code": "string",
    "description": "string",
    "plannedDuration": {
        "durationValue": 0,
        "durationUnitCode": {"termUid": "string", "name": "string"},
    },
    "startRule": "string",
    "endRule": "string",
    "elementColour": "string",
    "elementSubTypeUid": "string",
}

study_epoch = {
    "studyUid": "string",
    "startRule": "string",
    "endRule": "string",
    "epoch": "string",
    "epochSubType": "string",
    "durationUnit": "string",
    "order": 0,
    "description": "string",
    "duration": 0,
    "colorHash": "string",
}

study_visit = {
    "studyEpochUid": "string",
    "visitTypeUid": "string",
    "timeReferenceUid": "string",
    "timeValue": 0,
    "timeUnitUid": "string",
    "visitSubLabelCodelistUid": "string",
    "visitSubLabelReference": "string",
    "legacyVisitId": "string",
    "legacyVisitTypeAlias": "string",
    "legacyName": "string",
    "legacySubName": "string",
    "consecutiveVisitGroup": "string",
    "showVisit": True,
    "minVisitWindowValue": 0,
    "maxVisitWindowValue": 0,
    "visitWindowUnitUid": "string",
    "description": "string",
    "startRule": "string",
    "endRule": "string",
    "note": "string",
    "visitContactModeUid": "string",
    "visitClass": "string",
    "visitSubclass": "string",
    "isGlobalAnchorVisit": False,
}

study_design_cell = {
    "studyArmUid": "string",
    "studyEpochUid": "string",
    "studyElementUid": "string",
    "transitionRule": "string",
    "order": 0,
}

study_branch = {
    "name": "string",
    "shortName": "string",
    "code": "string",
    "description": "string",
    "colourCode": "string",
    "randomizationGroup": "string",
    "numberOfSubjects": 0,
    "armUid": "string",
}

study_activity = {
    "flowchartGroupUid": "string",
    "activityUid": "string",
    "activityInstanceUid": "string",
}

objective_template = {
    "name": "string",
    "guidanceText": "string",
    "libraryName": "Sponsor",
    "defaultParameterValues": [
        {
            "position": 0,
            "conjunction": "string",
            "values": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
        }
    ],
    "editableInstance": False,
    "indicationUids": ["string"],
    "confirmatoryTesting": True,
    "categoryUids": ["string"],
}

criteria_template = {
    "name": "string",
    "guidanceText": "string",
    "libraryName": "Sponsor",
    "defaultParameterValues": [
        {
            "position": 0,
            "conjunction": "string",
            "values": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
        }
    ],
    "editableInstance": False,
    "typeUid": "string",
    "indicationUids": ["string"],
    "categoryUids": ["string"],
    "subCategoryUids": ["string"],
}

timeframe_template = {
    "name": "string",
    "guidanceText": "string",
    "libraryName": "Sponsor",
    "editableInstance": False,
}

endpoint_template = {
    "name": "string",
    "guidanceText": "string",
    "libraryName": "Sponsor",
    "defaultParameterValues": [
        {
            "position": 0,
            "conjunction": "string",
            "values": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
        }
    ],
    "editableInstance": False,
    "indicationUids": ["string"],
    "categoryUids": ["string"],
    "subCategoryUids": ["string"],
}

activity_description_template = {
    "name": "string",
    "guidanceText": "string",
    "libraryName": "Sponsor",
    "defaultParameterValues": [
        {
            "position": 0,
            "conjunction": "string",
            "values": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
        }
    ],
    "editableInstance": False,
    "indicationUids": ["string"],
    "activityUids": ["string"],
    "activityGroupUids": ["string"],
    "activitySubGroupUids": ["string"],
}

study_objective = {
    "objectiveLevelUid": "string",
    "objectiveData": {
        "parameterValues": [
            {
                "values": [
                    {"uid": "string", "name": "string", "type": "string", "index": 0}
                ],
                "position": 0,
                "value": 0,
                "conjunction": "string",
            }
        ],
        "objectiveTemplateUid": "string",
        "nameOverride": "string",
        "libraryName": "string",
    },
}

study_endpoint = {
    "studyObjectiveUid": "string",
    "endpointLevelUid": "string",
    "endpointSubLevelUid": "string",
    "endpointData": {
        "parameterValues": [
            {
                "values": [
                    {"uid": "string", "name": "string", "type": "string", "index": 0}
                ],
                "position": 0,
                "value": 0,
                "conjunction": "string",
            }
        ],
        "endpointTemplateUid": "string",
        "nameOverride": "string",
        "libraryName": "string",
    },
    "endpointUnits": {"units": ["string"], "separator": "string"},
    "timeframeUid": "string",
}

study_criteria = {
    "criteriaData": {
        "parameterValues": [
            {
                "values": [
                    {"uid": "string", "name": "string", "type": "string", "index": 0}
                ],
                "position": 0,
                "value": 0,
                "conjunction": "string",
            }
        ],
        "criteriaTemplateUid": "string",
        "nameOverride": "string",
        "libraryName": "string",
    }
}

study_activity_schedule = {
  "studyActivityUid": "string",
  "studyVisitUid": "string",
  "note": "string"
}

timeframes = {
    "parameterValues": [
        {
            "values": [
                {"uid": "string", "name": "string", "type": "string", "index": 0}
            ],
            "position": 0,
            "value": 0,
            "conjunction": "string",
        }
    ],
    "timeframeTemplateUid": "string",
    "nameOverride": "string",
    "libraryName": "string",
}

compound_alias = {
    "name": "string",
    "nameSentenceCase": "string",
    "definition": "string",
    "abbreviation": "string",
    "libraryName": "string",
    "compoundUid": "string",
    "isPreferredSynonym": False,
}

compound = {
    "name": "string",
    "nameSentenceCase": "string",
    "definition": "string",
    "abbreviation": "string",
    "libraryName": "string",
    "analyteNumber": "string",
    "nncShortNumber": "string",
    "nncLongNumber": "string",
    "isSponsorCompound": True,
    "isNameInn": True,
    "substanceTermsUids": [],
    "doseValuesUids": [],
    "strengthValuesUids": [],
    "lagTimesUids": [],
    "deliveryDevicesUids": [],
    "dispensersUids": [],
    "projectsUids": [],
    "brandsUids": [],
    "doseFrequencyUids": [],
    "dosageFormUids": [],
    "routeOfAdministrationUids": [],
    "halfLifeUid": "string",
}

numeric_value_with_unit = {
    "name": "string",
    "nameSentenceCase": "string",
    "definition": "string",
    "abbreviation": "string",
    "libraryName": "string",
    "templateParameter": False,
    "value": 0,
    "unitDefinitionUid": "string",
}

lag_time = {
    "name": "string",
    "nameSentenceCase": "string",
    "definition": "string",
    "abbreviation": "string",
    "libraryName": "string",
    "templateParameter": False,
    "value": 0,
    "unitDefinitionUid": "string",
    "sdtmDomainUid": "string",
}

study_compound = {
    "compoundAliasUid": "string",
    "typeOfTreatmentUid": "string",
    "routeOfAdministrationUid": "string",
    "strengthValueUid": "string",
    "dosageFormUid": "string",
    "dispensedInUid": "string",
    "deviceUid": "string",
    "formulationUid": "string",
    "otherInfo": "string",
    "reasonForMissingNullValueUid": "string",
}

unit_definition = {
    "name": "string",
    "libraryName": "Sponsor",
    "convertibleUnit": True,
    "displayUnit": True,
    "masterUnit": True,
    "siUnit": True,
    "usConventionalUnit": True,
    "ctUnits": ["string"],
    "unitSubsets": [],
    "ucum": "string",
    "unitDimension": "string",
    "legacyCode": "string",
    "molecularWeightConvExpon": 0,
    "conversionFactorToMaster": 0,
    "comment": "string",
    "order": 0,
    "definition": "string",
    "templateParameter": False,
}

activity = {
    "name": "string",
    "nameSentenceCase": "string",
    "definition": "string",
    "abbreviation": "string",
    "libraryName": "string",
    "activitySubGroup": "string",
}

activity_groups = {
  "name": "string",
  "nameSentenceCase": "string",
  "definition": "string",
  "abbreviation": "string",
  "libraryName": "string"
}

activity_sub_groups = {
  "name": "string",
  "nameSentenceCase": "string",
  "definition": "string",
  "abbreviation": "string",
  "libraryName": "string",
  "activityGroup": "string"
}

ct_term = {
  "catalogueName": "string",
  "codelistUid": "string",
  "codeSubmissionValue": "string",
  "nameSubmissionValue": "string",
  "nciPreferredName": "string",
  "definition": "string",
  "sponsorPreferredName": "string",
  "sponsorPreferredNameSentenceCase": "string",
  "order": None,
  "libraryName": "string"
}

dictionary_term = {
  "dictionaryId": "string",
  "name": "string",
  "nameSentenceCase": "string",
  "abbreviation": "string",
  "definition": "string",
  "codelistUid": "string",
  "libraryName": "string"
}
