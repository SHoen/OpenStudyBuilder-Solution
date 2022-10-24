import repository from './repository'

const resource = 'listings/studies'

export default {
  getAllSdtm (uid, options, type) {
    const params = {
      ...options
    }
    return repository.get(`${resource}/all/SDTM/${type}/${uid}`, { params })
  }
}
