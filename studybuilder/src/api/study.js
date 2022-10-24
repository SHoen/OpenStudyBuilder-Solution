import constants from '@/constants/study'
import repository from './repository'

const resource = 'studies'

export default {
  get (options) {
    const params = {
      ...options
    }
    return repository.get(`${resource}`, { params })
  },
  projects_all () {
    const url = '/projects'
    return repository.get(url)
  },
  getAll (fields) {
    const url = `/${resource}`
    if (fields !== undefined) {
      fields = fields.join(',')
    }
    return repository.get(url, { params: { fields } })
  },
  getStudy (studyUid) {
    return repository.get(`${resource}/${studyUid}`)
  },
  getStudyProtocolTitle (studyUid) {
    return repository.get(`${resource}/${studyUid}/protocol-title`)
  },
  getStudyDescriptionMetadata (studyUid) {
    const fields = encodeURIComponent(constants.DESCRIPTION_METADATA)
    return repository.get(`${resource}/${studyUid}?fields=${fields}`)
  },
  getHighLevelStudyDesignMetadata (studyUid) {
    const fields = encodeURIComponent(constants.HIGH_LEVEL_STUDY_DESIGN_METADATA)
    return repository.get(`${resource}/${studyUid}?fields=${fields}`)
  },
  getStudyPopulationMetadata (studyUid) {
    const fields = encodeURIComponent(constants.POPULATION_METADATA)
    return repository.get(`${resource}/${studyUid}?fields=${fields}`)
  },
  getStudyInterventionMetadata (studyUid) {
    const fields = encodeURIComponent(constants.INTERVENTION_METADATA)
    return repository.get(`${resource}/${studyUid}?fields=${fields}`)
  },
  getAllStudyObjectives (params) {
    return repository.get('study/study-objectives', { params })
  },
  getStudyObjectives (studyUid, params) {
    return repository.get(`study/${studyUid}/study-objectives`, { params })
  },
  getStudyObjectiveAuditTrail (studyUid, studyObjectiveUid) {
    return repository.get(`study/${studyUid}/study-objectives/${studyObjectiveUid}/audit-trail`)
  },
  getStudyObjectivesDocx (studyUid) {
    return repository.get(`study/${studyUid}/study-objectives.docx`, { responseType: 'arraybuffer' })
  },
  selectStudyObjective (studyUid, objectiveUid, objectiveLevelUid) {
    const data = { objectiveUid, objectiveLevelUid }
    return repository.post(`study/${studyUid}/study-objectives/select`, data)
  },
  getStudyObjectivePreview (studyUid, data) {
    return repository.post(`study/${studyUid}/study-objectives/create/preview`, data)
  },
  createStudyObjective (studyUid, data) {
    return repository.post(`study/${studyUid}/study-objectives/create`, data)
  },
  updateStudyObjective (studyUid, studyObjectiveUid, data) {
    return repository.patch(`study/${studyUid}/study-objectives/${studyObjectiveUid}`, data)
  },
  updateStudyObjectiveLatestVersion (studyUid, studyObjectiveUid) {
    return repository.post(`study/${studyUid}/study-objectives/${studyObjectiveUid}/sync-latest-version`)
  },
  updateStudyObjectiveOrder (studyUid, studyObjectiveUid, order) {
    const data = { new_order: order }
    return repository.patch(`study/${studyUid}/study-objectives/${studyObjectiveUid}/order`, data)
  },
  deleteStudyObjective (studyUid, studyObjectiveUid) {
    return repository.delete(`study/${studyUid}/study-objectives/${studyObjectiveUid}`)
  },
  getAllStudyEndpoints (params) {
    return repository.get('study/study-endpoints', { params })
  },
  getStudyEndpoints (studyUid, params) {
    return repository.get(`study/${studyUid}/study-endpoints`, { params })
  },
  getStudyEndpointsByObjective (studyUid, objectiveUid) {
    const params = {
      filters: {
        'studyObjective.objective.uid': {
          v: [objectiveUid]
        }
      }
    }
    return repository.get('study/study-endpoints', { params })
  },
  getStudyEndpointAuditTrail (studyUid, studyEndpointUid) {
    return repository.get(`study/${studyUid}/study-endpoints/${studyEndpointUid}/audit-trail`)
  },
  getStudyEndpointPreview (studyUid, data) {
    return repository.post(`study/${studyUid}/study-endpoints/create/preview`, data)
  },
  createStudyEndpoint (studyUid, data) {
    return repository.post(`study/${studyUid}/study-endpoints/create`, data)
  },
  selectStudyEndpoint (studyUid, data) {
    return repository.post(`study/${studyUid}/study-endpoints/select`, data)
  },
  updateStudyEndpoint (studyUid, studyEndpointUid, data) {
    return repository.patch(`study/${studyUid}/study-endpoints/${studyEndpointUid}`, data)
  },
  updateStudyEndpointEndpointLatestVersion (studyUid, studyEndpointUid) {
    return repository.post(`study/${studyUid}/study-endpoints/${studyEndpointUid}/sync-latest-endpoint-version`)
  },
  updateStudyEndpointTimeframeLatestVersion (studyUid, studyEndpointUid) {
    return repository.post(`study/${studyUid}/study-endpoints/${studyEndpointUid}/sync-latest-timeframe-version`)
  },
  updateStudyEndpointOrder (studyUid, studyEndpointUid, order) {
    const data = { new_order: order }
    return repository.patch(`study/${studyUid}/study-endpoints/${studyEndpointUid}/order`, data)
  },
  deleteStudyEndpoint (studyUid, studyEndpointUid) {
    return repository.delete(`study/${studyUid}/study-endpoints/${studyEndpointUid}`)
  },
  updateStudyObjectiveAcceptVersion (studyUid, studyObjectiveUid) {
    return repository.post(`study/${studyUid}/study-objectives/${studyObjectiveUid}/accept-version`)
  },
  updateStudyEndpointAcceptVersion (studyUid, studyEndpointUid) {
    return repository.post(`study/${studyUid}/study-endpoints/${studyEndpointUid}/accept-version`)
  },
  getStudyCompounds (studyUid, params) {
    return repository.get(`study/${studyUid}/study-compounds`, { params })
  },
  updateStudyCompound (studyUid, studyCompoundUid, data) {
    return repository.patch(`study/${studyUid}/study-compounds/${studyCompoundUid}`, data)
  },
  selectStudyCompound (studyUid, data) {
    return repository.post(`study/${studyUid}/study-compounds/select`, data)
  },
  deleteStudyCompound (studyUid, studyCompoundUid) {
    return repository.delete(`study/${studyUid}/study-compounds/${studyCompoundUid}`)
  },
  getStudyCompoundDosings (studyUid) {
    return repository.get(`study/${studyUid}/study-compound-dosings`)
  },
  getStudyCompoundDosingAuditTrail (studyUid, studyCompoundDosingUid) {
    return repository.get(`study/${studyUid}/study-compound-dosings/${studyCompoundDosingUid}/audit-trail`)
  },
  updateStudyCompoundDosing (studyUid, studyCompoundDosingUid, data) {
    return repository.patch(`study/${studyUid}/study-compound-dosings/${studyCompoundDosingUid}`, data)
  },
  addStudyCompoundDosing (studyUid, data) {
    return repository.post(`study/${studyUid}/study-compound-dosings/select`, data)
  },
  deleteStudyCompoundDosing (studyUid, studyCompoundDosingUid) {
    return repository.delete(`study/${studyUid}/study-compound-dosings/${studyCompoundDosingUid}`)
  },
  getAllStudyActivities (params) {
    return repository.get('study/study-activities', { params })
  },
  getStudyActivities (studyUid, params) {
    return repository.get(`study/${studyUid}/study-activities`, { params })
  },
  createStudyActivity (studyUid, data) {
    return repository.post(`study/${studyUid}/study-activities/create`, data)
  },
  updateStudyActivity (studyUid, studyActivityUid, data) {
    return repository.patch(`study/${studyUid}/study-activities/${studyActivityUid}`, data)
  },
  deleteStudyActivity (studyUid, studyActivityUid) {
    return repository.delete(`study/${studyUid}/study-activities/${studyActivityUid}`)
  },
  studyActivityBatchOperations (studyUid, data) {
    return repository.post(`study/${studyUid}/study-activities/batch`, data)
  },
  getStudyActivityAuditTrail (studyUid, studyActivityUid) {
    return repository.get(`study/${studyUid}/study-activities/${studyActivityUid}/audit-trail`)
  },
  updateStudyActivityOrder (studyUid, studyActivityUid, order) {
    const data = { new_order: order }
    return repository.patch(`study/${studyUid}/study-activities/${studyActivityUid}/order`, data)
  },
  getStudyActivitySchedules (studyUid) {
    return repository.get(`study/${studyUid}/study-activity-schedules`)
  },
  createStudyActivitySchedule (studyUid, data) {
    return repository.post(`study/${studyUid}/study-activity-schedules`, data)
  },
  deleteStudyActivitySchedule (studyUid, scheduleUid) {
    return repository.delete(`study/${studyUid}/study-activity-schedules/${scheduleUid}`)
  },
  studyActivityScheduleBatchOperations (studyUid, data) {
    return repository.post(`study/${studyUid}/study-activity-schedules/batch`, data)
  },
  getAllStudyCriteria (params) {
    return repository.get('study/study-criteria', { params })
  },
  getStudyCriteria (studyUid) {
    return repository.get(`study/${studyUid}/study-criteria`)
  },
  getStudyCriteriaWithType (studyUid, criteriaType) {
    const params = {
      filters: JSON.stringify({ 'criteriaType.sponsorPreferredNameSentenceCase': { v: [criteriaType.sponsorPreferredNameSentenceCase] } })
    }
    return repository.get(`study/${studyUid}/study-criteria`, { params })
  },
  getStudyCriteriaAuditTrail (studyUid, studyCriteriaUid) {
    return repository.get(`study/${studyUid}/study-criteria/${studyCriteriaUid}/audit-trail`)
  },
  getStudyCriteriaPreview (studyUid, data) {
    return repository.post(`study/${studyUid}/study-criteria/create/preview`, data)
  },
  createStudyCriteria (studyUid, data) {
    return repository.post(`study/${studyUid}/study-criteria/create`, data)
  },
  batchCreateStudyCriteria (studyUid, data) {
    return repository.post(`study/${studyUid}/study-criteria/batch-select`, data)
  },
  patchStudyCriteria (studyUid, studyCriteriaUid, data) {
    return repository.patch(`study/${studyUid}/study-criteria/${studyCriteriaUid}/finalize`, data)
  },
  updateStudyCriteriaOrder (studyUid, studyCriteriaUid, order) {
    const data = { new_order: order }
    return repository.patch(`study/${studyUid}/study-criteria/${studyCriteriaUid}/order`, data)
  },
  updateStudyCriteriaKeyCriteria (studyUid, studyCriteriaUid, keyCriteria) {
    const data = { key_criteria: keyCriteria }
    return repository.patch(`study/${studyUid}/study-criteria/${studyCriteriaUid}/key-criteria`, data)
  },
  deleteStudyCriteria (studyUid, studyCriteriaUid) {
    return repository.delete(`study/${studyUid}/study-criteria/${studyCriteriaUid}`)
  },
  getAllStudyActivityInstructions (params) {
    return repository.get('study/study-activity-instructions', { params })
  },
  getStudyActivityInstructions (studyUid) {
    return repository.get(`study/${studyUid}/study-activity-instructions`)
  },
  studyActivityInstructionBatchOperations (studyUid, data) {
    return repository.post(`study/${studyUid}/study-activity-instructions/batch`, data)
  },
  deleteStudyActivityInstruction (studyUid, studyActivityInstructionUid) {
    return repository.delete(`study/${studyUid}/study-activity-instructions/${studyActivityInstructionUid}`)
  },
  create (data) {
    return repository.post(`${resource}`, data)
  },
  updateIdentification (uid, data) {
    const payload = {
      currentMetadata: {
        identificationMetadata: data
      }
    }
    return repository.patch(`${resource}/${uid}`, payload)
  },
  updateStudyType (uid, data) {
    const payload = {
      currentMetadata: {
        highLevelStudyDesign: data
      }
    }
    return repository.patch(`${resource}/${uid}`, payload)
  },
  updateStudyPopulation (uid, data) {
    const payload = {
      currentMetadata: {
        studyPopulation: data
      }
    }
    return repository.patch(`${resource}/${uid}`, payload)
  },
  updateStudyIntervention (studyUid, data) {
    const payload = {
      currentMetadata: {
        studyIntervention: data
      }
    }
    return repository.patch(`${resource}/${studyUid}`, payload)
  },
  updateStudyDescription (studyUid, data) {
    const payload = {
      currentMetadata: {
        studyDescription: data
      }
    }
    return repository.patch(`${resource}/${studyUid}`, payload)
  },
  getStudyProtocolFlowchartHtml (studyUid) {
    return repository.get(`${resource}/${studyUid}/flowchart.html`)
  },
  getStudyProtocolFlowchartDocx (studyUid) {
    return repository.get(`${resource}/${studyUid}/flowchart.docx`, { responseType: 'arraybuffer' })
  },
  getStudyProtocolInterventionsTableHtml (studyUid) {
    return repository.get(`${resource}/${studyUid}/interventions.html`)
  },
  getStudyProtocolInterventionsTableDocx (studyUid) {
    return repository.get(`${resource}/${studyUid}/interventions.docx`, { responseType: 'arraybuffer' })
  },
  copyFromStudy (uid, options) {
    return repository.patch(`${resource}/${uid}/copy-component?referenceStudyUid=${options.referenceStudyUid}&componentToCopy=${options.componentToCopy}&overwrite=${options.overwrite}`)
  },
  getStudyDesignFigureSvg (studyUid) {
    return repository.get(`${resource}/${studyUid}/design.svg`)
  },
  getStudyDesignFigureSvgArray (studyUid) {
    return repository.get(`${resource}/${studyUid}/design.svg`, { responseType: 'arraybuffer' })
  }
}
