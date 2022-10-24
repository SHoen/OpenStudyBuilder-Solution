<template>
<simple-form-dialog
  ref="form"
  :title="$t('StudyPopulationForm.title')"
  :help-items="helpItems"
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
            name="TherapeuticArea"
            rules=""
            >
            <multiple-select
              v-model="form.therapeuticAreasCodes"
              :data-cy="$t('StudyPopulationForm.therapeuticarea')"
              :label="$t('StudyPopulationForm.therapeuticarea')"
              :items="snomedTerms"
              item-text="name"
              item-value="termUid"
              return-object
              :errors="errors"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <not-applicable-field
        :clean-function="setNullValueStudyDisease"
        :checked="form.diseaseConditionsOrIndicationsNullValueCode ? true : false"
        >
        <template v-slot:mainField="{ notApplicable }">
          <multiple-select
            :data-cy="$t('StudyPopulationForm.disease_condition')"
            :label="$t('StudyPopulationForm.disease_condition')"
            :disabled="notApplicable"
            v-model="form.diseaseConditionsOrIndicationsCodes"
            :items="snomedTerms"
            item-value="termUid"
            item-text="name"
            return-object
            />
        </template>
      </not-applicable-field>
      <not-applicable-field
        :label=" $t('StudyPopulationForm.stable_disease_min_duration')"
        :clean-function="setNullValueDiseaseDuration"
        :checked="form.stableDiseaseMinimumDurationNullValueCode ? true : false"
        >
        <template v-slot:mainField="{ notApplicable }">
          <duration-field
            data-cy="stable-disease-min-duration"
            class="unit-select"
            v-model="form.stableDiseaseMinimumDuration"
            :disabled="notApplicable"
            />
        </template>
      </not-applicable-field>
      <validation-provider
        v-slot="{ errors }"
        >
        <v-row class="pr-4">
          <v-col cols="11">
            <multiple-select
              :data-cy="$t('StudyPopulationForm.diagnosis_group')"
              v-model="form.diagnosisGroupsCodes"
              :label="$t('StudyPopulationForm.diagnosis_group')"
              :items="snomedTerms"
              item-value="termUid"
              item-text="name"
              :errors="errors"
              return-object
              />
          </v-col>
        </v-row>
      </validation-provider>
      <not-applicable-field
        :clean-function="setNullValueRelapseCriteria"
        :checked="form.relapseCriteriaNullValueCode ? true : false"
        >
        <template v-slot:mainField="{ notApplicable }">
          <v-text-field
            :data-cy="$t('StudyPopulationForm.relapse_criteria')"
            v-model="form.relapseCriteria"
            :label="$t('StudyPopulationForm.relapse_criteria')"
            class="pt-0 my-0"
            :disabled="notApplicable"
            />
        </template>
      </not-applicable-field>
      <v-row>
        <v-col cols="4">
          <v-text-field
            :data-cy="$t('StudyPopulationForm.number_of_expected_subjects')"
            v-model="form.numberOfExpectedSubjects"
            :label="$t('StudyPopulationForm.number_of_expected_subjects')"
            :hint="$t('StudyPopulationForm.number_of_expected_subjects_hint')"
            class="pt-0 my-0"
            type="number"
            />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="4">
          <validation-provider
            v-slot="{ errors }"
            name="HealthySubjects"
            rules=""
            >
            <yes-no-field
              :data-cy="$t('StudyPopulationForm.healthy_subjects')"
              v-model="form.healthySubjectIndicator"
              :error-messages="errors"
              :label="$t('StudyPopulationForm.healthy_subjects')"
              />
          </validation-provider>
        </v-col>
        <v-col cols="5">
          <validation-provider
            v-slot="{ errors }"
            name="RareDiseaseIndicator"
            rules=""
            >
            <yes-no-field
              :data-cy="$t('StudyPopulationForm.rare_disease_indicator')"
              v-model="form.rareDiseaseIndicator"
              :error-messages="errors"
              :label="$t('StudyPopulationForm.rare_disease_indicator')"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row class="pr-4">
        <v-col cols="11">
          <validation-provider
            v-slot="{ errors }"
            >
            <v-select
              :data-cy="$t('StudyPopulationForm.sex_of_study_participants')"
              v-model="form.sexOfParticipantsCode"
              :label="$t('StudyPopulationForm.sex_of_study_participants')"
              :items="sexOfParticipants"
              item-value="termUid"
              item-text="sponsorPreferredName"
              return-object
              dense
              :errors="errors"
              clearable
              hide-details="auto"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <div class="mt-10">
        <label class="v-label">
          {{ $t('StudyPopulationForm.planned_min_max_age') }}
        </label>
      </div>
      <not-applicable-field
        :na-label="$t('StudyPopulationForm.pinf')"
        :clean-function="setPositiveInfinity"
        :checked="form.plannedMaximumAgeOfSubjectsNullValueCode ? true : false"
        >
        <template v-slot:mainField="{ notApplicable }">
          <v-row>
            <v-col cols="6">
              <validation-provider
                v-slot="{ errors }"
                name="PlannedMinAge"
                rules=""
                >
                <duration-field
                  data-cy="planned-minimum-age"
                  v-model="form.plannedMinimumAgeOfSubjects"
                  :errors="errors"
                  numeric-field-name="durationValue"
                  unit-field-name="durationUnitCode"
                  :hint="$t('StudyPopulationForm.planned_min_age')"
                  />
              </validation-provider>
            </v-col>
            <v-col cols="6">
              <validation-provider
                v-slot="{ errors }"
                name="PlannedMaxAge"
                rules=""
                >
                <duration-field
                  data-cy="planned-maximum-age"
                  v-model="form.plannedMaximumAgeOfSubjects"
                  :errors="errors"
                  numeric-field-name="durationValue"
                  unit-field-name="durationUnitCode"
                  :disabled="notApplicable"
                  :hint="$t('StudyPopulationForm.planned_max_age')"
                  />
              </validation-provider>
            </v-col>
          </v-row>
        </template>
      </not-applicable-field>
      <v-row>
        <v-col cols="4">
          <validation-provider
            v-slot="{ errors }"
            name="PediatricStudyIndicator"
            rules=""
            >
            <yes-no-field
              :data-cy="$t('StudyPopulationForm.pediatric_study_indicator')"
              v-model="form.pediatricStudyIndicator"
              :error-messages="errors"
              :label="$t('StudyPopulationForm.pediatric_study_indicator')"
              />
          </validation-provider>
        </v-col>
        <v-col cols="5">
          <validation-provider
            v-slot="{ errors }"
            name="PediatricInvestigationPlanIndicator"
            rules=""
            >
            <yes-no-field
              :data-cy="$t('StudyPopulationForm.pediatric_investigation_plan_indicator')"
              v-model="form.pediatricInvestigationPlanIndicator"
              :error-messages="errors"
              :label="$t('StudyPopulationForm.pediatric_investigation_plan_indicator')"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="9">
          <validation-provider
            v-slot="{ errors }"
            name="PediatricPostmarketStudyIndicator"
            rules=""
            >
            <yes-no-field
              :data-cy="$t('StudyPopulationForm.pediatric_postmarket_study_indicator')"
              v-model="form.pediatricPostmarketStudyIndicator"
              :error-messages="errors"
              :label="$t('StudyPopulationForm.pediatric_postmarket_study_indicator')"
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
    MultipleSelect,
    NotApplicableField,
    SimpleFormDialog,
    YesNoField
  },
  props: {
    metadata: Object,
    open: Boolean
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      snomedTerms: 'studiesGeneral/snomedTerms',
      sexOfParticipants: 'studiesGeneral/sexOfParticipants',
      units: 'studiesGeneral/units',
      nullValues: 'studiesGeneral/nullValues'
    })
  },
  data () {
    return {
      form: {
        plannedMinimumAgeOfSubjects: {},
        plannedMaximumAgeOfSubjects: {},
        plannedMinimumDuration: {}
      },
      helpItems: [
        'StudyPopulationForm.therapeuticarea',
        'StudyPopulationForm.disease_condition',
        'StudyPopulationForm.diagnosis_group',
        'StudyPopulationForm.rare_disease_indicator',
        'StudyPopulationForm.healthy_subjects',
        'StudyPopulationForm.planned_min_max_age',
        'StudyPopulationForm.pediatric_study_indicator',
        'StudyPopulationForm.pediatric_postmarket_study_indicator',
        'StudyPopulationForm.stable_disease_min_duration',
        'StudyPopulationForm.relapse_criteria',
        'StudyPopulationForm.number_of_expected_subjects',
        'StudyPopulationForm.sex_of_study_participants'
      ],
      minimumDurationCheckbox: false,
      data: this.metadata
    }
  },
  mounted () {
    this.$store.dispatch('studiesGeneral/fetchNullValues')
  },
  methods: {
    setNullValueStudyDisease () {
      this.$set(this.form, 'diseaseConditionsOrIndicationsCodes', [])
      if (this.form.diseaseConditionsOrIndicationsNullValueCode) {
        this.$set(this.form, 'diseaseConditionsOrIndicationsNullValueCode', null)
      } else {
        this.$set(this.form, 'diseaseConditionsOrIndicationsNullValueCode', { termUid: this.$t('_global.na_uid'), name: this.$t('_global.not_applicable_full_name') })
      }
    },
    setNullValueDiseaseDuration () {
      this.$set(this.form, 'stableDiseaseMinimumDuration', {})
      if (this.form.stableDiseaseMinimumDurationNullValueCode) {
        this.$set(this.form, 'stableDiseaseMinimumDurationNullValueCode', null)
      } else {
        this.$set(this.form, 'stableDiseaseMinimumDurationNullValueCode', { termUid: this.$t('_global.na_uid'), name: this.$t('_global.not_applicable_full_name') })
      }
    },
    setNullValueRelapseCriteria () {
      this.$set(this.form, 'relapseCriteria', '')
      if (this.form.relapseCriteriaNullValueCode) {
        this.$set(this.form, 'relapseCriteriaNullValueCode', null)
      } else {
        this.$set(this.form, 'relapseCriteriaNullValueCode', { termUid: this.$t('_global.na_uid'), name: this.$t('_global.not_applicable_full_name') })
      }
    },
    setNullValueNumberOfExpectedSubjects () {
      this.$set(this.form, 'numberOfExpectedSubjects', '')
      if (this.form.numberOfExpectedSubjectsNullValueCode) {
        this.$set(this.form, 'numberOfExpectedSubjectsNullValueCode', null)
      } else {
        this.$set(this.form, 'numberOfExpectedSubjectsNullValueCode', { termUid: this.$t('_global.na_uid'), name: this.$t('_global.not_applicable_full_name') })
      }
    },
    setPositiveInfinity () {
      this.$set(this.form, 'plannedMaximumAgeOfSubjects', {})
      if (this.form.plannedMaximumAgeOfSubjectsNullValueCode) {
        this.$set(this.form, 'plannedMaximumAgeOfSubjectsNullValueCode', null)
      } else {
        this.$set(this.form, 'plannedMaximumAgeOfSubjectsNullValueCode', { termUid: this.nullValues.find(el => el.sponsorPreferredName === 'Positive infinity').termUid, name: this.$t('_global.positive_infinity_full_name') })
      }
    },
    close () {
      this.$emit('close')
      this.$refs.observer.reset()
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
    prepareRequestPayload () {
      const data = JSON.parse(JSON.stringify(this.form))
      if (Object.keys(data.plannedMinimumAgeOfSubjects).length === 0 || !data.plannedMinimumAgeOfSubjects.durationValue) {
        data.plannedMinimumAgeOfSubjects = null
      }
      if (Object.keys(data.plannedMaximumAgeOfSubjects).length === 0 || !data.plannedMaximumAgeOfSubjects.durationValue) {
        data.plannedMaximumAgeOfSubjects = null
      }
      if (Object.keys(data.stableDiseaseMinimumDuration).length === 0 || !data.stableDiseaseMinimumDuration.durationValue) {
        data.stableDiseaseMinimumDuration = null
      }
      if (!data.numberOfExpectedSubjects) {
        data.numberOfExpectedSubjects = null
      }
      data.sexOfParticipantsCode = this.getTermPayload('sexOfParticipantsCode')
      data.therapeuticAreasCodes = this.getTermsPayload('therapeuticAreasCodes')
      data.diseaseConditionsOrIndicationsCodes = this.getTermsPayload('diseaseConditionsOrIndicationsCodes')
      data.diagnosisGroupsCodes = this.getTermsPayload('diagnosisGroupsCodes')
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
        await this.$store.dispatch('manageStudies/editStudyPopulation', [this.selectedStudy.uid, data])
        this.$emit('updated', data)
        bus.$emit('notification', { msg: this.$t('StudyPopulationForm.update_success') })
        this.close()
      } finally {
        this.$refs.form.working = false
      }
    }
  },
  watch: {
    minimumDurationCheckbox: function () {
      this.form.stableDiseaseMinimumDuration = {}
    },
    data: {
      handler: function (value) {
        this.form = JSON.parse(JSON.stringify(value))
        if (!this.form.plannedMinimumAgeOfSubjects) {
          this.form.plannedMinimumAgeOfSubjects = {}
        }
        if (!this.form.plannedMaximumAgeOfSubjects) {
          this.form.plannedMaximumAgeOfSubjects = {}
        }
        if (!this.form.stableDiseaseMinimumDuration) {
          this.form.stableDiseaseMinimumDuration = {}
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
