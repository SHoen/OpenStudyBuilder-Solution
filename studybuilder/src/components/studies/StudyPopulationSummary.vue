<template>
<study-metadata-summary
  :metadata="metadata"
  :params="params"
  :first-col-label="$t('StudyPopulationSummary.info_column')"
  persistent-dialog
  copy-from-study
  component="studyPopulation"
  >
  <template v-slot:form="{ closeHandler, dataToCopy, openHandler }">
    <study-population-form :open="openHandler" :metadata="(Object.keys(dataToCopy).length !== 0) ? dataToCopy : metadata" @updated="onMetadataUpdated" @close="closeHandler" />
  </template>
</study-metadata-summary>
</template>

<script>
import { mapGetters } from 'vuex'
import study from '@/api/study'
import StudyMetadataSummary from './StudyMetadataSummary'
import StudyPopulationForm from './StudyPopulationForm'

export default {
  components: {
    StudyMetadataSummary,
    StudyPopulationForm
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  data () {
    return {
      metadata: {},
      params: [
        {
          label: this.$t('StudyPopulationForm.therapeuticarea'),
          name: 'therapeuticAreasCodes',
          valuesDisplay: 'terms'
        },
        {
          label: this.$t('StudyPopulationForm.disease_condition'),
          name: 'diseaseConditionsOrIndicationsCodes',
          valuesDisplay: 'terms'
        },
        {
          label: this.$t('StudyPopulationForm.stable_disease_min_duration'),
          name: 'stableDiseaseMinimumDuration',
          valuesDisplay: 'duration'
        },
        {
          label: this.$t('StudyPopulationForm.healthy_subjects'),
          name: 'healthySubjectIndicator',
          valuesDisplay: 'yesno'
        },
        {
          label: this.$t('StudyPopulationForm.diagnosis_group'),
          name: 'diagnosisGroupsCodes',
          valuesDisplay: 'terms'
        },
        {
          label: this.$t('StudyPopulationForm.relapse_criteria'),
          name: 'relapseCriteria'
        },
        {
          label: this.$t('StudyPopulationForm.number_of_expected_subjects'),
          name: 'numberOfExpectedSubjects'
        },
        {
          label: this.$t('StudyPopulationForm.rare_disease_indicator'),
          name: 'rareDiseaseIndicator',
          valuesDisplay: 'yesno'
        },
        {
          label: this.$t('StudyPopulationForm.sex_of_study_participants'),
          name: 'sexOfParticipantsCode',
          valuesDisplay: 'terms'
        },
        {
          label: this.$t('StudyPopulationForm.planned_min_age'),
          name: 'plannedMinimumAgeOfSubjects',
          valuesDisplay: 'duration'
        },
        {
          label: this.$t('StudyPopulationForm.planned_max_age'),
          name: 'plannedMaximumAgeOfSubjects',
          valuesDisplay: 'duration'
        },
        {
          label: this.$t('StudyPopulationForm.pediatric_study_indicator'),
          name: 'pediatricStudyIndicator',
          valuesDisplay: 'yesno'
        },
        {
          label: this.$t('StudyPopulationForm.pediatric_investigation_plan_indicator'),
          name: 'pediatricInvestigationPlanIndicator',
          valuesDisplay: 'yesno'
        },
        {
          label: this.$t('StudyPopulationForm.pediatric_postmarket_study_indicator'),
          name: 'pediatricPostmarketStudyIndicator',
          valuesDisplay: 'yesno'
        }
      ]
    }
  },
  methods: {
    onMetadataUpdated (metadata) {
      this.metadata = metadata
    }
  },
  created () {
    this.$store.dispatch('studiesGeneral/fetchUnits')
    this.$store.dispatch('studiesGeneral/fetchSnomedTerms')
    this.$store.dispatch('studiesGeneral/fetchSexOfParticipants')
    study.getStudyPopulationMetadata(this.selectedStudy.uid).then(resp => {
      this.metadata = resp.data.currentMetadata.studyPopulation
    })
  }
}
</script>
