import Vue from 'vue'
import study from '@/api/study'

const state = {
  studyCompounds: [],
  studyCompounds__Loading: false,
  studyCompoundDosings: []
}

const getters = {
  studyCompounds: state => state.studyCompounds,
  studyCompounds__Loading: state => state.studyCompounds__Loading,
  studyCompoundDosings: state => state.studyCompoundDosings,
  getStudyCompoundsByTypeOfTreatment: state => typeOfTreatmentUid => {
    return state.studyCompounds.filter(item => item.typeOfTreatment.termUid === typeOfTreatmentUid)
  },
  getNAStudyCompoundsByTypeOfTreatment: state => typeOfTreatmentUid => {
    return state.studyCompounds.filter(item => item.typeOfTreatment.termUid === typeOfTreatmentUid && !item.compound)
  },
  getStudyCompoundDosingsByStudyCompound: state => {
    const result = {}
    for (const compoundDosing of state.studyCompoundDosings) {
      const uid = compoundDosing.studyCompound.studyCompoundUid
      if (result[uid] === undefined) {
        result[uid] = []
      }
      result[uid].push(compoundDosing)
    }
    return result
  }
}

const mutations = {
  SET_STUDY_COMPOUNDS (state, studyCompounds) {
    state.studyCompounds = studyCompounds
  },
  SET_STUDY_COMPOUNDS_LOADING (state, val) {
    state.studyCompounds__Loading = val
  },
  ADD_STUDY_COMPOUND (state, studyCompound) {
    state.studyCompounds.unshift(studyCompound)
  },
  UPDATE_STUDY_COMPOUND (state, studyCompound) {
    state.studyCompounds.filter((item, pos) => {
      if (item.studyCompoundUid === studyCompound.studyCompoundUid) {
        Vue.set(state.studyCompounds, pos, studyCompound)
      }
    })
  },
  REMOVE_STUDY_COMPOUND (state, studyCompoundUid) {
    state.studyCompounds = state.studyCompounds.filter(function (item) {
      return item.studyCompoundUid !== studyCompoundUid
    })
  },
  SET_STUDY_COMPOUND_DOSINGS (states, studyCompoundDosings) {
    state.studyCompoundDosings = studyCompoundDosings
  },
  ADD_STUDY_COMPOUND_DOSING (state, studyCompoundDosing) {
    state.studyCompoundDosings.unshift(studyCompoundDosing)
  },
  UPDATE_STUDY_COMPOUND_DOSING (state, studyCompoundDosing) {
    state.studyCompoundDosings.filter((item, pos) => {
      if (item.studyCompoundDosingUid === studyCompoundDosing.studyCompoundDosingUid) {
        Vue.set(state.studyCompoundDosings, pos, studyCompoundDosing)
      }
    })
  },
  REMOVE_STUDY_COMPOUND_DOSING (state, studyCompoundDosingUid) {
    state.studyCompoundDosings = state.studyCompoundDosings.filter(function (item) {
      return item.studyCompoundDosingUid !== studyCompoundDosingUid
    })
  }
}

const actions = {
  async fetchStudyCompounds ({ commit }, data) {
    commit('SET_STUDY_COMPOUNDS_LOADING', true)
    let respData
    await study.getStudyCompounds(data.studyUid, data).then(resp => {
      commit('SET_STUDY_COMPOUNDS', resp.data.items)
      commit('SET_STUDY_COMPOUNDS_LOADING', false)
      respData = resp
    })
    return respData
  },
  addStudyCompound ({ commit }, { studyUid, data }) {
    study.selectStudyCompound(studyUid, data).then(resp => {
      commit('ADD_STUDY_COMPOUND', resp.data)
    })
  },
  updateStudyCompound ({ commit }, { studyUid, studyCompoundUid, data }) {
    return study.updateStudyCompound(studyUid, studyCompoundUid, data).then(resp => {
      commit('UPDATE_STUDY_COMPOUND', resp.data)
    })
  },
  deleteStudyCompound ({ commit }, { studyUid, studyCompoundUid }) {
    return study.deleteStudyCompound(studyUid, studyCompoundUid).then(resp => {
      commit('REMOVE_STUDY_COMPOUND', studyCompoundUid)
    })
  },
  fetchStudyCompoundDosings ({ commit }, studyUid) {
    study.getStudyCompoundDosings(studyUid).then(resp => {
      commit('SET_STUDY_COMPOUND_DOSINGS', resp.data.items)
    })
  },
  addStudyCompoundDosing ({ commit }, { studyUid, data }) {
    return study.addStudyCompoundDosing(studyUid, data).then(resp => {
      commit('ADD_STUDY_COMPOUND_DOSING', resp.data)
    })
  },
  updateStudyCompoundDosing ({ commit }, { studyUid, studyCompoundDosingUid, data }) {
    return study.updateStudyCompoundDosing(studyUid, studyCompoundDosingUid, data).then(resp => {
      commit('UPDATE_STUDY_COMPOUND_DOSING', resp.data)
    })
  },
  deleteStudyCompoundDosing ({ commit }, { studyUid, studyCompoundDosingUid }) {
    return study.deleteStudyCompoundDosing(studyUid, studyCompoundDosingUid).then(resp => {
      commit('REMOVE_STUDY_COMPOUND_DOSING', studyCompoundDosingUid)
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
