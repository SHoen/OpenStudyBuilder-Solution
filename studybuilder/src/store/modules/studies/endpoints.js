import Vue from 'vue'
import endpoints from '@/api/endpoints'
import timeframes from '@/api/timeframes'
import study from '@/api/study'
import instances from '@/utils/instances'
import utils from '@/store/utils'

const state = {
  studyEndpoints: [],
  total: 0
}

const getters = {
  studyEndpoints: state => state.studyEndpoints,
  total: state => state.total
}

const mutations = {
  SET_STUDY_ENDPOINTS (state, studyEndpoints) {
    state.studyEndpoints = studyEndpoints.items
    state.total = studyEndpoints.total
  },
  ADD_STUDY_ENDPOINT (state, studyEndpoint) {
    state.studyEndpoints.unshift(studyEndpoint)
  },
  UPDATE_STUDY_ENDPOINT (state, studyEndpoint) {
    state.studyEndpoints.filter((item, pos) => {
      if (item.study_endpoint_uid === studyEndpoint.study_endpoint_uid) {
        Vue.set(state.studyEndpoints, pos, studyEndpoint)
        return true
      }
      return false
    })
  },
  REMOVE_STUDY_ENDPOINT (state, studyEndpointUid) {
    state.studyEndpoints = state.studyEndpoints.filter(function (item) {
      return item.study_endpoint_uid !== studyEndpointUid
    })
  }
}

