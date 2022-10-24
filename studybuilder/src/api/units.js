import repository from './repository'

const resource = 'concepts/unit-definitions'

export default {
  get (params) {
    return repository.get(`${resource}`, params)
  },
  getByDimension (dimension) {
    const params = { dimension: dimension }
    return repository.get(`${resource}`, { params })
  },
  getBySubset (subset) {
    const params = { subset: subset, sortBy: { conversionFactorToMaster: true } }
    return repository.get(`${resource}`, { params })
  },
  create (data) {
    return repository.post(`${resource}`, data)
  },
  edit (uid, data) {
    return repository.patch(`${resource}/${uid}`, data)
  },
  delete (uid) {
    return repository.delete(`${resource}/${uid}`)
  },
  newVersion (uid) {
    return repository.post(`${resource}/${uid}/new-version`)
  },
  approve (uid) {
    return repository.post(`${resource}/${uid}/approve`)
  },
  inactivate (uid) {
    return repository.post(`${resource}/${uid}/inactivate`)
  },
  reactivate (uid) {
    return repository.post(`${resource}/${uid}/reactivate`)
  }
}
