import Vue from 'vue'
import objectives from '@/api/objectives'

const state = {
  objectives: []
}

const getters = {
  objectives: state => state.objectives
}

const mutations = {
  SET_OBJECTIVES (state, objectives) {
    state.objectives = objectives
  },
  ADD_OBJECTIVE (state, objective) {
    state.objectives.unshift(objective)
  },
  UPDATE_OBJECTIVE (state, objective) {
    state.objectives.filter((item, pos) => {
      if (item.uid === objective.uid) {
        Vue.set(state.objectives, pos, objective)
      }
    })
  },
  REMOVE_OBJECTIVE (state, objective) {
    state.objectives = state.objectives.filter(function (item) {
      return item.uid !== objective.uid
    })
  }
}

const actions = {
  fetchObjectives ({ commit }) {
    return objectives.get().then(resp => {
      commit('SET_OBJECTIVES', resp.data.items)
    })
  },
  fetchFilteredObjectives ({ commit }, data) {
    return objectives.getFiltered(data).then(resp => {
      commit('SET_OBJECTIVES', resp.data.items)
    })
  },
  addObjective ({ commit }, data) {
    return objectives.create(data).then(resp => {
      commit('ADD_OBJECTIVE', resp.data)
    })
  },
  updateObjective ({ commit }, { uid, data }) {
    return objectives.update(uid, data).then(resp => {
      commit('UPDATE_OBJECTIVE', resp.data)
    })
  },
  approveObjective ({ commit }, objective) {
    return objectives.approve(objective.uid).then(resp => {
      commit('UPDATE_OBJECTIVE', resp.data)
    })
  },
  inactivateObjective ({ commit }, objective) {
    return objectives.inactivate(objective.uid).then(resp => {
      commit('UPDATE_OBJECTIVE', resp.data)
    })
  },
  reactivateObjective ({ commit }, objective) {
    return objectives.reactivate(objective.uid).then(resp => {
      commit('UPDATE_OBJECTIVE', resp.data)
    })
  },
  deleteObjective ({ commit }, objective) {
    return objectives.deleteObject(objective.uid).then(resp => {
      commit('REMOVE_OBJECTIVE', objective)
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
