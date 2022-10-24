
const state = {
  form: ''
}

const getters = {
  form: state => state.form
}

const mutations = {
  SET_FORM (state, form) {
    state.form = JSON.stringify(form)
  },
  CLEAR_FORM () {
    state.form = ''
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations
}
