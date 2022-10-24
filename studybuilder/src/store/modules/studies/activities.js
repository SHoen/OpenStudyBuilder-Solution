import study from '@/api/study'
import Vue from 'vue'

const state = {
  studyActivities: []
}

const getters = {
  studyActivities: state => state.studyActivities,
  sortedStudyActivities: state => {
    const result = {}
    for (const studyActivity of state.studyActivities) {
      const fgroup = studyActivity.flowchartGroup.sponsorPreferredName
      if (!result[fgroup]) {
        Vue.set(result, fgroup, {})
      }
      const group = (studyActivity.activity.activityGroup)
        ? studyActivity.activity.activityGroup.name : ''
      const subgroup = (studyActivity.activity.activitySubGroup)
        ? studyActivity.activity.activitySubGroup.name : ''
      if (!result[fgroup][group]) {
        Vue.set(result[fgroup], group, {})
      }
      if (!result[fgroup][group][subgroup]) {
        Vue.set(result[fgroup][group], subgroup, [])
      }
      result[fgroup][group][subgroup].push(studyActivity)
    }
    return result
  }
}

const mutations = {
  SET_STUDY_ACTIVITIES (state, studyActivities) {
    state.studyActivities = studyActivities
  },
  UPDATE_STUDY_ACTIVITY (state, studyActivity) {
    state.studyActivities.filter((item, pos) => {
      if (item.studyActivityUid === studyActivity.studyActivityUid) {
        Vue.set(state.studyActivities, pos, studyActivity)
      }
    })
  }
}

const actions = {
  fetchStudyActivities ({ commit }, params) {
    return study.getStudyActivities(params.studyUid, params).then(resp => {
      commit('SET_STUDY_ACTIVITIES', resp.data.items)
      return resp
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
