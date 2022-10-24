import repository from './repository'

const resource = 'dictionaries'

export default {
  getSnomedCategories (options) {
    const params = {
      ...options
    }
    return repository.get(`${resource}/codelists/SNOMED`, { params })
  },
  getCodelists (library) {
    return repository.get(`${resource}/codelists/${library}`)
  },
  getTerms (options) {
    const params = {
      ...options
    }
    return repository.get(`${resource}/terms`, { params })
  },
  getSubstances (params) {
    return repository.get(`${resource}/substances`, { params })
  },
  inactivate (uid) {
    return repository.post(`${resource}/terms/${uid}/inactivate`)
  },
  reactivate (uid) {
    return repository.post(`${resource}/terms/${uid}/reactivate`)
  },
  delete (uid) {
    return repository.delete(`${resource}/terms/${uid}`)
  },
  approve (uid) {
    return repository.post(`${resource}/terms/${uid}/approve`)
  },
  newVersion (uid) {
    return repository.post(`${resource}/terms/${uid}/new-version`)
  },
  edit (uid, term) {
    const params = {
      ...term
    }
    return repository.patch(`${resource}/terms/${uid}`, params)
  },
  create (term) {
    const params = {
      ...term
    }
    return repository.post(`${resource}/terms`, params)
  }
}
