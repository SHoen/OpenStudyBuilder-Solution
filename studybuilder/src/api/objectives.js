import api from './libraryObjects'
import repository from './repository'

const basePath = '/objectives'

const objectives = api(basePath)

objectives.getStudies = function (uid) {
  return repository.get(`${basePath}/${uid}/studies`)
}

export default objectives
