import dictionaries from '@/api/dictionaries'
import study from '@/api/study'
import terms from '@/api/controlledTerminology/terms'
import units from '@/api/units'

const state = {
  selectedStudy: null,
  selectedStudyVersion: null,
  studyPreferredTimeUnit: null,
  soaPreferredTimeUnit: null,
  studyTypes: [],
  trialIntentTypes: [],
  trialTypes: [],
  trialPhases: [],
  interventionTypes: [],
  snomedTerms: [],
  sexOfParticipants: [],
  trialBlindingSchemas: [],
  controlTypes: [],
  interventionModels: [],
  units: [],
  nullValues: [],
  objectiveLevels: [],
  endpointLevels: [],
  endpointSubLevels: [],
  allUnits: []
}

const getters = {
  selectedStudy: state => state.selectedStudy,
  selectedStudyVersion: state => state.selectedStudyVersion,
  studyPreferredTimeUnit: state => state.studyPreferredTimeUnit,
  soaPreferredTimeUnit: state => state.soaPreferredTimeUnit,
  studyTypes: state => state.studyTypes,
  trialIntentTypes: state => state.trialIntentTypes,
  trialTypes: state => state.trialTypes,
  trialPhases: state => state.trialPhases,
  interventionTypes: state => state.interventionTypes,
  snomedTerms: state => state.snomedTerms,
  sexOfParticipants: state => state.sexOfParticipants,
  trialBlindingSchemas: state => state.trialBlindingSchemas,
  controlTypes: state => state.controlTypes,
  interventionModels: state => state.interventionModels,
  units: state => state.units,
  nullValues: state => state.nullValues,
  objectiveLevels: state => state.objectiveLevels,
  sortedObjectiveLevels: state => {
    return state.objectiveLevels.sort((a, b) => {
      return a.order - b.order
    })
  },
  endpointLevels: state => state.endpointLevels,
  endpointSubLevels: state => state.endpointSubLevels,
  sortedEndpointLevels: state => {
    return state.endpointLevels.sort((a, b) => {
      return a.order - b.order
    })
  },
  allUnits: state => state.allUnits
}

const mutations = {
  SELECT_STUDY (state, { studyObj, forceReload }) {
    state.selectedStudy = studyObj
    state.selectedStudyVersion = studyObj.current_metadata.version_metadata.version_number
    localStorage.setItem('selectedStudy', JSON.stringify(studyObj))
    if (forceReload) {
      document.location.reload()
    }
  },
  UNSELECT_STUDY (state) {
    state.selectedStudy = null
    localStorage.removeItem('selectedStudy')
  },
  SET_STUDY_PREFERRED_TIME_UNIT (state, timeUnit) {
    state.studyPreferredTimeUnit = timeUnit
  },
  SET_SOA_PREFERRED_TIME_UNIT (state, timeUnit) {
    state.soaPreferredTimeUnit = timeUnit
  },
  SET_UNITS (state, data) {
    state.units = data
  },
  SET_ALL_UNITS (state, data) {
    state.allUnits = data
  },
  SET_STUDY_TYPES (state, data) {
    state.studyTypes = data
  },
  SET_TRIAL_INTENT_TYPES (state, data) {
    state.trialIntentTypes = data
  },
  SET_TRIAL_TYPES (state, data) {
    state.trialTypes = data
  },
  SET_TRIAL_PHASES (state, data) {
    state.trialPhases = data
  },
  SET_INTERVENTION_TYPES (state, data) {
    state.interventionTypes = data
  },
  SET_SNOMED_TERMS (state, data) {
    state.snomedTerms = data
  },
  SET_SEX_OF_PARTICIPANTS (state, data) {
    state.sexOfParticipants = data
  },
  SET_TRIAL_BLINDING_SCHEMAS (state, data) {
    state.trialBlindingSchemas = data
  },
  SET_CONTROL_TYPES (state, data) {
    state.controlTypes = data
  },
  SET_INTERVENTION_MODELS (state, data) {
    state.interventionModels = data
  },
  SET_NULL_VALUES (state, data) {
    state.nullValues = data
  },
  SET_OBJECTIVE_LEVELS (state, data) {
    state.objectiveLevels = data
  },
  SET_ENDPOINT_LEVELS (state, data) {
    state.endpointLevels = data
  },
  SET_ENDPOINT_SUB_LEVELS (state, data) {
    state.endpointSubLevels = data
  }
}

