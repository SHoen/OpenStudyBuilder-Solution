import Vue from 'vue'
import concepts from '@/api/concepts'
import pconstants from '@/constants/parameters'

/*
** Check if parameter is a constant (text or number) and format it properly
*/
async function formatConstantParameterValue (parameter) {
  const result = { ...parameter }
  let resp = null

  if (parameter.selectedValues && !Array.isArray(parameter.selectedValues)) {
    if (parameter.name === pconstants.NUM_VALUE) {
      const numData = {
        value: parameter.selectedValues,
        libraryName: 'Sponsor',
        templateParameter: true
      }
      resp = await concepts.create(numData, 'numeric-values')
    } else if (parameter.name === pconstants.TEXT_VALUE) {
      const textData = {
        name: parameter.selectedValues,
        nameSentenceCase: parameter.selectedValues.toLowerCase(),
        libraryName: 'Sponsor',
        templateParameter: true
      }
      resp = await concepts.create(textData, 'text-values')
    }
    if (resp) {
      result.selectedValues = []
      result.selectedValues[0] = {
        name: resp.data.name,
        type: result.name,
        uid: resp.data.uid
      }
    }
  }
  return result
}

/*
** Format parameter values in a way compatible with what API expects.
*/
async function formatParameterValues (parameters, onlyDefaultValues) {
  const result = []
  let position = 1

  for (let parameter of parameters) {
    if (onlyDefaultValues && !parameter.saveAsDefault) {
      position += 1
      continue
    }
    let conjunction = ''
    if (parameter.selectedSeparator) {
      conjunction = parameter.selectedSeparator.trim()
    }
    let index = 1
    const values = []
    const value = null

    parameter = await formatConstantParameterValue(parameter)
    if (parameter.selectedValues.length || !onlyDefaultValues) {
      parameter.selectedValues.forEach(value => {
        values.push({
          index: index,
          type: parameter.name,
          name: value.name,
          uid: value.uid
        })
        index += 1
      })
      result.push({
        position: position,
        conjunction: conjunction,
        values: values,
        value: value
      })
    }
    position += 1
  }
  return result
}

function getSeparator (conjunction) {
  if (conjunction === ',') {
    return ', '
  }
  return ' ' + conjunction + ' '
}

/*
** Load parameter values received from the API
*/
function loadParameterValues (parameterValues, parameters, fromDefaultParameterValues) {
  let index = 0
  parameterValues.forEach(item => {
    if (item.values.length) {
      item.values.forEach(value => {
        if (value.type === pconstants.NUM_VALUE || value.type === pconstants.TEXT_VALUE) {
          Object.assign(parameters[index], { selectedSeparator: '', selectedValues: value.name })
        } else {
          Vue.set(parameters[index], 'selectedSeparator', getSeparator(item.conjunction))
          if (parameters[index].selectedValues) {
            parameters[index].selectedValues.push({
              name: value.name,
              uid: value.uid,
              type: value.type
            })
          } else {
            Vue.set(parameters[index], 'selectedValues', [{
              name: value.name,
              uid: value.uid,
              type: value.type
            }])
          }
        }
        if (fromDefaultParameterValues) {
          Vue.set(parameters[index], 'saveAsDefault', true)
        }
      })
    } else if (!fromDefaultParameterValues) {
      Vue.set(parameters[index], 'skip', true)
      Vue.set(parameters[index], 'selectedValues', [])
    }
    index += 1
  })
}

export default {
  formatParameterValues,
  loadParameterValues
}
