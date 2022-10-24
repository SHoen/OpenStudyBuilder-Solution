<template>
<simple-form-dialog
  ref="form"
  :title="title"
  :help-items="helpItems"
  :help-text="$t('_help.StudyDefineForm.general')"
  @close="cancel"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <validation-observer ref="observer">
      <v-row class="pr-4">
        <v-col cols="11">
          <validation-provider
            v-slot="{ errors }"
            name="StudyType"
            >
            <v-autocomplete
              data-cy="study-type"
              v-model="form.studyTypeCode"
              :label="$t('StudyDefineForm.studytype')"
              :items="studyTypes"
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
      <v-row class="pr-4">
        <v-col cols="11">
          <validation-provider
            v-slot="{ errors }"
            name="TrialTypes"
            >
            <multiple-select
              data-cy="trial-type"
              v-model="form.trialTypesCodes"
              :label="$t('StudyDefineForm.trialtype')"
              :items="trialTypes"
              item-text="sponsorPreferredName"
              item-value="termUid"
              return-object
              :errors="errors"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row class="pr-4">
        <v-col cols="11">
          <validation-provider
            v-slot="{ errors }"
            name="TrialPhase"
            >
            <v-select
              data-cy="study-phase-classification"
              v-model="form.trialPhaseCode"
              :label="$t('StudyDefineForm.trialphase')"
              :items="trialPhases"
              item-text="sponsorPreferredNameSentenceCase"
              item-value="termUid"
              return-object
              :error-messages="errors"
              dense
              clearable
              ></v-select>
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="5">
          <validation-provider
            v-slot="{ errors }"
            name="ExtensionTrial"
            rules="oneselected:@ExtensionTrialNullFlavor"
            >
            <yes-no-field
              data-cy="extension-study"
              v-model="form.isExtensionTrial"
              :error-messages="errors"
              :label="$t('StudyDefineForm.extensiontrial')"
              />
          </validation-provider>
        </v-col>
        <v-col cols="5">
          <validation-provider
            v-slot="{ errors }"
            name="AdaptiveDesign"
            >
            <yes-no-field
              data-cy="adaptive-design"
              v-model="form.isAdaptiveDesign"
              :error-messages="errors"
              :label="$t('StudyDefineForm.adaptivedesign')"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row class="pr-4 mb-4">
        <v-col cols="11">
          <validation-provider
            v-slot="{ errors }"
            name="StudyStopRules"
            >
            <v-text-field
              data-cy="stop-rule"
              v-model="form.studyStopRules"
              :label="$t('StudyDefineForm.studystoprule')"
              :error-messages="errors"
              dense
              clearable
              :disabled="stopRulesNone"
              ></v-text-field>
          </validation-provider>
        </v-col>
        <v-col cols="1">
          <v-checkbox
            v-model="stopRulesNone"
            :label="$t('StudyDefineForm.none')"
            hide-details
            @change="updateStopRules"
            />
        </v-col>
      </v-row>
      <not-applicable-field
        :label="$t('StudyDefineForm.confirmed_resp_min_duration')"
        data-cy="confirmed-resp-min-dur-field"
        :clean-function="setNullValueConfirmedDuration"
        :checked="form.confirmedResponseMinimumDurationNullValueCode ? true : false"
        >
        <template v-slot:mainField="{ notApplicable }">
          <duration-field
            data-cy="confirmed-resp-min-dur"
            v-model="form.confirmedResponseMinimumDuration"
            numericFieldName="durationValue"
            unitFieldName="durationUnitCode"
            :disabled="notApplicable"
            />
        </template>
      </not-applicable-field>
      <v-row class="mt-4">
        <v-col cols="9">
          <validation-provider
            v-slot="{ errors }"
            name="PostAuthIndicator"
            >
            <yes-no-field
              data-cy="post-auth-safety-indicator"
              v-model="form.postAuthIndicator"
              :error-messages="errors"
              :label="$t('StudyDefineForm.post_auth_safety_indicator')"
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
import { bus } from '@/main'
import { mapGetters } from 'vuex'
import { studyMetadataFormMixin } from '@/mixins/studyMetadataForm'
import DurationField from '@/components/tools/DurationField'
import MultipleSelect from '@/components/tools/MultipleSelect'
import NotApplicableField from '@/components/tools/NotApplicableField'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import studyConstants from '@/constants/study'
import YesNoField from '@/components/tools/YesNoField'

