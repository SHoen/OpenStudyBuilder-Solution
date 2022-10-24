export const parameterValuesMixin = {
  methods: {
    /*
    ** Compute name preview based on given template and parameters.
    */
    getNamePreview (template, parameters) {
      if (!parameters.length) {
        return ''
      }
      let result = ''
      let paramIndex = 0
      let inParam = false
      for (const c of template) {
        if (c === '[') {
          inParam = true
        } else if (c === ']') {
          if (parameters[paramIndex].selectedValues && parameters[paramIndex].selectedValues.length) {
            const valueNames = parameters[paramIndex].selectedValues.map(v => v.name)
            const concatenation = (parameters[paramIndex].selectedSeparator)
              ? valueNames.join(parameters[paramIndex].selectedSeparator)
              : valueNames.join(' ')
            result += `[${concatenation}]`
          } else {
            result += `[${parameters[paramIndex].name}]`
          }
          paramIndex++
          inParam = false
        } else if (!inParam) {
          result += c
        }
      }
      return result
    }
  }
}
