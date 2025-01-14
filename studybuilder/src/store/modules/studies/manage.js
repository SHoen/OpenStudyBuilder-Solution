import Vue from 'vue'
import study from '@/api/study'

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
    return state.projects.find(project => project.project_number === number)
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
        return true
      }
      return false
    })
  },
  SET_PROJECTS (state, projects) {
    state.projects = projects
  }
}

const actions = {
  fetchStudies ({ commit }) {
    return study.getAll().then(resp => {
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
      resp.data.items.sort(function (a, b) {
        return a.name.toLowerCase().localeCompare(b.name.toLowerCase())
      })
      commit('SET_PROJECTS', resp.data.items)
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