const actions = {
  async initialize ({ commit, dispatch }) {
    const selectedStudy = localStorage.getItem('selectedStudy')
    if (selectedStudy) {
      const parsedStudy = JSON.parse(selectedStudy)
      dispatch('selectStudy', { studyObj: parsedStudy })
      try {
        await study.getStudy(parsedStudy.uid, true)
      } catch (error) {
        commit('UNSELECT_STUDY')
      }
    }
  },
  selectStudy ({ commit, state }, { studyObj, forceReload }) {
    commit('SELECT_STUDY', { studyObj, forceReload })
    study.getStudyPreferredTimeUnit(studyObj.uid, studyObj.current_metadata.version_metadata.version_number).then(resp => {
      commit('SET_STUDY_PREFERRED_TIME_UNIT', resp.data)
    })
    study.getSoAPreferredTimeUnit(studyObj.uid, studyObj.current_metadata.version_metadata.version_number).then(resp => {
      commit('SET_SOA_PREFERRED_TIME_UNIT', resp.data)
    })
  },
  setStudyPreferredTimeUnit ({ commit, state }, { timeUnitUid, protocolSoa }) {
    const data = {
      unit_definition_uid: timeUnitUid
    }
    return study.updateStudyPreferredTimeUnit(state.selectedStudy.uid, data, protocolSoa).then(resp => {
      protocolSoa ? commit('SET_SOA_PREFERRED_TIME_UNIT', resp.data) : commit('SET_STUDY_PREFERRED_TIME_UNIT', resp.data)
    })
  },
  fetchUnits ({ commit, state }) {
    units.getBySubset('Study Time').then(resp => {
      commit('SET_UNITS', resp.data.items)
    })
  },
  fetchAllUnits ({ commit, state }) {
    units.get({ params: { page_size: 0 } }).then(resp => {
      commit('SET_ALL_UNITS', resp.data.items)
    })
  },
  fetchStudyTypes ({ commit, state }) {
    terms.getByCodelist('studyType').then(resp => {
      commit('SET_STUDY_TYPES', resp.data.items)
    })
  },
  fetchTrialIntentTypes ({ commit, state }) {
    terms.getByCodelist('trialIntentType').then(resp => {
      commit('SET_TRIAL_INTENT_TYPES', resp.data.items)
    })
  },
  fetchTrialTypes ({ commit, state }) {
    terms.getByCodelist('trialType').then(resp => {
      commit('SET_TRIAL_TYPES', resp.data.items)
    })
  },
  fetchTrialPhases ({ commit, state }) {
    terms.getByCodelist('trialPhase').then(resp => {
      commit('SET_TRIAL_PHASES', resp.data.items)
    })
  },
  fetchInterventionTypes ({ commit, state }) {
    terms.getByCodelist('interventionTypes').then(resp => {
      commit('SET_INTERVENTION_TYPES', resp.data.items)
    })
  },
  fetchSnomedTerms ({ commit, data }) {
    dictionaries.getCodelists('SNOMED').then(resp => {
      const params = {
        codelist_uid: resp.data.items[0].codelist_uid,
        page_size: 0
      }
      dictionaries.getTerms(params).then(resp => {
        commit('SET_SNOMED_TERMS', resp.data.items)
      })
    })
  },
  fetchSexOfParticipants ({ commit, state }) {
    terms.getByCodelist('sexOfParticipants').then(resp => {
      commit('SET_SEX_OF_PARTICIPANTS', resp.data.items)
    })
  },
  fetchTrialBlindingSchemas ({ commit, state }) {
    terms.getByCodelist('trialBlindingSchema').then(resp => {
      commit('SET_TRIAL_BLINDING_SCHEMAS', resp.data.items)
    })
  },
  fetchControlTypes ({ commit, state }) {
    terms.getByCodelist('controlType').then(resp => {
      commit('SET_CONTROL_TYPES', resp.data.items)
    })
  },
  fetchInterventionModels ({ commit, data }) {
    terms.getByCodelist('interventionModel').then(resp => {
      commit('SET_INTERVENTION_MODELS', resp.data.items)
    })
  },
  fetchNullValues ({ commit, state }) {
    terms.getByCodelist('nullValues').then(resp => {
      commit('SET_NULL_VALUES', resp.data.items)
    })
  },
  fetchObjectiveLevels ({ commit, state }) {
    terms.getByCodelist('objectiveLevels').then(resp => {
      // FIXME: deal with pagination to retrieve all items
      commit('SET_OBJECTIVE_LEVELS', resp.data.items)
    })
  },
  fetchEndpointLevels ({ commit, state }) {
    terms.getByCodelist('endpointLevels').then(resp => {
      // FIXME: deal with pagination to retrieve all items
      commit('SET_ENDPOINT_LEVELS', resp.data.items)
    })
  },
  fetchEndpointSubLevels ({ commit, state }) {
    terms.getByCodelist('endpointSubLevels').then(resp => {
      // FIXME: deal with pagination to retrieve all items
      commit('SET_ENDPOINT_SUB_LEVELS', resp.data.items)
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
