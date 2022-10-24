import units from '@/api/units'
import Vue from 'vue'

const state = {
  units: []
}

const getters = {
  units: state => state.units
}

const mutations = {
  SET_UNITS (state, units) {
    state.units = units
  },
  ADD_UNIT (state, unit) {
    state.units.items.unshift(unit)
  },
  UPDATE_UNIT (state, unit) {
    state.units.items.filter((item, pos) => {
      if (item.uid === unit.uid) {
        Vue.set(state.units, pos, unit)
      }
    })
  }
}

const actions = {
  fetchUnits ({ commit }, params) {
    return units.get(params).then(resp => {
      commit('SET_UNITS', resp.data)
    })
  },
  addUnit ({ commit }, data) {
    return units.create(data).then(resp => {
      commit('ADD_UNIT', resp.data)
    })
  },
  updateUnit ({ commit }, { uid, data }) {
    return units.edit(uid, data).then(resp => {
      commit('UPDATE_UNIT', resp.data)
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
