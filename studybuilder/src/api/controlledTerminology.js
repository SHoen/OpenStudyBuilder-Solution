import repository from './repository'

const resource = 'ct'

export default {
  getCatalogues () {
    return repository.get(`${resource}/catalogues`)
  },
  getPackages () {
    return repository.get(`${resource}/packages`)
  },
  getPackagesDates (catalogueName) {
    const params = { catalogue_name: catalogueName }
    return repository.get(`${resource}/packages/dates`, { params })
  },
  getPackagesChanges (catalogueName, fromDate, toDate) {
    const params = { catalogue_name: catalogueName, old_package_date: fromDate, new_package_date: toDate }
    return repository.get(`${resource}/packages/changes`, { params })
  },
  getPackagesCodelistChanges (codelistUid, catalogueName, fromDate, toDate) {
    const params = { catalogue_name: catalogueName, old_package_date: fromDate, new_package_date: toDate }
    return repository.get(`${resource}/packages/${codelistUid}/changes`, { params })
  },
  getCodelists (options) {
    const params = {
      ...options
    }
    if (params.size === -1) {
      params.size = 1000
    }
    return repository.get(`${resource}/codelists`, { params })
  },
  getCodelistNames (codelistUid) {
    return repository.get(`${resource}/codelists/${codelistUid}/names`)
  },
  getCodelistNamesVersions (codelistUid) {
    return repository.get(`${resource}/codelists/${codelistUid}/names/versions`)
  },
  updateCodelistNames (codelistUid, data) {
    return repository.patch(`${resource}/codelists/${codelistUid}/names`, data)
  },
  newCodelistNamesVersion (codelistUid) {
    return repository.post(`${resource}/codelists/${codelistUid}/names/new-version`)
  },
  approveCodelistNames (codelistUid) {
    return repository.post(`${resource}/codelists/${codelistUid}/names/approve`)
  },
  getCodelistAttributes (codelistUid) {
    return repository.get(`${resource}/codelists/${codelistUid}/attributes`)
  },
  getCodelistAttributesVersions (codelistUid) {
    return repository.get(`${resource}/codelists/${codelistUid}/attributes/versions`)
  },
  newCodelistAttributesVersion (codelistUid) {
    return repository.post(`${resource}/codelists/${codelistUid}/attributes/new-version`)
  },
  approveCodelistAttributes (codelistUid) {
    return repository.post(`${resource}/codelists/${codelistUid}/attributes/approve`)
  },
  getCodelistTerms (params) {
    return repository.get(`${resource}/terms`, { params })
  },
  getCodelistTermsNames (params) {
    return repository.get(`${resource}/terms/names`, { params })
  },
  getCodelistTermNames (termUid) {
    return repository.get(`${resource}/terms/${termUid}/names`)
  },
  newCodelistTermNamesVersion (termUid) {
    return repository.post(`${resource}/terms/${termUid}/names/new-version`)
  },
  approveCodelistTermNames (termUid) {
    return repository.post(`${resource}/terms/${termUid}/names/approve`)
  },
  inactivateCodelistTermNames (termUid) {
    return repository.post(`${resource}/terms/${termUid}/names/inactivate`)
  },
  reactivateCodelistTermNames (termUid) {
    return repository.post(`${resource}/terms/${termUid}/names/reactivate`)
  },
  deleteCodelistTermNames (termUid) {
    return repository.delete(`${resource}/terms/${termUid}/names`)
  },
  getCodelistTermsAttributes (codelistUid, options) {
    const params = {
      ...options,
      codelist_uid: codelistUid
    }
    return repository.get(`${resource}/terms/attributes`, { params })
  },
  getCodelistTermAttributes (termUid) {
    return repository.get(`${resource}/terms/${termUid}/attributes`)
  },
  newCodelistTermAttributesVersion (termUid) {
    return repository.post(`${resource}/terms/${termUid}/attributes/new-version`)
  },
  approveCodelistTermAttributes (termUid) {
    return repository.post(`${resource}/terms/${termUid}/attributes/approve`)
  },
  inactivateCodelistTermAttributes (termUid) {
    return repository.post(`${resource}/terms/${termUid}/attributes/inactivate`)
  },
  reactivateCodelistTermAttributes (termUid) {
    return repository.post(`${resource}/terms/${termUid}/attributes/reactivate`)
  },
  deleteCodelistTermAttributes (termUid) {
    return repository.delete(`${resource}/terms/${termUid}/attributes`)
  },
  createCodelistTerm (data) {
    return repository.post(`${resource}/terms`, data)
  },
  addTermToCodelist (codelistUid, termUid) {
    const data = {
      termUid,
      order: 999999
    }
    return repository.post(`${resource}/codelists/${codelistUid}/add-term`, data)
  },
  removeTermFromCodelist (codelistUid, termUid) {
    const data = {
      termUid,
      order: 999999
    }
    return repository.post(`${resource}/codelists/${codelistUid}/remove-term`, data)
  },
  updateCodelistTermNames (termUid, data) {
    return repository.patch(`${resource}/terms/${termUid}/names`, data)
  },
  updateCodelistTermAttributes (termUid, data) {
    return repository.patch(`${resource}/terms/${termUid}/attributes`, data)
  },
  updateCodelistAttributes (codelistUid, data) {
    return repository.patch(`${resource}/codelists/${codelistUid}/attributes`, data)
  },
  createCodelist (data) {
    return repository.post(`${resource}/codelists`, data)
  },
  getStats () {
    return repository.get(`${resource}/stats`)
  }
}
