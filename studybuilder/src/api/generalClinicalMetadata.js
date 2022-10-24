import repository from './repository'

const resource = 'listings/libraries/all/gcmd'

export default {
  get (value, params) {
    return repository.get(`${resource}/${value}`, { params })
  }
}
