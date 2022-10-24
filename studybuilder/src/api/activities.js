import repository from './repository'

const resource = 'concepts/activities'

export default {
  get (options, source) {
    const params = {
      ...options
    }
    return repository.get(`${resource}/${source}`, { params })
  },
  inactivate (uid, source) {
    return repository.post(`${resource}/${source}/${uid}/inactivate`)
  },
  reactivate (uid, source) {
    return repository.post(`${resource}/${source}/${uid}/reactivate`)
  },
  delete (uid, source) {
    return repository.delete(`${resource}/${source}/${uid}`)
  },
  approve (uid, source) {
    return repository.post(`${resource}/${source}/${uid}/approve`)
  },
  newVersion (uid, source) {
    return repository.post(`${resource}/${source}/${uid}/new-version`)
  },
  getCompounds () {
    return repository.get(`${resource}/compounds`)
  },
  getHeaderData (options) {
    const params = {
      ...options
    }
    return repository.get(`${resource}/headers`, { params })
  },
  getGroups () {
    return repository.get(`${resource}/activity-groups`)
  },
  getSubGroups (group) {
    const params = {
      activityGroupUid: group
    }
    return repository.get(`${resource}/activity-sub-groups`, { params })
  },
  getAllGroups (options) {
    const params = {
      ...options
    }
    return repository.get(`${resource}/activity-groups`, { params })
  },
  getAllSubGroups (options) {
    const params = {
      ...options
    }
    return repository.get(`${resource}/activity-sub-groups`, { params })
  },
  getSubGroupActivities (group) {
    const params = {
      activitySubGroupUid: group
    }
    return repository.get(`${resource}/activities`, { params })
  },
  create (data, source) {
    const params = {
      ...data
    }
    return repository.post(`${resource}/${source}`, params)
  },
  update (uid, data, source) {
    const params = {
      ...data
    }
    return repository.patch(`${resource}/${source}/${uid}`, params)
  }
}
