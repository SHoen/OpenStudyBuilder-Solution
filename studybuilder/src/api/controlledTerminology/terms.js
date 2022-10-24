import repository from '../repository'

const resource = 'ct/terms'

const knownCodelists = {
  studyType: { attribute: 'codelist_uid', value: 'C99077' },
  trialIntentType: { attribute: 'codelist_uid', value: 'C66736' },
  trialType: { attribute: 'codelist_uid', value: 'C66739' },
  trialPhase: { attribute: 'codelist_uid', value: 'C66737' },
  interventionTypes: { attribute: 'codelist_uid', value: 'C99078' },
  therapeuticArea: { attribute: 'codelist_name', value: 'Therapeutic area' },
  interventionType: { attribute: 'codelist_uid', value: 'C99078' },
  controlType: { attribute: 'codelist_uid', value: 'C66785' },
  interventionModel: { attribute: 'codelist_uid', value: 'C99076' },
  trialBlindingSchema: { attribute: 'codelist_uid', value: 'C66735' },
  nullValues: { attribute: 'codelist_name', value: 'Null Flavor' },
  ageUnits: { attribute: 'codelist_uid', value: 'C66781' },
  objectiveLevels: { attribute: 'codelist_name', value: 'Objective Level' },
  units: { attribute: 'codelist_name', value: 'Unit' },
  visitTypes: { attribute: 'codelist_name', value: 'VisitType' },
  timepointReferences: { attribute: 'codelist_name', value: 'Time Point Reference' },
  epochs: { attribute: 'codelist_name', value: 'Epoch' },
  epochTypes: { attribute: 'codelist_name', value: 'Epoch Type' },
  epochSubTypes: { attribute: 'codelist_name', value: 'Epoch Sub Type' },
  sexOfParticipants: { attribute: 'codelist_name', value: 'Sex of Participants' },
  objectiveCategories: { attribute: 'codelist_name', value: 'Objective Category' },
  endpointLevels: { attribute: 'codelist_name', value: 'Endpoint Level' },
  endpointSubLevels: { attribute: 'codelist_name', value: 'Endpoint Sub Level' },
  endpointCategories: { attribute: 'codelist_name', value: 'Endpoint Category' },
  endpointSubCategories: { attribute: 'codelist_name', value: 'Endpoint Sub Category' },
  criteriaTypes: { attribute: 'codelist_name', value: 'Criteria Type' },
  criteriaCategories: { attribute: 'codelist_name', value: 'Criteria Category' },
  criteriaSubCategories: { attribute: 'codelist_name', value: 'Criteria Sub Category' },
  typeOfTreatment: { attribute: 'codelist_name', value: 'Type of Treatment' },
  routeOfAdministration: { attribute: 'codelist_uid', value: 'C66729' },
  dosageForm: { attribute: 'codelist_uid', value: 'C66726' },
  flowchartGroups: { attribute: 'codelist_name', value: 'Flowchart Group' },
  contactModes: { attribute: 'codelist_name', value: 'Visit Contact Mode' },
  epochAllocations: { attribute: 'codelist_name', value: 'Epoch Allocation' },
  armTypes: { attribute: 'codelist_name', value: 'Arm Type' },
  unitDimensions: { attribute: 'codelist_name', value: 'Unit Dimension' },
  unitSubsets: { attribute: 'codelist_name', value: 'Unit Subset' },
  elementSubTypes: { attribute: 'codelist_name', value: 'Element Sub Type' },
  elementTypes: { attribute: 'codelist_name', value: 'Element Type' },
  language: { attribute: 'codelist_name', value: 'Language' },
  sdtmDomainAbbreviation: { attribute: 'codelist_name', value: 'SDTM Domain Abbreviation' },
  originType: { attribute: 'codelist_name', value: 'Origin Type' },
  dataType: { attribute: 'codelist_name', value: 'Data type' },
  frequency: { attribute: 'codelist_uid', value: 'C71113' },
  deliveryDevice: { attribute: 'codelist_name', value: 'Delivery Device' },
  dispensedIn: { attribute: 'codelist_name', value: 'Compound Dispensed In' },
  adverseEvents: { attribute: 'codelist_uid', value: 'C66734' }
}

export default {
  getAll (params) {
    return repository.get(resource, { params })
  },
  getByCodelist (name) {
    const codelist = knownCodelists[name]
    if (codelist !== undefined) {
      const params = { size: 100 }
      params[codelist.attribute] = codelist.value
      return repository.get(`${resource}/names`, { params })
    }
    throw new Error(`Provided codelist (${name}) is unknown`)
  },
  getAttributesByCodelist (name) {
    const codelist = knownCodelists[name]
    if (codelist !== undefined) {
      const params = { size: 100 }
      params[codelist.attribute] = codelist.value
      return repository.get(`${resource}/attributes`, { params })
    }
    throw new Error(`Provided codelist (${name}) is unknown`)
  },
  getTermByUid (termUid) {
    return repository.get(`${resource}/${termUid}/names`)
  },
  getTermsByCodelistUid (codelistUid) {
    const params = {
      codelist_uid: codelistUid
    }
    return repository.get(`${resource}`, { params })
  }
}
