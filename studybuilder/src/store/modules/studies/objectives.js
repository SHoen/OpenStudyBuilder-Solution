import Vue from 'vue'
import objectives from '@/api/objectives'
import study from '@/api/study'
import instances from '@/utils/instances'
import utils from '@/store/utils'

const state = {
  studyObjectives: []
}

const getters = {
  studyObjectives: state => state.studyObjectives
}

const mutations = {
  SET_STUDY_OBJECTIVES (state, studyObjectives) {
    state.studyObjectives = studyObjectives
  },
  ADD_STUDY_OBJECTIVE (state, studyObjective) {
    state.studyObjectives.unshift(studyObjective)
  },
  UPDATE_STUDY_OBJECTIVE (state, studyObjective) {
    state.studyObjectives.filter((item, pos) => {
      if (item.studyObjectiveUid === studyObjective.studyObjectiveUid) {
        Vue.set(state.studyObjectives, pos, studyObjective)
      }
    })
  },
  REMOVE_STUDY_OBJECTIVE (state, studyObjectiveUid) {
    state.studyObjectives = state.studyObjectives.filter(function (item) {
      return item.studyObjectiveUid !== studyObjectiveUid
    })
  }
}

const actions = {
  fetchStudyObjectives ({ commit }, data) {
    return study.getStudyObjectives(data.studyUid, data).then(resp => {
      commit('SET_STUDY_OBJECTIVES', resp.data.items)
      return resp
    })
  },
  /*
  ** Create a study objective based on an objective template. We fist
  ** look if an objective already exists for the provided name. If so,
  ** we select it, otherwise we create a new objective in Final state
  ** and select if.
  */
  async addStudyObjectiveFromTemplate ({ commit, dispatch }, { studyUid, form, parameters }) {
    const objective = {
      objectiveTemplateUid: form.objectiveTemplate.uid,
      parameterValues: await instances.formatParameterValues(parameters),
      libraryName: form.objectiveTemplate.library.name
    }
    const objectiveLevelUid = (form.objectiveLevel) ? form.objectiveLevel.termUid : undefined
    const data = {
      objectiveLevelUid,
      objectiveData: objective
    }
    return study.createStudyObjective(studyUid, data).then(() => {
      dispatch('fetchStudyObjectives', { studyUid })
    })
  },
  addStudyObjective ({ commit, dispatch }, { studyUid, objectiveUid, objectiveLevelUid }) {
    return study.selectStudyObjective(studyUid, objectiveUid, objectiveLevelUid).then(() => {
      dispatch('fetchStudyObjectives', { studyUid })
    })
  },
  async updateStudyObjective ({ commit, dispatch }, { studyUid, studyObjectiveUid, form }) {
    const data = {}
    if (form.objectiveLevel) {
      data.objectiveLevelUid = form.objectiveLevel.termUid
    }
    if (form.parameters !== undefined) {
      let objectiveUid = null
      try {
        const searchName = utils.getInternalApiName(form.objective.objectiveTemplate.name, form.parameters)
        const response = await objectives.getObjectByName(searchName)
        objectiveUid = response.data.uid
      } catch (error) {
        const objective = {
          objectiveTemplateUid: form.objective.objectiveTemplate.uid,
          parameterValues: await instances.formatParameterValues(form.parameters),
          libraryName: form.objectiveTemplate ? form.objectiveTemplate.library.name : form.objective.library.name
        }
        const resp = await objectives.create(objective)
        objectiveUid = resp.data.uid
        await objectives.approve(objectiveUid)
      }
      data.objectiveUid = objectiveUid
    }
    await study.updateStudyObjective(studyUid, studyObjectiveUid, data)
    dispatch('fetchStudyObjectives', { studyUid })
  },
  async updateStudyObjectiveLatestVersion ({ commit }, { studyUid, studyObjectiveUid }) {
    const resp = await study.updateStudyObjectiveLatestVersion(
      studyUid, studyObjectiveUid
    )
    commit('UPDATE_STUDY_OBJECTIVE', resp.data)
  },
  async updateStudyObjectiveAcceptVersion ({ commit }, { studyUid, studyObjectiveUid }) {
    const resp = await study.updateStudyObjectiveAcceptVersion(
      studyUid, studyObjectiveUid
    )
    commit('UPDATE_STUDY_OBJECTIVE', resp.data)
  },
  deleteStudyObjective ({ commit }, { studyUid, studyObjectiveUid }) {
    return study.deleteStudyObjective(studyUid, studyObjectiveUid).then(resp => {
      commit('REMOVE_STUDY_OBJECTIVE', studyObjectiveUid)
    })
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