const actions = {
  fetchStudyEndpoints ({ commit }, data) {
    const studyUid = data.studyUid
    delete data.studyUid
    return study.getStudyEndpoints(studyUid, data).then(resp => {
      commit('SET_STUDY_ENDPOINTS', resp.data)
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
      endpoint_template_uid: data.endpoint_template.uid,
      library_name: data.endpoint_template.library.name,
      parameter_terms: await instances.formatParameterValues(endpointParameters)
    }
    data.endpoint_data = endpointData
    delete data.endpoint_template

    data.endpoint_units.units = data.endpoint_units.units.map(unit => unit.uid)

    if (data.timeframe_template) {
      // Create timeframe if a timeframe with specified name does not exist
      const timeframe = {
        timeframe_template_uid: data.timeframe_template.uid,
        library_name: data.timeframe_template.library.name,
        parameter_terms: await instances.formatParameterValues(timeframeParameters)
      }
      const timeframeTemplate = data.timeframe_template
      delete data.timeframe_template
      try {
        // Search for an existing timeframe by name
        const searchName = utils.getInternalApiName(timeframeTemplate.name, timeframeParameters)
        const response = await timeframes.getObjectByName(searchName)
        data.timeframe_uid = response.data.items[0].uid
      } catch (error) {
        // Create timeframe since a timeframe with specified name does not exist
        const response = await timeframes.create(timeframe)
        data.timeframe_uid = response.data.uid
        try {
          await timeframes.approve(data.timeframe_uid)
        } catch (error) {
          // Do some cleanup
          await timeframes.deleteObject(data.timeframe_uid)
          throw error
        }
      }
    }

    if (data.study_objective) {
      data.study_objective_uid = data.study_objective.study_objective_uid
      delete data.study_objective
    }

    if (data.endpoint_level) {
      data.endpoint_level_uid = data.endpoint_level.term_uid
      delete data.endpoint_level
    }
    if (data.endpoint_sublevel) {
      data.endpoint_sublevel_uid = data.endpoint_sublevel.term_uid
      delete data.endpoint_sublevel
    }

    return study.createStudyEndpoint(studyUid, data)
  },
  selectFromStudyEndpoint ({ commit }, { studyUid, studyEndpoint }) {
    const data = {
      endpoint_uid: studyEndpoint.endpoint.uid,
      endpoint_units: {
        units: studyEndpoint.endpoint_units.units.map(unit => unit.uid),
        separator: studyEndpoint.endpoint_units.separator
      }
    }
    if (studyEndpoint.timeframe) {
      data.timeframe_uid = studyEndpoint.timeframe.uid
    }
    if (studyEndpoint.endpoint_level) {
      data.endpoint_level_uid = studyEndpoint.endpoint_level.term_uid
    }
    if (studyEndpoint.endpoint_sublevel) {
      data.endpoint_sublevel_uid = studyEndpoint.endpoint_sublevel.term_uid
    }
    return study.selectStudyEndpoint(studyUid, data)
  },
  async updateStudyEndpoint ({ commit, dispatch }, { studyUid, studyEndpointUid, form }) {
    const data = {}
    if (form.endpoint_units) {
      data.endpoint_units = { units: form.endpoint_units.units.map(unit => unit.uid) }
    }
    if (form.study_objective !== undefined) {
      if (form.study_objective === null) {
        data.study_objective_uid = null
      } else {
        data.study_objective_uid = form.study_objective.study_objective_uid
      }
    }
    if (form.endpoint_level !== undefined) {
      if (form.endpoint_level === null) {
        data.endpoint_level_uid = null
      } else {
        data.endpoint_level_uid = form.endpoint_level.term_uid
      }
    }
    if (form.endpoint_sublevel !== undefined) {
      if (form.endpoint_sublevel === null) {
        data.endpoint_sublevel_uid = null
      } else {
        data.endpoint_sublevel_uid = form.endpoint_sublevel.term_uid
      }
    }
    if (form.endpoint_parameters !== undefined) {
      try {
        // Search for an existing endpoint by name
        const searchName = utils.getInternalApiName(form.endpoint_template.name, form.endpoint_parameters)
        const response = await endpoints.getObjectByName(searchName)
        data.endpoint_uid = response.data.items[0].uid
      } catch (error) {
        // Create endpoint since an endpoint with specified name does not exist
        const endpoint = {
          endpoint_template_uid: form.endpoint_template.uid,
          library_name: form.endpoint_template.library.name,
          parameter_terms: await instances.formatParameterValues(form.endpoint_parameters)
        }
        const resp = await endpoints.create(endpoint)
        data.endpoint_uid = resp.data.uid
        try {
          await endpoints.approve(resp.data.uid)
        } catch (error) {
          // Do some cleanup
          await endpoints.deleteObject(data.endpoint_uid)
          throw error
        }
      }
    }
    if (form.timeframe_parameters !== undefined) {
      try {
        // Search for an existing timeframe by name
        const searchName = utils.getInternalApiName(form.timeframe_template.name, form.timeframe_parameters)
        const response = await timeframes.getObjectByName(searchName)
        data.timeframe_uid = response.data.items[0].uid
      } catch (error) {
        // Create timeframe since a timeframe with specified name does not exist
        const timeframe = {
          timeframe_template_uid: form.timeframe_template.uid,
          library_name: form.timeframe_template.library.name,
          parameter_terms: await instances.formatParameterValues(form.timeframe_parameters)
        }
        const resp = await timeframes.create(timeframe)
        data.timeframe_uid = resp.data.uid
        try {
          await timeframes.approve(resp.data.uid)
        } catch (error) {
          // Do some cleanup
          await timeframes.deleteObject(data.timeframe_uid)
          throw error
        }
      }
    }
    return study.updateStudyEndpoint(studyUid, studyEndpointUid, data)
  },
  async updateStudyEndpointEndpointLatestVersion ({ commit }, { studyUid, studyEndpointUid }) {
    const resp = await study.updateStudyEndpointEndpointLatestVersion(
      studyUid, studyEndpointUid
    )
    commit('UPDATE_STUDY_ENDPOINT', resp.data)
  },
  async updateStudyEndpointTimeframeLatestVersion ({ commit }, { studyUid, studyEndpointUid }) {
    const resp = await study.updateStudyEndpointTimeframeLatestVersion(
      studyUid, studyEndpointUid
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
