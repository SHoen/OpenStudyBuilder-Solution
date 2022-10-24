<template>
<simple-form-dialog
  ref="form"
  :title="$t('StudyInterventionTypeForm.title')"
  :help-items="helpItems"
  :help-text="$t('_help.StudyInterventionTypeForm.general')"
  @close="cancel"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <validation-observer ref="observer">
      <v-row>
        <v-col cols="11">
          <validation-provider
            v-slot="{ errors }"
            name="InterventionType"
            >
            <v-autocomplete
              :data-cy="$t('StudyInterventionTypeForm.intervention_type')"
              v-model="form.interventionTypeCode"
              :label="$t('StudyInterventionTypeForm.intervention_type')"
              :items="interventionTypes"
              item-text="sponsorPreferredName"
              item-value="termUid"
              return-object
              :error-messages="errors"
              dense
              clearable
              ></v-autocomplete>
          </validation-provider>
        </v-col>
      </v-row>
      <not-applicable-field
        :clean-function="setNullValueTrialIntentTypesCodes"
        :checked="form.trialIntentTypesNullValueCode ? true : false"
        >
        <template v-slot:mainField="{ notApplicable }">
          <multiple-select
            :data-cy="$t('StudyDefineForm.studyintent')"
            v-model="form.trialIntentTypesCodes"
            :label="$t('StudyDefineForm.studyintent')"
            :items="trialIntentTypes"
            item-text="sponsorPreferredName"
            item-value="termUid"
            return-object
            :disabled="notApplicable"
            dense
            clearable
            />
        </template>
      </not-applicable-field>
      <v-row>
        <v-col cols="11">
          <validation-provider
            v-slot="{ errors }"
            name="ControlType"
            >
            <v-autocomplete
              :data-cy="$t('StudyInterventionTypeForm.control_type')"
              v-model="form.controlTypeCode"
              :label="$t('StudyInterventionTypeForm.control_type')"
              :items="controlTypes"
              item-text="sponsorPreferredName"
              item-value="termUid"
              return-object
              :error-messages="errors"
              dense
              clearable
              ></v-autocomplete>
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="11">
          <validation-provider
            v-slot="{ errors }"
            name="InterventionModel"
            >
            <v-autocomplete
              :data-cy="$t('StudyInterventionTypeForm.intervention_model')"
              v-model="form.interventionModelCode"
              :label="$t('StudyInterventionTypeForm.intervention_model')"
              :items="interventionModels"
              item-text="sponsorPreferredName"
              item-value="termUid"
              return-object
              :error-messages="errors"
              dense
              clearable
              ></v-autocomplete>
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="5">
          <validation-provider
            v-slot="{ errors }"
            name="Randomised"
            >
            <yes-no-field
              :data-cy="$t('StudyInterventionTypeForm.randomised')"
              v-model="form.isTrialRandomised"
              :error-messages="errors"
              :label="$t('StudyInterventionTypeForm.randomised')"
              />
          </validation-provider>
        </v-col>
        <v-col cols="5">
          <validation-provider
            v-slot="{ errors }"
            name="AddedToExistingTreatments"
            >
            <yes-no-field
              :data-cy="$t('StudyInterventionTypeForm.added_to_et')"
              v-model="form.addOnToExistingTreatments"
              :error-messages="errors"
              :label="$t('StudyInterventionTypeForm.added_to_et')"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="11">
          <validation-provider
            v-slot="{ errors }"
            name="BlindingSchema"
            >
            <v-autocomplete
              :data-cy="$t('StudyInterventionTypeForm.blinding_schema')"
              v-model="form.trialBlindingSchemaCode"
              :label="$t('StudyInterventionTypeForm.blinding_schema')"
              :items="trialBlindingSchemas"
              item-text="sponsorPreferredName"
              item-value="termUid"
              return-object
              :error-messages="errors"
              dense
              clearable
              ></v-autocomplete>
          </validation-provider>
        </v-col>
      </v-row>
      <not-applicable-field
        :clean-function="setNullValueStratificationFactor"
        :checked="form.stratificationFactorNullValueCode ? true : false"
        >
        <template v-slot:mainField="{ notApplicable }">
          <v-text-field
            :data-cy="$t('StudyInterventionTypeForm.strfactor')"
            :label="$t('StudyInterventionTypeForm.strfactor')"
            :disabled="notApplicable"
            v-model="form.stratificationFactor"
            dense
            clearable
            ></v-text-field>
        </template>
      </not-applicable-field>
      <v-row>
        <v-col cols="10">
          <label class="v-label theme--light">{{ $t('StudyInterventionTypeForm.planned_st_length') }}</label>
          <validation-provider
            v-slot="{ errors }"
            name="PlannedStudyLength"
            >
            <duration-field
              data-cy="planned-study-length"
              v-model="form.plannedStudyLength"
              :errors="errors"
              numericFieldName="durationValue"
              unitFieldName="durationUnitCode"
              :max="1000"
              />
          </validation-provider>
        </v-col>
      </v-row>
    </validation-observer>
  </template>
