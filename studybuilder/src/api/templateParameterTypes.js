import repository from './repository'

const resource = 'template-parameters'

export default {
  getTypes () {
    return repository.get(`/${resource}`)
  },
  getValues (templateParameterName) {
    return repository.get(`${resource}/${templateParameterName}/values`)
  }
}
