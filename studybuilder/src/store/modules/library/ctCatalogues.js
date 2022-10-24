import controlledTerminology from '@/api/controlledTerminology'

const state = {
  catalogues: [],
  currentCataloguePage: 1
}

const getters = {
  catalogues: state => state.catalogues,
  currentCataloguePage: state => state.currentCataloguePage
}

const mutations = {
  SET_CATALOGUES (state, catalogues) {
    state.catalogues = catalogues
  },
  SET_CURRENT_CATALOGUE_PAGE (state, page) {
    state.currentCataloguePage = page
  }
}

const actions = {
  fetchCatalogues ({ commit }) {
    return controlledTerminology.getCatalogues().then(resp => {
      commit('SET_CATALOGUES', resp.data)
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
