
import repository from './repository'

const resource = 'study'

export default {
  getFilteredEpochs (studyUid, params) {
    return repository.get(`${resource}/${studyUid}/study-epochs`, { params })
  },
  getStudyEpochs (studyUid) {
    return repository.get(`${resource}/${studyUid}/study-epochs`)
  },
  getStudyVisits (studyUid, options) {
    const params = {
      ...options
    }
    return repository.get(`${resource}/${studyUid}/study-visits`, { params })
  },
  getAmountOfVisitsInStudyEpoch (studyUid, studyEpochUid) {
    return repository.get(`${resource}/${studyUid}/get-amount-of-visits-in-epoch/${studyEpochUid}`)
  },
  getGlobalAnchorVisit (studyUid) {
    return repository.get(`${resource}/${studyUid}/global-anchor-visit`)
  },
  getAnchorVisitsInGroupOfSubvisits (studyUid) {
    return repository.get(`${resource}/${studyUid}/anchor-visits-in-group-of-subvisits`)
  },
  addStudyVisit (studyUid, data) {
    return repository.post(`${resource}/${studyUid}/study-visits`, data)
  },
  getStudyVisitPreview (studyUid, data) {
    return repository.post(`${resource}/${studyUid}/study-visits/preview`, data)
  },
  updateStudyVisit (studyUid, studyVisitUid, data) {
    return repository.patch(`${resource}/${studyUid}/study-visits/${studyVisitUid}`, data)
  },
  deleteStudyVisit (studyUid, studyVisitUid) {
    return repository.delete(`${resource}/${studyUid}/study-visits/${studyVisitUid}`)
  },
  getStudyVisitVersions (studyUid, studyVisitUid) {
    return repository.get(`${resource}/${studyUid}/study-visits/${studyVisitUid}/audit-trail`)
  },
  getGroups (studyUid) {
    return repository.get(`${resource}/${studyUid}/allowed-consecutive-groups`)
  },
  reorderStudyEpoch (studyUid, studyEpochUid, order) {
    return repository.patch(`${resource}/${studyUid}/study-epochs/${studyEpochUid}/order/${order}`)
  },
  addStudyEpoch (studyUid, data) {
    return repository.post(`${resource}/${studyUid}/study-epochs`, data)
  },
  updateStudyEpoch (studyUid, studyEpochUid, data) {
    return repository.patch(`${resource}/${studyUid}/study-epochs/${studyEpochUid}`, data)
  },
  deleteStudyEpoch (studyUid, studyEpochUid, data) {
    return repository.delete(`${resource}/${studyUid}/study-epochs/${studyEpochUid}`)
  },
  getStudyEpochVersions (studyUid, studyEpochUid) {
    return repository.get(`${resource}/${studyUid}/study-epochs/${studyEpochUid}/audit-trail`)
  },
  getStudyArmVersions (studyUid, studyArmUid) {
    return repository.get(`${resource}/${studyUid}/study-arms/${studyArmUid}/audit-trail`)
  },
  getStudyBranchVersions (studyUid, studyBranchUid) {
    return repository.get(`${resource}/${studyUid}/study-branch-arms/${studyBranchUid}/audit-trail`)
  },
  getAllowedConfigs () {
    return repository.get(`${resource}/epochs/allowed-configs`)
  },
  getPreviewEpoch (studyUid, data) {
    return repository.post(`${resource}/${studyUid}/study-epochs/preview`, data)
  },
  getAllowedVisitTypes (data) {
    const params = {
      ...data
    }
    return repository.get(`${resource}/study-visits/allowed-visit-types`, { params })
  },
  getStudyArmsVersions (studyUid) {
    return repository.get(`${resource}/${studyUid}/study-arms/audit-trail`)
  },
  getStudyBranchesVersions (studyUid) {
    return repository.get(`${resource}/${studyUid}/study-branch-arm/audit-trail`)
  },
  getStudyVisitsVersions (studyUid) {
    return repository.get(`${resource}/${studyUid}/study-visits/audit-trail`)
  }
}
