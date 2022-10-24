import dictionaries from '@/api/dictionaries'

const state = {
  substances: []
}

const getters = {
  substances: state => state.substances
}

const mutations = {
  SET_SUBSTANCES (state, substances) {
    state.substances = substances
  }
}

const actions = {
  fetchSubstances ({ commit }) {
    return dictionaries.getSubstances().then(resp => {
      commit('SET_SUBSTANCES', resp.data.items)
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
