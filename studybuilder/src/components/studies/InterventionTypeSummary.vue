<template>
<study-metadata-summary
  :metadata="metadata"
  :params="params"
  :first-col-label="$t('StudyInterventionTypeSummary.intervention_type_info')"
  persistent-dialog
  copy-from-study
  component="studyIntervention"
  >
  <template v-slot:form="{ closeHandler, dataToCopy, openHandler }">
    <intervention-type-form :open="openHandler" :metadata="(Object.keys(dataToCopy).length !== 0) ? dataToCopy : metadata" @updated="onMetadataUpdated" @close="closeHandler" />
  </template>
</study-metadata-summary>
</template>

<script>
import { mapGetters } from 'vuex'
import study from '@/api/study'
import InterventionTypeForm from './InterventionTypeForm'
import StudyMetadataSummary from './StudyMetadataSummary'

export default {
  components: {
    InterventionTypeForm,
    StudyMetadataSummary
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
          label: this.$t('StudyInterventionTypeForm.intervention_type'),
          name: 'interventionTypeCode',
          valuesDisplay: 'term'
        },
        {
          label: this.$t('StudyDefineForm.studyintent'),
          name: 'trialIntentTypesCodes',
          valuesDisplay: 'terms'
        },
        {
          label: this.$t('StudyInterventionTypeForm.added_to_et'),
          name: 'addOnToExistingTreatments',
          valuesDisplay: 'yesno'
        },
        {
          label: this.$t('StudyInterventionTypeForm.control_type'),
          name: 'controlTypeCode',
          valuesDisplay: 'term'
        },
        {
          label: this.$t('StudyInterventionTypeForm.intervention_model'),
          name: 'interventionModelCode',
          valuesDisplay: 'term'
        },
        {
          label: this.$t('StudyInterventionTypeForm.randomised'),
          name: 'isTrialRandomised',
          valuesDisplay: 'yesno'
        },
        { label: this.$t('StudyInterventionTypeForm.strfactor'), name: 'stratificationFactor' },
        {
          label: this.$t('StudyInterventionTypeForm.blinding_schema'),
          name: 'trialBlindingSchemaCode',
          valuesDisplay: 'term'
        },
        {
          label: this.$t('StudyInterventionTypeForm.planned_st_length'),
          name: 'plannedStudyLength',
          valuesDisplay: 'duration'
        }
      ]
    }
  },
  methods: {
    onMetadataUpdated (metadata) {
      this.metadata = metadata
    }
  },
  mounted () {
    this.$store.dispatch('studiesGeneral/fetchUnits')
    this.$store.dispatch('studiesGeneral/fetchTrialBlindingSchemas')
    this.$store.dispatch('studiesGeneral/fetchControlTypes')
    this.$store.dispatch('studiesGeneral/fetchInterventionModels')
    this.$store.dispatch('studiesGeneral/fetchTrialIntentTypes')
    this.$store.dispatch('studiesGeneral/fetchInterventionTypes')
    study.getStudyInterventionMetadata(this.selectedStudy.uid).then(resp => {
      this.metadata = resp.data.currentMetadata.studyIntervention
    })
  }
}
</script>
