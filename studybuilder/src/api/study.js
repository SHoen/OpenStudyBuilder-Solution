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
  getAll () {
    const url = `/${resource}`
    return repository.get(url, { params: { page_size: 0 } })
  },
  getStudy (studyUid, ignoreErrors, studyVersion) {
    const params = {
      ignoreErrors: ignoreErrors,
      study_value_version: studyVersion
    }
    return repository.get(`${resource}/${studyUid}`, { params })
  },
  getStudySnapshotHistory (studyUid, params) {
    return repository.get(`${resource}/${studyUid}/snapshot-history`, { params })
  },
  deleteStudy (studyUid) {
    return repository.delete(`${resource}/${studyUid}`)
  },
  releaseStudy (studyUid, data) {
    return repository.post(`${resource}/${studyUid}/release`, data)
  },
  lockStudy (studyUid, data) {
    return repository.post(`${resource}/${studyUid}/locks`, data)
  },
  unlockStudy (studyUid) {
    return repository.delete(`${resource}/${studyUid}/locks`)
  },
  getStudyPreferredTimeUnit (studyUid) {
    return repository.get(`${resource}/${studyUid}/time-units`, { ignoreErrors: true })
  },
  updateStudyPreferredTimeUnit (studyUid, data) {
    return repository.patch(`${resource}/${studyUid}/time-units`, data)
  },
  getStudyProtocolTitle (studyUid, studyVersion) {
    const params = {
      study_value_version: studyVersion
    }
    return repository.get(`${resource}/${studyUid}/protocol-title`, { params })
  },
  getStudyDescriptionMetadata (studyUid, studyVersion) {
    const params = {
      study_value_version: studyVersion
    }
    return repository.get(`${resource}/${studyUid}?include_sections=${constants.DESCRIPTION_METADATA}`, { params })
  },
  getHighLevelStudyDesignMetadata (studyUid, studyVersion) {
    const includeSections = [constants.HIGH_LEVEL_STUDY_DESIGN_METADATA]
    const params = {
      study_value_version: studyVersion
    }
    return repository.get(`${resource}/${studyUid}?include_sections=${includeSections}`, { params })
  },
  getStudyPopulationMetadata (studyUid, studyVersion) {
    const includeSections = [constants.POPULATION_METADATA]
    const params = {
      study_value_version: studyVersion
    }
    return repository.get(`${resource}/${studyUid}?include_sections=${includeSections}`, { params })
  },
  getStudyInterventionMetadata (studyUid, studyVersion) {
    const includeSections = [constants.INTERVENTION_METADATA]
    const params = {
      study_value_version: studyVersion
    }
    return repository.get(`${resource}/${studyUid}?include_sections=${includeSections}`, { params })
  },
  getStudyFieldsAuditTrail (studyUid, section) {
    const includeSections = []
    if (section !== 'identification_metadata') {
      includeSections.push(section)
      return repository.get(`${resource}/${studyUid}/fields-audit-trail?include_sections=${includeSections}&exclude_sections=identification_metadata`)
    }
    return repository.get(`${resource}/${studyUid}/fields-audit-trail`)
  },
  getAllStudyObjectives (params) {
    return repository.get('study-objectives', { params })
  },
  getStudyObjectives (studyUid, params) {
    return repository.get(`studies/${studyUid}/study-objectives`, { params })
  },
  getStudyObjectivesAuditTrail (studyUid) {
    return repository.get(`studies/${studyUid}/study-objectives/audit-trail`)
  },
  getStudyObjectiveAuditTrail (studyUid, studyObjectiveUid) {
    return repository.get(`studies/${studyUid}/study-objectives/${studyObjectiveUid}/audit-trail`)
  },
  getStudyObjectivesHtml (studyUid) {
    return repository.get(`studies/${studyUid}/study-objectives.html`)
  },
  getStudyObjectivesDocx (studyUid) {
    return repository.get(`studies/${studyUid}/study-objectives.docx`, { responseType: 'arraybuffer' })
  },
  selectStudyObjective (studyUid, objectiveUid, objectiveLevelUid) {
    const data = {
      objective_uid: objectiveUid,
      objective_level_uid: objectiveLevelUid
    }
    return repository.post(`studies/${studyUid}/study-objectives`, data)
  },
  getStudyObjectivePreview (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-objectives/preview`, data)
  },
  createStudyObjective (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-objectives?create_objective=true`, data)
  },
  batchCreateStudyObjectives (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-objectives/batch-select`, data)
  },
  updateStudyObjective (studyUid, studyObjectiveUid, data) {
    return repository.patch(`studies/${studyUid}/study-objectives/${studyObjectiveUid}`, data)
  },
  updateStudyObjectiveLatestVersion (studyUid, studyObjectiveUid) {
    return repository.post(`studies/${studyUid}/study-objectives/${studyObjectiveUid}/sync-latest-version`)
  },
  updateStudyObjectiveOrder (studyUid, studyObjectiveUid, order) {
    const data = { new_order: order }
    return repository.patch(`studies/${studyUid}/study-objectives/${studyObjectiveUid}/order`, data)
  },
  deleteStudyObjective (studyUid, studyObjectiveUid) {
    return repository.delete(`studies/${studyUid}/study-objectives/${studyObjectiveUid}`)
  },
  getAllStudyEndpoints (params) {
    return repository.get('study-endpoints', { params })
  },
  getStudyEndpoints (studyUid, params) {
    return repository.get(`studies/${studyUid}/study-endpoints`, { params })
  },
  getStudyEndpointsByObjective (studyUid, objectiveUid) {
    const params = {
      filters: {
        'studyObjective.objective.uid': {
          v: [objectiveUid]
        }
      }
    }
    return repository.get('study-endpoints', { params })
  },
  getStudyEndpointsAuditTrail (studyUid) {
    return repository.get(`studies/${studyUid}/study-endpoints/audit-trail`)
  },
  getStudyEndpointAuditTrail (studyUid, studyEndpointUid) {
    return repository.get(`studies/${studyUid}/study-endpoints/${studyEndpointUid}/audit-trail`)
  },
  getStudyEndpointPreview (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-endpoints/preview`, data)
  },
  createStudyEndpoint (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-endpoints?create_endpoint=true`, data)
  },
  batchCreateStudyEndpoints (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-endpoints/batch-select`, data)
  },
  selectStudyEndpoint (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-endpoints`, data)
  },
  updateStudyEndpoint (studyUid, studyEndpointUid, data) {
    return repository.patch(`studies/${studyUid}/study-endpoints/${studyEndpointUid}`, data)
  },
  updateStudyEndpointEndpointLatestVersion (studyUid, studyEndpointUid) {
    return repository.post(`studies/${studyUid}/study-endpoints/${studyEndpointUid}/sync-latest-endpoint-version`)
  },
  updateStudyEndpointTimeframeLatestVersion (studyUid, studyEndpointUid) {
    return repository.post(`studies/${studyUid}/study-endpoints/${studyEndpointUid}/sync-latest-timeframe-version`)
  },
  updateStudyEndpointOrder (studyUid, studyEndpointUid, order) {
    const data = { new_order: order }
    return repository.patch(`studies/${studyUid}/study-endpoints/${studyEndpointUid}/order`, data)
  },
  deleteStudyEndpoint (studyUid, studyEndpointUid) {
    return repository.delete(`studies/${studyUid}/study-endpoints/${studyEndpointUid}`)
  },
  updateStudyObjectiveAcceptVersion (studyUid, studyObjectiveUid) {
    return repository.post(`studies/${studyUid}/study-objectives/${studyObjectiveUid}/accept-version`)
  },
  updateStudyEndpointAcceptVersion (studyUid, studyEndpointUid) {
    return repository.post(`studies/${studyUid}/study-endpoints/${studyEndpointUid}/accept-version`)
  },
  getStudyCompounds (studyUid, params) {
    return repository.get(`studies/${studyUid}/study-compounds`, { params })
  },
  getStudyCompoundsAuditTrail (studyUid) {
    return repository.get(`studies/${studyUid}/study-compounds/audit-trail`)
  },
  getStudyCompoundAuditTrail (studyUid, studyCompoundUid) {
    return repository.get(`studies/${studyUid}/study-compounds/${studyCompoundUid}/audit-trail`)
  },
  updateStudyCompound (studyUid, studyCompoundUid, data) {
    return repository.patch(`studies/${studyUid}/study-compounds/${studyCompoundUid}`, data)
  },
  selectStudyCompound (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-compounds`, data)
  },
  deleteStudyCompound (studyUid, studyCompoundUid) {
    return repository.delete(`studies/${studyUid}/study-compounds/${studyCompoundUid}`)
  },
  getStudyCompoundDosings (studyUid, studyValueVersion) {
    const params = {
      study_value_version: studyValueVersion,
      page_size: 0
    }
    return repository.get(`studies/${studyUid}/study-compound-dosings`, { params })
  },
  getStudyCompoundDosingsAuditTrail (studyUid) {
    return repository.get(`studies/${studyUid}/study-compound-dosings/audit-trail`)
  },
  getStudyCompoundDosingAuditTrail (studyUid, studyCompoundDosingUid) {
    return repository.get(`studies/${studyUid}/study-compound-dosings/${studyCompoundDosingUid}/audit-trail`)
  },
  updateStudyCompoundDosing (studyUid, studyCompoundDosingUid, data) {
    return repository.patch(`studies/${studyUid}/study-compound-dosings/${studyCompoundDosingUid}`, data)
  },
  addStudyCompoundDosing (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-compound-dosings`, data)
  },
  deleteStudyCompoundDosing (studyUid, studyCompoundDosingUid) {
    return repository.delete(`studies/${studyUid}/study-compound-dosings/${studyCompoundDosingUid}`)
  },
  getAllStudyActivities (params) {
    return repository.get('study-activities', { params })
  },
  getStudyActivities (studyUid, params) {
    return repository.get(`studies/${studyUid}/study-activities`, { params })
  },
  createStudyActivity (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-activities`, data)
  },
  updateStudyActivity (studyUid, studyActivityUid, data) {
    return repository.patch(`studies/${studyUid}/study-activities/${studyActivityUid}`, data)
  },
  deleteStudyActivity (studyUid, studyActivityUid) {
    return repository.delete(`studies/${studyUid}/study-activities/${studyActivityUid}`)
  },
  studyActivityBatchOperations (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-activities/batch`, data)
  },
  getStudyActivitiesAuditTrail (studyUid) {
    return repository.get(`studies/${studyUid}/study-activities/audit-trail`)
  },
  getStudyActivityAuditTrail (studyUid, studyActivityUid) {
    return repository.get(`studies/${studyUid}/study-activities/${studyActivityUid}/audit-trail`)
  },
  updateStudyActivityOrder (studyUid, studyActivityUid, order) {
    const data = { new_order: order }
    return repository.patch(`studies/${studyUid}/study-activities/${studyActivityUid}/order`, data)
  },
  updateToApprovedActivity (studyUid, studyActivityUid) {
    return repository.patch(`studies/${studyUid}/study-activities/${studyActivityUid}/activity-requests-approvals`)
  },
  getStudyActivitySchedules (studyUid, options) {
    const params = {
      ...options
    }
    return repository.get(`studies/${studyUid}/study-activity-schedules`, { params })
  },
  createStudyActivitySchedule (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-activity-schedules`, data)
  },
  deleteStudyActivitySchedule (studyUid, scheduleUid) {
    return repository.delete(`studies/${studyUid}/study-activity-schedules/${scheduleUid}`)
  },
  studyActivityScheduleBatchOperations (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-activity-schedules/batch`, data)
  },
  getAllStudyCriteria (params) {
    return repository.get('study-criteria', { params })
  },
  getStudyCriteria (studyUid, studyVersion) {
    const params = {
      page_size: 0,
      study_value_version: studyVersion
    }
    return repository.get(`studies/${studyUid}/study-criteria`, { params })
  },
  getStudyCriteriaWithType (studyUid, criteriaType, params) {
    if (!params.filters) {
      params.filters = JSON.stringify({ 'criteria_type.sponsor_preferred_name_sentence_case': { v: [criteriaType.sponsor_preferred_name_sentence_case] } })
    } else {
      const filters = JSON.parse(params.filters)
      filters['criteria_type.sponsor_preferred_name_sentence_case'] = { v: [criteriaType.sponsor_preferred_name_sentence_case] }
      params.filters = JSON.stringify(filters)
    }
    return repository.get(`studies/${studyUid}/study-criteria`, { params })
  },
  getStudyCriteriaAllAuditTrail (studyUid, criteriaTypeUid) {
    return repository.get(`studies/${studyUid}/study-criteria/audit-trail?criteria_type_uid=${criteriaTypeUid}`)
  },
  getStudyCriteriaAuditTrail (studyUid, studyCriteriaUid) {
    return repository.get(`studies/${studyUid}/study-criteria/${studyCriteriaUid}/audit-trail`)
  },
  getStudyCriteriaPreview (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-criteria/preview`, data)
  },
  createStudyCriteria (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-criteria?create_criteria=true`, data)
  },
  batchCreateStudyCriteria (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-criteria/batch-select`, data)
  },
  patchStudyCriteria (studyUid, studyCriteriaUid, data) {
    return repository.patch(`studies/${studyUid}/study-criteria/${studyCriteriaUid}`, data)
  },
  updateStudyCriteriaOrder (studyUid, studyCriteriaUid, order) {
    const data = { new_order: order }
    return repository.patch(`studies/${studyUid}/study-criteria/${studyCriteriaUid}/order`, data)
  },
  updateStudyCriteriaKeyCriteria (studyUid, studyCriteriaUid, keyCriteria) {
    const data = { key_criteria: keyCriteria }
    return repository.patch(`studies/${studyUid}/study-criteria/${studyCriteriaUid}/key-criteria`, data)
  },
  deleteStudyCriteria (studyUid, studyCriteriaUid) {
    return repository.delete(`studies/${studyUid}/study-criteria/${studyCriteriaUid}`)
  },
  updateStudyCriteriaAcceptVersion (studyUid, studyCriteriaUid) {
    return repository.post(`studies/${studyUid}/study-criteria/${studyCriteriaUid}/accept-version`)
  },
  updateStudyCriteriaLatestVersion (studyUid, studyCriteriaUid) {
    return repository.post(`studies/${studyUid}/study-criteria/${studyCriteriaUid}/sync-latest-version`)
  },
  getAllStudyActivityInstructions (params) {
    return repository.get('study-activity-instructions', { params })
  },
  getStudyActivityInstructions (studyUid, params) {
    return repository.get(`studies/${studyUid}/study-activity-instructions`, { params })
  },
  studyActivityInstructionBatchOperations (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-activity-instructions/batch`, data)
  },
  deleteStudyActivityInstruction (studyUid, studyActivityInstructionUid) {
    return repository.delete(`studies/${studyUid}/study-activity-instructions/${studyActivityInstructionUid}`)
  },
  create (data) {
    return repository.post(`${resource}`, data)
  },
  updateIdentification (uid, data) {
    const payload = {
      current_metadata: {
        identification_metadata: data
      }
    }
    return repository.patch(`${resource}/${uid}`, payload)
  },
  updateStudyType (uid, data) {
    const payload = {
      current_metadata: {
        high_level_study_design: data
      }
    }
    return repository.patch(`${resource}/${uid}`, payload)
  },
  updateStudyPopulation (uid, data) {
    const payload = {
      current_metadata: {
        study_population: data
      }
    }
    return repository.patch(`${resource}/${uid}`, payload)
  },
  updateStudyIntervention (studyUid, data) {
    const payload = {
      current_metadata: {
        study_intervention: data
      }
    }
    return repository.patch(`${resource}/${studyUid}`, payload)
  },
  updateStudyDescription (studyUid, data) {
    const payload = {
      current_metadata: {
        study_description: data
      }
    }
    return repository.patch(`${resource}/${studyUid}`, payload)
  },
  getStudyProtocolFlowchartHtml (studyUid, studyVersion) {
    const params = {
      study_value_version: studyVersion
    }
    return repository.get(`${resource}/${studyUid}/flowchart.html`, { params })
  },
  getStudyProtocolFlowchartDocx (studyUid, studyVersion) {
    const params = {
      study_value_version: studyVersion,
      responseType: 'arraybuffer'
    }
    return repository.get(`${resource}/${studyUid}/flowchart.docx`, { params })
  },
  getStudyProtocolInterventionsTableHtml (studyUid) {
    return repository.get(`${resource}/${studyUid}/interventions.html`)
  },
  getStudyProtocolInterventionsTableDocx (studyUid) {
    return repository.get(`${resource}/${studyUid}/interventions.docx`, { responseType: 'arraybuffer' })
  },
  copyFromStudy (uid, options) {
    return repository.patch(`${resource}/${uid}/copy-component?reference_study_uid=${options.reference_study_uid}&component_to_copy=${options.component_to_copy}&overwrite=${options.overwrite}`)
  },
  getStudyDesignFigureSvg (studyUid) {
    return repository.get(`${resource}/${studyUid}/design.svg`)
  },
  getStudyDesignFigureSvgArray (studyUid) {
    return repository.get(`${resource}/${studyUid}/design.svg`, { responseType: 'arraybuffer' })
  },
  getStudyDiseaseMilestones (studyUid, params) {
    return repository.get(`${resource}/${studyUid}/study-disease-milestones`, { params })
  },
  getStudyDiseaseMilestonesAuditTrail (studyUid) {
    return repository.get(`${resource}/${studyUid}/study-disease-milestones/audit-trail`)
  },
  getStudyDiseaseMilestoneAuditTrail (studyUid, diseaseMilestoneUid) {
    return repository.get(`${resource}/${studyUid}/study-disease-milestones/${diseaseMilestoneUid}/audit-trail`)
  },
  createStudyDiseaseMilestone (studyUid, data) {
    return repository.post(`${resource}/${studyUid}/study-disease-milestones`, data)
  },
  updateStudyDiseaseMilestone (studyUid, diseaseMilestoneUid, data) {
    return repository.patch(`${resource}/${studyUid}/study-disease-milestones/${diseaseMilestoneUid}`, data)
  },
  updateStudyDiseaseMilestoneOrder (studyUid, diseaseMilestoneUid, order) {
    const data = { new_order: order.new_order }
    return repository.patch(`${resource}/${studyUid}/study-disease-milestones/${diseaseMilestoneUid}/order`, data)
  },
  deleteStudyDiseaseMilestone (studyUid, diseaseMilestoneUid) {
    return repository.delete(`${resource}/${studyUid}/study-disease-milestones/${diseaseMilestoneUid}`)
  },
  getCtrOdmXml (studyUid) {
    return repository.get(`${resource}/${studyUid}/ctr/odm.xml`)
  },
  downloadCtrOdmXml (studyUid) {
    return repository.get(`${resource}/${studyUid}/ctr/odm.xml`, { responseType: 'arraybuffer' })
  },
  getAllStudyFootnotes (params) {
    return repository.get('study-soa-footnotes', { params })
  },
  getStudyFootnotes (studyUid, params) {
    return repository.get(`studies/${studyUid}/study-soa-footnotes`, { params })
  },
  getStudyFootnotesAuditTrail (studyUid) {
    return repository.get(`studies/${studyUid}/study-soa-footnote/audit-trail`)
  },
  getStudyFootnoteAuditTrail (studyUid, studyFootnoteUid) {
    return repository.get(`studies/${studyUid}/study-soa-footnotes/${studyFootnoteUid}/audit-trail`)
  },
  getStudyFootnotePreview (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-soa-footnotes/preview`, data)
  },
  createStudyFootnote (studyUid, data, createFootnote) {
    if (createFootnote === undefined) {
      createFootnote = false
    }
    return repository.post(`${resource}/${studyUid}/study-soa-footnotes?create_footnote=${createFootnote}`, data)
  },
  batchCreateStudyFootnotes (studyUid, data) {
    return repository.post(`studies/${studyUid}/study-soa-footnotes/batch-select`, data)
  },
  updateStudyFootnote (studyUid, studyFootnoteUid, data) {
    return repository.patch(`${resource}/${studyUid}/study-soa-footnotes/${studyFootnoteUid}`, data)
  },
  deleteStudyFootnote (studyUid, studyFootnoteUid) {
    return repository.delete(`${resource}/${studyUid}/study-soa-footnotes/${studyFootnoteUid}`)
  }
}
