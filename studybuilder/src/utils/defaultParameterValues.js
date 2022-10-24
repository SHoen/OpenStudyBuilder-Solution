function hasDefaultParameterValues (template) {
  for (const setNumber in template.defaultParameterValues) {
    for (const parameterValue of template.defaultParameterValues[setNumber]) {
      if (parameterValue.values.length) {
        return true
      }
    }
  }
  return false
}

export default {
  hasDefaultParameterValues
}
