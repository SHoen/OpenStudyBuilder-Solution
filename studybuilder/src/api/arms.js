import repository from './repository'

const resource = 'study'

export default {
  getAllForStudy (uid, options) {
    const params = {
      ...options
    }
    return repository.get(`${resource}/${uid}/study-arms`, { params })
  },
  create (uid, data) {
    const params = {
      ...data
    }
    return repository.post(`${resource}/${uid}/study-arms/create`, params)
  },
  edit (uid, data, armUid) {
    const params = {
      ...data
    }
    return repository.patch(`${resource}/${uid}/study-arms/${armUid}`, params)
  },
  delete (studyUid, armUid) {
    return repository.delete(`${resource}/${studyUid}/study-arms/${armUid}`)
  },
  getStudyElements (uid, options) {
    const params = {
      ...options
    }
    return repository.get(`${resource}/${uid}/study-elements`, { params })
  },
  getStudyElement (uid, elementUid) {
    return repository.get(`${resource}/${uid}/study-elements/${elementUid}`)
  },
  addStudyElement (uid, data) {
    return repository.post(`${resource}/${uid}/study-elements/create`, data)
  },
  editStudyElement (uid, elementUid, data) {
    return repository.patch(`${resource}/${uid}/study-elements/${elementUid}`, data)
  },
  deleteStudyElement (uid, elementUid) {
    return repository.delete(`${resource}/${uid}/study-elements/${elementUid}`)
  },
  getStudyElementsAllowedConfigs () {
    return repository.get(`${resource}/study-elements/allowed-element-configs`)
  },
  getAllStudyCells (uid) {
    return repository.get(`${resource}/${uid}/study-design-cells`)
  },
  createStudyCell (uid, data) {
    return repository.post(`${resource}/${uid}/study-design-cells`, data)
  },
  updateStudyCell (uid, cellUid, data) {
    return repository.patch(`${resource}/${uid}/study-design-cells/${cellUid}`, data)
  },
  deleteStudyCell (uid, cellUid) {
    return repository.delete(`${resource}/${uid}/study-design-cells/${cellUid}`)
  },
  getAllBranchArms (uid, options) {
    const params = {
      ...options
    }
    return repository.get(`${resource}/${uid}/study-branch-arms`, { params })
  },
  createBranchArm (uid, data) {
    return repository.post(`${resource}/${uid}/study-branch-arms/create`, data)
  },
  editBranchArm (uid, branchArmUid, data) {
    return repository.patch(`${resource}/${uid}/study-branch-arms/${branchArmUid}`, data)
  },
  deleteBranchArm (uid, branchArmUid) {
    return repository.delete(`${resource}/${uid}/study-branch-arms/${branchArmUid}`)
  },
  updateBranchArmOrder (uid, branchArmUid, data) {
    return repository.patch(`${resource}/${uid}/study-branch-arms/${branchArmUid}/order`, data)
  },
  updateArmOrder (uid, armUid, data) {
    return repository.patch(`${resource}/${uid}/study-arms/${armUid}/order`, data)
  },
  updateElementOrder (uid, elementUid, data) {
    return repository.patch(`${resource}/${uid}/study-elements/${elementUid}/order`, data)
  },
  getAllBranchesForArm (uid, armUid) {
    return repository.get(`${resource}/${uid}/study-branch-arms/arm/${armUid}`)
  },
  getAllCohorts (uid, options) {
    const params = {
      ...options
    }
    return repository.get(`${resource}/${uid}/study-cohorts`, { params })
  },
  getAllCohortsForArm (uid, armUid) {
    const params = { armUid: armUid }
    return repository.get(`${resource}/${uid}/study-cohorts`, { params })
  },
  createCohort (uid, data) {
    return repository.post(`${resource}/${uid}/study-cohorts/create`, data)
  },
  editCohort (uid, cohortUid, data) {
    return repository.patch(`${resource}/${uid}/study-cohorts/${cohortUid}`, data)
  },
  updateCohortOrder (uid, cohortUid, data) {
    return repository.patch(`${resource}/${uid}/study-cohorts/${cohortUid}/order`, data)
  },
  deleteCohort (uid, cohortUid) {
    return repository.delete(`${resource}/${uid}/study-cohorts/${cohortUid}`)
  },
  cellsBatchUpdate (uid, data) {
    return repository.post(`${resource}/${uid}/study-design-cells/batch`, data)
  },
  getAllCellsForArm (uid, armUid) {
    return repository.get(`${resource}/${uid}/study-design-cells/arm/${armUid}`)
  },
  getAllCellsForBranch (uid, branchArmUid) {
    return repository.get(`${resource}/${uid}/study-design-cells/branch-arm/${branchArmUid}`)
  },
  getStudyCohortVersions (studyUid, studyCohortUid) {
    return repository.get(`${resource}/${studyUid}/study-cohorts/${studyCohortUid}/audit-trail`)
  },
  getStudyElementVersions (studyUid, studyElementUid) {
    return repository.get(`${resource}/${studyUid}/study-elements/${studyElementUid}/audit-trail`)
  },
  getStudyCohortsVersions (studyUid) {
    return repository.get(`${resource}/${studyUid}/study-cohort/audit-trail`)
  },
  getStudyElementsVersions (studyUid) {
    return repository.get(`${resource}/${studyUid}/study-element/audit-trail`)
  }
}
