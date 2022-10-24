import Vue from 'vue'
import endpoints from '@/api/endpoints'

const state = {
  endpoints: []
}

const getters = {
  endpoints: state => state.endpoints
}

const mutations = {
  SET_ENDPOINTS (state, endpoints) {
    state.endpoints = endpoints
  },
  ADD_ENDPOINT (state, endpoint) {
    state.endpoints.unshift(endpoint)
  },
  UPDATE_ENDPOINT (state, endpoint) {
    state.endpoints.filter((item, pos) => {
      if (item.uid === endpoint.uid) {
        Vue.set(state.endpoints, pos, endpoint)
      }
    })
  },
  REMOVE_ENDPOINT (state, endpoint) {
    state.endpoints = state.endpoints.filter(function (item) {
      return item.uid !== endpoint.uid
    })
  }
}

const actions = {
  fetchEndpoints ({ commit }) {
    return endpoints.get().then(resp => {
      commit('SET_ENDPOINTS', resp.data.items)
    })
  },
  fetchFilteredEndpoints ({ commit }, data) {
    return endpoints.getFiltered(data).then(resp => {
      commit('SET_ENDPOINTS', resp.data.items)
    })
  },
  addEndpoint ({ commit }, data) {
    return endpoints.create(data).then(resp => {
      commit('ADD_ENDPOINT', resp.data)
    })
  },
  updateEndpoint ({ commit }, { uid, data }) {
    return endpoints.update(uid, data).then(resp => {
      commit('UPDATE_ENDPOINT', resp.data)
    })
  },
  approveEndpoint ({ commit }, endpoint) {
    return endpoints.approve(endpoint.uid).then(resp => {
      commit('UPDATE_ENDPOINT', resp.data)
    })
  },
  inactivateEndpoint ({ commit }, endpoint) {
    return endpoints.inactivate(endpoint.uid).then(resp => {
      commit('UPDATE_ENDPOINT', resp.data)
    })
  },
  reactivateEndpoint ({ commit }, endpoint) {
    return endpoints.reactivate(endpoint.uid).then(resp => {
      commit('UPDATE_ENDPOINT', resp.data)
    })
  },
  deleteEndpoint ({ commit }, endpoint) {
    return endpoints.deleteObject(endpoint.uid).then(resp => {
      commit('REMOVE_ENDPOINT', endpoint)
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
