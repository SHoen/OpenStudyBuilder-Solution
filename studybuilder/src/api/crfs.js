import repository from './repository'

const resource = 'concepts/odms'

export default {
  get (source, params) {
    if (!source) {
      return repository.get(`${resource}`, params)
    }

    return repository.get(`${resource}/${source}`, params)
  },
  reactivate (source, uid) {
    return repository.post(`${resource}/${source}/${uid}/reactivate`)
  },
  inactivate (source, uid) {
    return repository.post(`${resource}/${source}/${uid}/inactivate`)
  },
  newVersion (source, uid) {
    return repository.post(`${resource}/${source}/${uid}/new-version`)
  },
  approve (source, uid) {
    return repository.post(`${resource}/${source}/${uid}/approve`)
  },
  delete (source, uid) {
    return repository.delete(`${resource}/${source}/${uid}`)
  },
  createForm (data) {
    return repository.post(`${resource}/forms/create`, data)
  },
  updateForm (data, uid) {
    return repository.patch(`${resource}/forms/${uid}/update`, data)
  },
  batchCreateDescription (data) {
    return repository.post(`${resource}/descriptions/batch`, data)
  },
  createAlias (data) {
    return repository.post(`${resource}/aliases`, data)
  },
  getAliases () {
    return repository.get(`${resource}/aliases`)
  },
  getForm (uid) {
    return repository.get(`${resource}/forms/${uid}`)
  },
  createItemGroup (data) {
    return repository.post(`${resource}/item-groups/create`, data)
  },
  updateItemGroup (data, uid) {
    return repository.patch(`${resource}/item-groups/${uid}/update`, data)
  },
  getItemGroup (uid) {
    return repository.get(`${resource}/item-groups/${uid}`)
  },
  getFormAuditTrail (uid) {
    return repository.get(`${resource}/forms/${uid}/versions`)
  },
  getGroupAuditTrail (uid) {
    return repository.get(`${resource}/item-groups/${uid}/versions`)
  },
  createItem (data) {
    return repository.post(`${resource}/items/create`, data)
  },
  updateItem (data, uid) {
    return repository.patch(`${resource}/items/${uid}/update`, data)
  },
  getItem (uid) {
    return repository.get(`${resource}/items/${uid}`)
  },
  getItemAuditTrail (uid) {
    return repository.get(`${resource}/items/${uid}/versions`)
  },
  getTemplate (uid) {
    return repository.get(`${resource}/templates/${uid}`)
  },
  createTemplate (data) {
    return repository.post(`${resource}/templates`, data)
  },
  updateTemplate (data, uid) {
    return repository.patch(`${resource}/templates/${uid}`, data)
  },
  addFormsToTemplate (data, uid, sync) {
    return repository.post(`${resource}/templates/${uid}/add-forms?override=${sync}`, data)
  },
  addItemGroupsToForm (data, uid, sync) {
    return repository.post(`${resource}/forms/${uid}/add-item-groups?override=${sync}`, data)
  },
  addItemsToItemGroup (data, uid, sync) {
    return repository.post(`${resource}/item-groups/${uid}/add-items?override=${sync}`, data)
  },
  overwriteFormsInTemplate (data, uid) {
    return repository.post(`${resource}/templates/${uid}/forms`, data)
  },
  overwriteItemGroupsInForm (data, uid) {
    return repository.post(`${resource}/forms/${uid}/item-groups`, data)
  },
  overwriteItemsInItemGroup (data, uid) {
    return repository.post(`${resource}/item-groups/${uid}/items`, data)
  },
  addActivityGroupsToForm (data, uid) {
    return repository.post(`${resource}/forms/${uid}/add-activity-groups?override=true`, data)
  },
  addActivitySubGroupsToItemGroup (data, uid) {
    return repository.post(`${resource}/item-groups/${uid}/add-activity-sub-groups?override=true`, data)
  },
  addActivitiesToItem (data, uid) {
    return repository.post(`${resource}/items/${uid}/add-activities?override=true`, data)
  },
  getXml (params) {
    return repository.get(`${resource}/metadata/xmls`, { params: params, responseType: 'document' })
  },
  getXmlToDownload (params) {
    return repository.get(`${resource}/metadata/xmls`, { params })
  },
  getAllAliases (params) {
    return repository.get(`${resource}/aliases`, { params })
  },
  deleteAlias (uid) {
    return repository.delete(`${resource}/aliases/${uid}`)
  },
  addAlias (data) {
    return repository.post(`${resource}/aliases`, data)
  },
  editAlias (uid, data) {
    return repository.patch(`${resource}/aliases/${uid}`, data)
  },
  getDescriptions () {
    return repository.get(`${resource}/descriptions`)
  },
  getExpressions () {
    return repository.get(`${resource}/formal-expressions`)
  },
  createExpression (data) {
    return repository.post(`${resource}/formal-expressions`, data)
  },
  editExpression (uid, data) {
    return repository.patch(`${resource}/formal-expressions/${uid}`, data)
  },
  deleteExpression (uid) {
    return repository.delete(`${resource}/formal-expressions/${uid}`)
  },
  getConditionByOid (params) {
    return repository.get(`${resource}/conditions`, { params })
  },
  createCondition (data) {
    return repository.post(`${resource}/conditions/create`, data)
  },
  editCondition (uid, data) {
    return repository.patch(`${resource}/conditions/${uid}/update`, data)
  },
  deleteCondition (uid) {
    return repository.delete(`${resource}/conditions/${uid}`)
  },
  getFormRelationship (uid) {
    return repository.get(`${resource}/forms/${uid}/relationships`)
  },
  getGroupRelationship (uid) {
    return repository.get(`${resource}/item-groups/${uid}/relationships`)
  },
  getItemRelationship (uid) {
    return repository.get(`${resource}/items/${uid}/relationships`)
  }
}
