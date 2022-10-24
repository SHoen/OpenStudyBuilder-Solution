import Vue from 'vue'
import study from '@/api/study'
import constants from '@/constants/study'

const state = {
  studies: {
    items: []
  },
  projects: []
}

const getters = {
  studies: state => state.studies,
  projects: state => state.projects,
  getProjectByNumber: state => number => {
    return state.projects.find(project => project.projectNumber === number)
  }
}

const mutations = {
  SET_STUDIES (state, studies) {
    state.studies = studies
  },
  ADD_STUDY (state, study) {
    state.studies.items.unshift(study)
  },
  UPDATE_STUDY (state, study) {
    state.studies.items.filter((item, pos) => {
      if (item.uid === study.uid) {
        Vue.set(state.studies.items, pos, study)
      }
    })
  },
  SET_PROJECTS (state, projects) {
    state.projects = projects
  }
}

const actions = {
  fetchStudies ({ commit }) {
    return study.getAll([`${constants.IDENTIFICATION_METADATA}`, `${constants.VERSION_METADATA}`, `${constants.DESCRIPTION_METADATA}`]).then(resp => {
      commit('SET_STUDIES', resp.data)
    })
  },
  addStudy ({ commit }, data) {
    return new Promise((resolve, reject) => {
      study.create(data).then(resp => {
        commit('ADD_STUDY', resp.data)
        resolve(resp)
      }).catch(error => {
        reject(error)
      })
    })
  },
  editStudyIdentification ({ commit }, [uid, data]) {
    return new Promise((resolve, reject) => {
      study.updateIdentification(uid, data).then(resp => {
        commit('UPDATE_STUDY', resp.data)
        resolve(resp)
      }).catch(error => {
        reject(error)
      })
    })
  },
  editStudyType ({ commit }, [uid, data]) {
    return study.updateStudyType(uid, data)
  },
  editStudyPopulation ({ commit }, [uid, data]) {
    return study.updateStudyPopulation(uid, data)
  },
  updateStudyIntervention ({ commit }, [uid, data]) {
    return study.updateStudyIntervention(uid, data)
  },
  fetchProjects ({ commit }) {
    return study.projects_all().then(resp => {
      commit('SET_PROJECTS', resp.data)
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