export default {
  mixins: [studyMetadataFormMixin],
  components: {
    DurationField,
    MultipleSelect,
    NotApplicableField,
    SimpleFormDialog,
    YesNoField
  },
  props: {
    metadata: Object,
    open: Boolean
  },
  data () {
    return {
      form: {},
      helpItems: [
        'StudyDefineForm.studytype',
        'StudyDefineForm.studyintent',
        'StudyDefineForm.trialtype',
        'StudyDefineForm.trialphase',
        'StudyDefineForm.extensiontrial',
        'StudyDefineForm.adaptivedesign',
        'StudyDefineForm.studystoprule',
        'StudyDefineForm.confirmed_resp_min_duration',
        'StudyDefineForm.post_auth_safety_indicator'
      ],
      data: this.metadata,
      stopRulesNone: false
    }
  },
  computed: {
    title () {
      return this.$t('StudyDefineForm.title')
    },
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyTypes: 'studiesGeneral/studyTypes',
      trialIntentTypes: 'studiesGeneral/trialIntentTypes',
      trialTypes: 'studiesGeneral/trialTypes',
      trialPhases: 'studiesGeneral/trialPhases'
    })
  },
  methods: {
    setNullValueConfirmedDuration () {
      this.$set(this.form, 'confirmedResponseMinimumDuration', {})
      if (this.form.confirmedResponseMinimumDurationNullValueCode) {
        this.$set(this.form, 'confirmedResponseMinimumDurationNullValueCode', null)
      } else {
        this.$set(this.form, 'confirmedResponseMinimumDurationNullValueCode', { termUid: this.$t('_global.na_uid'), name: this.$t('_global.not_applicable_full_name') })
      }
    },
    close () {
      this.$emit('close')
      this.$refs.observer.reset()
    },
    prepareRequestPayload () {
      const data = { ...this.form }
      if (!data.confirmedResponseMinimumDuration.durationValue) {
        data.confirmedResponseMinimumDuration = null
      }
      data.studyTypeCode = this.getTermPayload('studyTypeCode')
      data.trialIntentTypesCodes = this.getTermsPayload('trialIntentTypesCodes')
      data.trialTypesCodes = this.getTermsPayload('trialTypesCodes')
      data.trialPhaseCode = this.getTermPayload('trialPhaseCode')
      if (this.stopRulesNone) {
        data.studyStopRules = studyConstants.STOP_RULE_NONE
      }
      return data
    },
    async cancel () {
      if (_isEqual(this.metadata, this.prepareRequestPayload())) {
        this.close()
        return
      }
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue')
      }
      if (await this.$refs.form.confirm(this.$t('_global.cancel_changes'), options)) {
        this.data = {}
        this.data = this.metadata
        this.close()
      }
    },
    async submit () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      this.$refs.form.working = true
      const data = this.prepareRequestPayload()
      try {
        await this.$store.dispatch('manageStudies/editStudyType', [this.selectedStudy.uid, data])
        this.$emit('updated', data)
        bus.$emit('notification', { msg: this.$t('StudyDefineForm.update_success') })
        this.close()
      } finally {
        this.$refs.form.working = false
      }
    },
    updateStopRules (value) {
      if (value) {
        this.$set(this.form, 'studyStopRules', null)
      }
    }
  },
  watch: {
    data: {
      handler: function (value) {
        this.form = JSON.parse(JSON.stringify(value))
        if (!this.form.confirmedResponseMinimumDuration) {
          this.form.confirmedResponseMinimumDuration = {}
        }
        if (!this.metadata.confirmedResponseMinimumDuration) {
          this.metadata.confirmedResponseMinimumDuration = null
        }
        if (this.metadata.studyStopRules === studyConstants.STOP_RULE_NONE) {
          this.stopRulesNone = true
        }
      },
      immediate: true
    },
    metadata (value) {
      this.data = value
    }
  }
}
</script>
