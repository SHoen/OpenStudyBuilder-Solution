import Vue from 'vue'
import studyEpochs from '@/api/studyEpochs'

const state = {
  studyEpochs: [],
  studyVisits: [],
  allowedConfigs: []
}

const getters = {
  studyEpochs: state => state.studyEpochs,
  studyVisits: state => state.studyVisits,
  allowedConfigs: state => state.allowedConfigs
}

const mutations = {
  SET_STUDY_VISITS (state, studyVisits) {
    state.studyVisits = studyVisits
  },
  SET_STUDY_EPOCHS (state, studyEpochs) {
    state.studyEpochs = studyEpochs
  },
  SET_ALLOWED_CONFIGS (state, allowedConfigs) {
    state.allowedConfigs = allowedConfigs
  },
  ADD_STUDY_EPOCH (state, studyEpoch) {
    state.studyEpochs.unshift(studyEpoch)
  },
  UPDATE_STUDY_EPOCH (state, studyEpoch) {
    state.studyEpochs.filter((item, pos) => {
      if (item.uid === studyEpoch.uid) {
        Vue.set(state.studyEpochs, pos, studyEpoch)
      }
    })
  },
  REMOVE_STUDY_EPOCH (state, uid) {
    state.studyEpochs = state.studyEpochs.filter(function (item) {
      return item.uid !== uid
    })
  }
}

const actions = {
  fetchStudyVisits ({ commit }, studyUid) {
    return studyEpochs.getStudyVisits(studyUid).then(resp => {
      commit('SET_STUDY_VISITS', resp.data.items)
    })
  },
  fetchFilteredStudyVisits ({ commit }, data) {
    return studyEpochs.getStudyVisits(data.studyUid, data).then(resp => {
      commit('SET_STUDY_VISITS', resp.data)
    })
  },
  async addStudyVisit ({ commit, dispatch }, { studyUid, input }) {
    await studyEpochs.addStudyVisit(studyUid, input)
    await dispatch('fetchStudyEpochs', studyUid)
  },
  updateStudyVisit ({ commit, dispatch }, { studyUid, studyVisitUid, input }) {
    return studyEpochs.updateStudyVisit(studyUid, studyVisitUid, input).then(resp => {
      dispatch('fetchStudyEpochs', studyUid)
    })
  },
  async deleteStudyVisit ({ commit, dispatch }, { studyUid, studyVisitUid }) {
    await studyEpochs.deleteStudyVisit(studyUid, studyVisitUid)
    await dispatch('fetchStudyEpochs', studyUid)
  },
  fetchStudyEpochs ({ commit }, studyUid) {
    return studyEpochs.getStudyEpochs(studyUid).then(resp => {
      commit('SET_STUDY_EPOCHS', resp.data.items)
    })
  },
  fetchFilteredStudyEpochs ({ commit }, data) {
    return studyEpochs.getFilteredEpochs(data.studyUid, data).then(resp => {
      commit('SET_STUDY_EPOCHS', resp.data.items)
    })
  },
  fetchAllowedConfigs ({ commit }) {
    return studyEpochs.getAllowedConfigs().then(resp => {
      commit('SET_ALLOWED_CONFIGS', resp.data)
    })
  },
  async addStudyEpoch ({ commit }, { studyUid, input }) {
    return studyEpochs.addStudyEpoch(studyUid, input).then(resp => {
      commit('ADD_STUDY_EPOCH', resp.data)
    })
  },
  async updateStudyEpoch ({ commit }, { studyUid, studyEpochUid, input }) {
    return studyEpochs.updateStudyEpoch(studyUid, studyEpochUid, input).then(resp => {
      commit('UPDATE_STUDY_EPOCH', resp.data)
    })
  },
  deleteStudyEpoch ({ commit }, { studyUid, studyEpochUid }) {
    return studyEpochs.deleteStudyEpoch(studyUid, studyEpochUid).then(resp => {
      commit('REMOVE_STUDY_EPOCH', studyEpochUid)
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
