import Vue from 'vue'
import endpoints from '@/api/endpoints'
import timeframes from '@/api/timeframes'
import study from '@/api/study'
import instances from '@/utils/instances'
import utils from '@/store/utils'

const state = {
  studyEndpoints: []
}

const getters = {
  studyEndpoints: state => state.studyEndpoints
}

const mutations = {
  SET_STUDY_ENDPOINTS (state, studyEndpoints) {
    state.studyEndpoints = studyEndpoints
  },
  ADD_STUDY_ENDPOINT (state, studyEndpoint) {
    state.studyEndpoints.unshift(studyEndpoint)
  },
  UPDATE_STUDY_ENDPOINT (state, studyEndpoint) {
    state.studyEndpoints.filter((item, pos) => {
      if (item.studyEndpointUid === studyEndpoint.studyEndpointUid) {
        Vue.set(state.studyEndpoints, pos, studyEndpoint)
      }
    })
  },
  REMOVE_STUDY_ENDPOINT (state, studyEndpointUid) {
    state.studyEndpoints = state.studyEndpoints.filter(function (item) {
      return item.studyEndpointUid !== studyEndpointUid
    })
  }
}

const actions = {
  fetchStudyEndpoints ({ commit }, data) {
    return study.getStudyEndpoints(data.studyUid, data).then(resp => {
      commit('SET_STUDY_ENDPOINTS', resp.data.items)
      return resp
    })
  },
  /*
  ** FIXME: there are too much API calls here, and we don't have a
  ** proper way to rollback what we do in case of error.
  */
  async addStudyEndpoint ({ commit, dispatch }, { studyUid, data, endpointParameters, timeframeParameters }) {
    // Create endpoint
    const endpointData = {
      endpointTemplateUid: data.endpointTemplate.uid,
      libraryName: data.endpointTemplate.library.name,
      parameterValues: await instances.formatParameterValues(endpointParameters)
    }
    data.endpointData = endpointData
    delete data.endpointTemplate

    if (data.timeframeTemplate) {
      // Create timeframe
      const timeframe = {
        timeframeTemplateUid: data.timeframeTemplate.uid,
        libraryName: data.timeframeTemplate.library.name,
        parameterValues: await instances.formatParameterValues(timeframeParameters)
      }
      const timeframeTemplate = data.timeframeTemplate
      delete data.timeframeTemplate
      try {
        const searchName = utils.getInternalApiName(timeframeTemplate.name, timeframeParameters)
        const response = await timeframes.getObjectByName(searchName)
        data.timeframeUid = response.data.uid
      } catch (error) {
        const response = await timeframes.create(timeframe)
        data.timeframeUid = response.data.uid
        try {
          await timeframes.approve(data.timeframeUid)
        } catch (error) {
          // Do some cleanup
          await timeframes.deleteObject(data.timeframeUid)
          throw error
        }
      }
    }

    if (data.studyObjective) {
      data.studyObjectiveUid = data.studyObjective.studyObjectiveUid
      delete data.studyObjective
    }

    if (data.endpointLevel) {
      data.endpointLevelUid = data.endpointLevel.termUid
      delete data.endpointLevel
    }
    if (data.endpointSubLevel) {
      data.endpointSubLevelUid = data.endpointSubLevel.termUid
      delete data.endpointSubLevel
    }

    return study.createStudyEndpoint(studyUid, data).then(resp => {
      // Fetch complete list of endpoints to be sure orders are updated
      dispatch('fetchStudyEndpoints', { studyUid })
    })
  },
  selectFromStudyEndpoint ({ commit }, { studyUid, form, studyEndpoint }) {
    const data = {
      studyObjectiveUid: form.studyObjective.studyObjectiveUid,
      endpointUid: studyEndpoint.endpoint.uid,
      endpointUnits: studyEndpoint.endpointUnits
    }
    if (studyEndpoint.timeframe) {
      data.timeframeUid = studyEndpoint.timeframe.uid
    }
    if (form.endpointLevel) {
      data.endpointLevelUid = form.endpointLevel.termUid
    }
    if (form.endpointSubLevel) {
      data.endpointSubLevelUid = form.endpointSubLevel.termUid
    }
    return study.selectStudyEndpoint(studyUid, data).then(resp => {
      commit('ADD_STUDY_ENDPOINT', resp.data)
    })
  },
  async updateStudyEndpoint ({ commit, dispatch }, { studyUid, studyEndpointUid, form }) {
    const data = {
      endpointUnits: form.endpointUnits
    }
    if (form.studyObjective) {
      data.studyObjectiveUid = form.studyObjective.studyObjectiveUid
    } else {
      data.studyObjectiveUid = null
    }
    if (form.endpointLevel) {
      data.endpointLevelUid = form.endpointLevel.termUid
    }
    if (form.endpointSubLevel) {
      data.endpointSubLevelUid = form.endpointSubLevel.termUid
    }
    if (form.endpointParameters !== undefined) {
      try {
        const searchName = utils.getInternalApiName(form.endpointTemplate.name, form.endpointParameters)
        const response = await endpoints.getObjectByName(searchName)
        data.endpointUid = response.data.uid
      } catch (error) {
        // Create endpoint
        const endpoint = {
          endpointTemplateUid: form.endpointTemplate.uid,
          libraryName: form.endpointTemplate.library.name,
          parameterValues: await instances.formatParameterValues(form.endpointParameters)
        }
        const resp = await endpoints.create(endpoint)
        data.endpointUid = resp.data.uid
        try {
          await endpoints.approve(resp.data.uid)
        } catch (error) {
          // Do some cleanup
          await endpoints.deleteObject(data.endpointUid)
          throw error
        }
      }
    }
    if (form.timeframeParameters !== undefined) {
      try {
        const searchName = utils.getInternalApiName(form.timeframeTemplate.name, form.timeframeParameters)
        const response = await timeframes.getObjectByName(searchName)
        data.timeframeUid = response.data.uid
      } catch (error) {
        // Create timeframe
        const timeframe = {
          timeframeTemplateUid: form.timeframeTemplate.uid,
          libraryName: form.timeframeTemplate.library.name,
          parameterValues: await instances.formatParameterValues(form.timeframeParameters)
        }
        const resp = await timeframes.create(timeframe)
        data.timeframeUid = resp.data.uid
        try {
          await timeframes.approve(resp.data.uid)
        } catch (error) {
          // Do some cleanup
          await timeframes.deleteObject(data.timeframeUid)
          throw error
        }
      }
    }
    return study.updateStudyEndpoint(studyUid, studyEndpointUid, data).then(resp => {
      dispatch('fetchStudyEndpoints', { studyUid })
    })
  },
  async updateStudyEndpointEndpointLatestVersion ({ commit }, { studyUid, studyObjectiveUid }) {
    const resp = await study.updateStudyEndpointEndpointLatestVersion(
      studyUid, studyObjectiveUid
    )
    commit('UPDATE_STUDY_ENDPOINT', resp.data)
  },
  async updateStudyEndpointTimeframeLatestVersion ({ commit }, { studyUid, studyObjectiveUid }) {
    const resp = await study.updateStudyEndpointTimeframeLatestVersion(
      studyUid, studyObjectiveUid
    )
    commit('UPDATE_STUDY_ENDPOINT', resp.data)
  },
  async updateStudyEndpointAcceptVersion ({ commit }, { studyUid, studyEndpointUid }) {
    const resp = await study.updateStudyEndpointAcceptVersion(
      studyUid, studyEndpointUid
    )
    commit('UPDATE_STUDY_ENDPOINT', resp.data)
  },
  deleteStudyEndpoint ({ commit }, { studyUid, studyEndpointUid }) {
    return study.deleteStudyEndpoint(studyUid, studyEndpointUid).then(resp => {
      commit('REMOVE_STUDY_ENDPOINT', studyEndpointUid)
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
