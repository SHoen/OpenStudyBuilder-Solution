<template>
<study-metadata-summary
  :metadata="metadata"
  :params="params"
  :first-col-label="$t('StudyTypeSummary.info_column')"
  persistent-dialog
  copy-from-study
  component="highLevelStudyDesign"
  >
  <template v-slot:form="{ closeHandler, dataToCopy, openHandler }">
    <study-define-form :open="openHandler" :metadata="(Object.keys(dataToCopy).length !== 0) ? dataToCopy : metadata" @updated="onMetadataUpdated" @close="closeHandler" />
  </template>
</study-metadata-summary>
</template>

<script>
import { mapGetters } from 'vuex'
import study from '@/api/study'
import StudyMetadataSummary from './StudyMetadataSummary'
import StudyDefineForm from './StudyDefineForm'

export default {
  components: {
    StudyMetadataSummary,
    StudyDefineForm
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
          label: this.$t('StudyDefineForm.studytype'),
          name: 'studyTypeCode',
          valuesDisplay: 'term'
        },
        {
          label: this.$t('StudyDefineForm.trialtype'),
          name: 'trialTypesCodes',
          valuesDisplay: 'terms'
        },
        {
          label: this.$t('StudyDefineForm.trialphase'),
          name: 'trialPhaseCode',
          valuesDisplay: 'term'
        },
        {
          label: this.$t('StudyDefineForm.extensiontrial'),
          name: 'isExtensionTrial',
          valuesDisplay: 'yesno'
        },
        {
          label: this.$t('StudyDefineForm.adaptivedesign'),
          name: 'isAdaptiveDesign',
          valuesDisplay: 'yesno'
        },
        {
          label: this.$t('StudyDefineForm.studystoprule'),
          name: 'studyStopRules'
        },
        {
          label: this.$t('StudyDefineForm.confirmed_resp_min_duration'),
          name: 'confirmedResponseMinimumDuration',
          valuesDisplay: 'duration'
        },
        {
          label: this.$t('StudyDefineForm.post_auth_safety_indicator'),
          name: 'postAuthIndicator',
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
  mounted () {
    this.$store.dispatch('studiesGeneral/fetchUnits')
    this.$store.dispatch('studiesGeneral/fetchStudyTypes')
    this.$store.dispatch('studiesGeneral/fetchTrialIntentTypes')
    this.$store.dispatch('studiesGeneral/fetchTrialPhases')
    this.$store.dispatch('studiesGeneral/fetchTrialTypes')
    this.$store.dispatch('studiesGeneral/fetchNullValues')
    study.getHighLevelStudyDesignMetadata(this.selectedStudy.uid).then(resp => {
      this.metadata = resp.data.currentMetadata.highLevelStudyDesign
    })
  }
}
</script>
