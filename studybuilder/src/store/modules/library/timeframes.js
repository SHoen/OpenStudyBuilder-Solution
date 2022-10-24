import Vue from 'vue'
import timeframes from '@/api/timeframes'

const state = {
  timeframes: []
}

const getters = {
  timeframes: state => state.timeframes
}

const mutations = {
  SET_TIMEFRAMES (state, timeframes) {
    state.timeframes = timeframes
  },
  ADD_TIMEFRAME (state, timeframe) {
    state.timeframes.unshift(timeframe)
  },
  UPDATE_TIMEFRAME (state, timeframe) {
    state.timeframes.filter((item, pos) => {
      if (item.uid === timeframe.uid) {
        Vue.set(state.timeframes, pos, timeframe)
      }
    })
  },
  REMOVE_TIMEFRAME (state, timeframe) {
    state.timeframes = state.timeframes.filter(function (item) {
      return item.uid !== timeframe.uid
    })
  }
}

const actions = {
  fetchTimeframes ({ commit }) {
    return timeframes.get().then(resp => {
      commit('SET_TIMEFRAMES', resp.data.items)
    })
  },
  fetchFilteredTimeframes ({ commit }, data) {
    return timeframes.getFiltered(data).then(resp => {
      commit('SET_TIMEFRAMES', resp.data.items)
    })
  },
  addTimeframe ({ commit }, data) {
    return timeframes.create(data).then(resp => {
      commit('ADD_TIMEFRAME', resp.data)
    })
  },
  updateTimeframe ({ commit }, { uid, data }) {
    return timeframes.update(uid, data).then(resp => {
      commit('UPDATE_TIMEFRAME', resp.data)
    })
  },
  approveObject ({ commit }, timeframe) {
    return timeframes.approve(timeframe.uid).then(resp => {
      commit('UPDATE_TIMEFRAME', resp.data)
    })
  },
  inactivateObject ({ commit }, timeframe) {
    return timeframes.inactivate(timeframe.uid).then(resp => {
      commit('UPDATE_TIMEFRAME', resp.data)
    })
  },
  reactivateObject ({ commit }, timeframe) {
    return timeframes.reactivate(timeframe.uid).then(resp => {
      commit('UPDATE_TIMEFRAME', resp.data)
    })
  },
  deleteTimeframe ({ commit }, timeframe) {
    return timeframes.deleteObject(timeframe.uid).then(resp => {
      commit('REMOVE_TIMEFRAME', timeframe)
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
