<template>
<div>
  <n-n-table
    :headers="headers"
    :items="computedParams"
    item-key="name"
    export-object-label="Metadata"
    :itemsPerPage="15"
    has-history
    disable-filtering
    >
    <template v-slot:actions="">
      <v-btn
        v-if="copyFromStudy"
        color="primary"
        data-cy="copy-from-study"
        fab
        small
        @click.stop="openCopyForm"
        :title="$t('NNTableTooltips.copy_from_study')"
        >
        <v-icon>mdi-content-copy</v-icon>
      </v-btn>
      <v-btn
        fab
        small
        class="ml-2"
        color="primary"
        @click.stop="openForm"
        :title="$t('NNTableTooltips.edit_content')"
        data-cy="edit-content"
        >
        <v-icon>
          mdi-pencil
        </v-icon>
      </v-btn>
    </template>
  </n-n-table>
  <slot name="form" :openHandler="showForm" v-bind:closeHandler="closeForm" v-bind:data="metadata" v-bind:dataToCopy="dataToCopy"></slot>

  <v-dialog
    v-model="showCopyForm"
    persistent
    max-width="500px"
    >
    <copy-from-study-form  @close="closeCopyForm" @apply="openFormToCopy" :component="component"/>
  </v-dialog>
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import NNTable from '@/components/tools/NNTable'
import CopyFromStudyForm from '@/components/tools/CopyFromStudyForm'

export default {
  components: {
    NNTable,
    CopyFromStudyForm
  },
  props: {
    params: Array,
    metadata: Object,
    firstColLabel: String,
    persistentDialog: {
      type: Boolean,
      default: false
    },
    formMaxWidth: {
      type: String,
      required: false
    },
    copyFromStudy: {
      type: Boolean,
      default: false
    },
    component: String
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyTypes: 'studiesGeneral/studyTypes',
      trialIntentTypes: 'studiesGeneral/trialIntentTypes',
      trialTypes: 'studiesGeneral/trialTypes',
      trialPhases: 'studiesGeneral/trialPhases',
      therapeuticAreas: 'studiesGeneral/therapeuticAreas',
      diseaseConditions: 'studiesGeneral/diseaseConditions',
      sexOfParticipants: 'studiesGeneral/sexOfParticipants',
      diagnosisGroups: 'studiesGeneral/diagnosisGroups',
      controlTypes: 'studiesGeneral/controlTypes',
      interventionModels: 'studiesGeneral/interventionModels',
      trialBlindingSchemas: 'studiesGeneral/trialBlindingSchemas',
      nullValues: 'studiesGeneral/nullValues'
    }),
    computedParams () {
      return this.buildTableParams(this.params)
    }
  },
  data () {
    return {
      headers: [
        { text: this.firstColLabel, value: 'name', width: '30%' },
        { text: this.$t('StudyMetadataSummary.selected_values'), value: 'values' },
        { text: this.$t('StudyMetadataSummary.reason_for_missing'), value: 'reasonForMissing' }
      ],
      showForm: false,
      showCopyForm: false,
      dataToCopy: {}
    }
  },
  methods: {
    openForm () {
      this.showForm = true
    },
    closeForm () {
      this.showForm = false
    },
    openFormToCopy (data) {
      this.dataToCopy = data
      this.showForm = true
      this.showCopyForm = false
    },
    openCopyForm () {
      this.showCopyForm = true
    },
    closeCopyForm () {
      this.showCopyForm = false
    },
    buildTableParams (fields) {
      const result = []
      fields.forEach(field => {
        let nullValueName = null
        if (field.nullValueName === undefined) {
          nullValueName = field.name
          const suffixes = ['Code', 'Codes']
          suffixes.forEach(suffix => {
            if (nullValueName.endsWith(suffix)) {
              nullValueName = nullValueName.replace(suffix, '')
            }
          })
          nullValueName += 'NullValueCode'
        } else {
          nullValueName = field.nullValueName
        }
        let values = this.metadata[field.name]
        if (field.name === 'sexOfParticipantsCode' && values !== undefined && values !== null) {
          values = values.name
        }
        result.push({
          name: field.label,
          values: (values !== undefined && values !== null && field.valuesDisplay && field.name !== 'sexOfParticipantsCode') ? this[`${field.valuesDisplay}Display`](values) : values,
          reasonForMissing: this.naDisplay(this.metadata[nullValueName])
        })
      })
      return result
    },
    yesnoDisplay (value) {
      return (value) ? this.$t('_global.yes') : this.$t('_global.no')
    },
    durationDisplay (value) {
      return `${value.durationValue} ${value.durationUnitCode.name}`
    },
    termDisplay (value) {
      if (!value) {
        return ''
      }
      return value.name
    },
    termsDisplay (value) {
      const result = value.map(item => item.name)
      return result.join(', ')
    },
    naDisplay (value) {
      if (value) {
        return value.name
      }
    }
  }
}
</script>
