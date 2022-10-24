
import repository from './repository'

export default (basePath) => {
  return {
    get (params) {
      const url = `${basePath}`
      return repository.get(url, { params })
    },
    getTemplate (uid) {
      return repository.get(`${basePath}/${uid}`)
    },
    getParameters (uid, params) {
      return repository.get(`${basePath}/${uid}/parameters`, { params })
    },
    getObjectTemplateParameters (uid) {
      return repository.get(`${basePath}/${uid}/parameters`)
    },
    getVersions (uid) {
      return repository.get(`${basePath}/${uid}/versions`)
    },
    create (data) {
      return repository.post(`${basePath}`, data)
    },
    update (uid, data) {
      return repository.patch(`${basePath}/${uid}`, data)
    },
    approve (uid) {
      return repository.post(`${basePath}/${uid}/approve`)
    },
    approveCascade (uid, cascade) {
      return repository.post(`${basePath}/${uid}/approve?cascade=${cascade}`)
    },
    createNewVersion (uid, data) {
      return repository.post(`${basePath}/${uid}/new-version`, data)
    },
    inactivate (uid) {
      return repository.post(`${basePath}/${uid}/inactivate`)
    },
    reactivate (uid) {
      return repository.post(`${basePath}/${uid}/reactivate`)
    },
    delete (uid) {
      return repository.delete(`${basePath}/${uid}`)
    },
    preValidate (data) {
      return repository.post(`${basePath}/pre-validate`, data)
    },
    addDefaultParameterValuesSet (uid, data) {
      return repository.patch(`${basePath}/${uid}/default-parameter-values`, { defaultParameterValues: data })
    },
    editDefaultParameterValuesSet (uid, setNumber, data) {
      return repository.patch(`${basePath}/${uid}/default-parameter-values`, { setNumber, defaultParameterValues: data })
    },
    deleteDefaultParameterValuesSet (uid, setNumber) {
      return repository.patch(`${basePath}/${uid}/default-parameter-values`, { setNumber: parseInt(setNumber), defaultParameterValues: [] })
    },
    updateGroupings (uid, data) {
      return repository.patch(`${basePath}/${uid}/groupings`, data)
    }
  }
}