</simple-form-dialog>
</template>

<script>
import _isEqual from 'lodash/isEqual'
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import { studyMetadataFormMixin } from '@/mixins/studyMetadataForm'
import DurationField from '@/components/tools/DurationField'
import MultipleSelect from '@/components/tools/MultipleSelect'
import NotApplicableField from '@/components/tools/NotApplicableField'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import YesNoField from '@/components/tools/YesNoField'

export default {
  mixins: [studyMetadataFormMixin],
  components: {
    DurationField,
    NotApplicableField,
    SimpleFormDialog,
    YesNoField,
    MultipleSelect
  },
  props: {
    metadata: Object,
    open: Boolean
  },
  computed: {
    ...mapGetters({
      controlTypes: 'studiesGeneral/controlTypes',
      interventionModels: 'studiesGeneral/interventionModels',
      selectedStudy: 'studiesGeneral/selectedStudy',
      trialBlindingSchemas: 'studiesGeneral/trialBlindingSchemas',
      interventionTypes: 'studiesGeneral/interventionTypes',
      trialIntentTypes: 'studiesGeneral/trialIntentTypes'
    })
  },
  data () {
    return {
      form: {},
      helpItems: [
        'StudyInterventionTypeForm.intervention_type',
        'StudyInterventionTypeForm.study_intent_type',
        'StudyInterventionTypeForm.added_to_et',
        'StudyInterventionTypeForm.control_type',
        'StudyInterventionTypeForm.intervention_model',
        'StudyInterventionTypeForm.randomised',
        'StudyInterventionTypeForm.strfactor',
        'StudyInterventionTypeForm.blinding_schema',
        'StudyInterventionTypeForm.planned_st_length'
      ],
      data: this.metadata
    }
  },
  methods: {
    setNullValueTrialIntentTypesCodes () {
      this.$set(this.form, 'trialIntentTypesCodes', [])
      if (this.form.trialIntentTypesNullValueCode) {
        this.$set(this.form, 'trialIntentTypesNullValueCode', null)
      } else {
        this.$set(this.form, 'trialIntentTypesNullValueCode', { termUid: this.$t('_global.na_uid'), name: this.$t('_global.not_applicable_full_name') })
      }
    },
    setNullValueStratificationFactor () {
      this.$set(this.form, 'stratificationFactor', '')
      if (this.form.diseaseConditionsOrIndicationsNullValueCode) {
        this.$set(this.form, 'stratificationFactorNullValueCode', null)
      } else {
        this.$set(this.form, 'stratificationFactorNullValueCode', { termUid: this.$t('_global.na_uid'), name: this.$t('_global.not_applicable_full_name') })
      }
    },
    close () {
      this.$emit('close')
      this.$store.commit('form/CLEAR_FORM')
      this.$refs.observer.reset()
    },
    async cancel () {
      if (this.$store.getters['form/form'] === '' || _isEqual(this.$store.getters['form/form'], JSON.stringify(this.form))) {
        this.close()
      } else {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue')
        }
        if (await this.$refs.form.confirm(this.$t('_global.cancel_changes'), options)) {
          this.close()
        }
      }
    },
    prepareRequestPayload () {
      const data = JSON.parse(JSON.stringify(this.form))
      if (data.plannedStudyLength.durationValue === undefined) {
        data.plannedStudyLength = null
      }
      data.controlTypeCode = this.getTermPayload('controlTypeCode')
      data.interventionModelCode = this.getTermPayload('interventionModelCode')
      data.trialBlindingSchemaCode = this.getTermPayload('trialBlindingSchemaCode')
      data.interventionTypeCode = this.getTermPayload('interventionTypeCode')
      data.trialIntentTypesCodes = this.getTermsPayload('trialIntentTypesCodes')
      return data
    },
    async submit () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      const data = this.prepareRequestPayload()
      this.$refs.form.working = true
      try {
        await this.$store.dispatch('manageStudies/updateStudyIntervention', [this.selectedStudy.uid, data])
        this.$emit('updated', data)
        bus.$emit('notification', { msg: this.$t('StudyInterventionTypeForm.update_success') })
        this.close()
      } finally {
        this.$refs.form.working = false
      }
    }
  },
  watch: {
    data: {
      handler: function (value) {
        this.form = JSON.parse(JSON.stringify(value))
        if (!this.form.plannedStudyLength) {
          this.form.plannedStudyLength = {}
        }
        if (!this.metadata.plannedStudyLength) {
          this.metadata.plannedStudyLength = null
        }
        this.$store.commit('form/SET_FORM', this.form)
      },
      immediate: true
    },
    metadata (value) {
      this.data = value
    }
  }
}
</script>
