import Vue from 'vue'

const state = {
  userInfo: null,
  displayWelcomeMsg: false
}

const getters = {
  userInfo: state => state.userInfo,
  displayWelcomeMsg: state => state.displayWelcomeMsg
}

const mutations = {
  SET_USER_INFO (state, userInfo) {
    state.userInfo = userInfo
  },
  SET_WELCOME_MSG_FLAG (state, value) {
    state.displayWelcomeMsg = value
  }
}

const actions = {
  initialize ({ commit }) {
    Vue.prototype.$auth.getUserInfo().then(userInfo => {
      commit('SET_USER_INFO', userInfo)
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
