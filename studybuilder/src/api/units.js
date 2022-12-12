import repository from './repository'

const resource = 'concepts/unit-definitions'

export default {
  get (params) {
    return repository.get(`${resource}`, params)
  },
  getByDimension (dimension) {
    const params = { dimension: dimension, page_size: 0 }
    return repository.get(`${resource}`, { params })
  },
  getBySubset (subset) {
    const params = { subset: subset, sort_by: { conversion_factor_to_master: true }, page_size: 0 }
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
    return repository.post(`${resource}/${uid}/versions`)
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
