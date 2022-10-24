<template>
<div>
  <stepper-form
    :title="title"
    :steps="steps"
    @close="close"
    @save="submit"
    :form-observer-getter="getObserver"
    ref="stepper"
    data-cy="form-body"
    :help-items="helpItems"
    :editData="form"
    @change="onTabChange"
    >
    <template v-slot:step.visitType="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <v-row>
            <v-col>
              <v-radio-group
                v-model="form.visitClass"
                :error-messages="errors"
                >
                <v-radio
                  v-for="visitClass in visitClasses"
                  :key="visitClass.value"
                  :label="visitClass.label"
                  :value="visitClass.value"
                  :data-cy="visitClass.value"
                  />
              </v-radio-group>
            </v-col>
          </v-row>
        </validation-provider>
      </validation-observer>
    </template>
    <template v-slot:step.epoch="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <v-row>
            <v-col>
              <v-autocomplete
                v-model="studyEpoch"
                data-cy="study-period"
                :label="$t('StudyVisitForm.period')"
                :items="filteredPeriods"
                item-text="epochName"
                item-value="uid"
                :error-messages="errors"
                clearable
                :loading="loading"
                :disabled="studyVisit"
                />
            </v-col>
          </v-row>
        </validation-provider>
      </validation-observer>
    </template>
    <template v-slot:step.details="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <div class="sub-title">{{ $t('StudyVisitForm.timing') }}</div>
        <v-row>
          <v-col cols="4">
            <v-checkbox
              v-model="batchCreateVisits"
              :label="$t('StudyVisitForm.batch_create_visits')"
              :disabled="true"
              />
          </v-col>
          <v-col cols="4">
            <v-text-field
              v-if="batchCreateVisits"
              v-model="visitCount"
              :label="$t('StudyVisitForm.batch_create_visit_count')"
              type="number"
              />
          </v-col>

        </v-row>
        <v-row>
          <v-col cols="12" v-if="form.visitClass === visitConstants.CLASS_SINGLE_VISIT">
            <v-radio-group
              v-model="form.visitSubclass"
              row
              hide-details
            >
              <v-radio
                :label="$t('StudyVisitForm.single_visit')"
                data-cy="single-visit"
                :value="visitConstants.SUBCLASS_SINGLE_VISIT"
              ></v-radio>
              <v-radio
                :label="$t('StudyVisitForm.anchor_visit_in_group')"
                data-cy="anchor-visit-in-visit-group"
                :value="visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV"
              ></v-radio>
              <v-radio
                v-if="!displayAnchorVisitFlag && anchorVisitsInSubgroup.length"
                :label="$t('StudyVisitForm.additional_sub_visit')"
                :value="visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV"
              ></v-radio>
            </v-radio-group>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="4">
            <validation-provider
              v-slot="{ errors }"
              rules="required"
              >
              <v-autocomplete
                v-model="form.visitTypeUid"
                :label="$t('StudyVisitForm.visit_type')"
                data-cy="visit-type"
                :items="visitTypes"
                item-text="visit_type_name"
                item-value="visit_type_uid"
                :error-messages="errors"
                clearable
                :disabled="form.visitClass !== visitConstants.CLASS_SINGLE_VISIT"
                />
            </validation-provider>
          </v-col>
          <v-col cols="4">
            <validation-provider
              v-slot="{ errors }"
              rules="required"
              >
              <v-autocomplete
                v-model="form.visitContactModeUid"
                :label="$t('StudyVisitForm.contact_mode')"
                data-cy="contact-mode"
                :items="contactModes"
                item-text="sponsorPreferredName"
                item-value="termUid"
                :error-messages="errors"
                @change="getVisitPreview"
                clearable
                />
            </validation-provider>
          </v-col>
          <v-col cols="4">
            <div class="d-flex">
              <v-checkbox
                v-if="displayAnchorVisitFlag"
                v-model="form.isGlobalAnchorVisit"
                :label="$t('StudyVisitForm.anchor_visit')"
                data-cy="anchor-visit-checkbox"
                :hint="$t('StudyVisitForm.anchor_visit_hint')"
                persistent-hint
                :disabled="batchCreateVisits"
                />
              <v-text-field
                :label="$t('StudyVisitForm.current_anchor_visit')"
                v-model="currentAnchorVisit"
                readonly
                filled
                class="ml-4"
                />
            </div>
          </v-col>
        </v-row>
        <v-row v-if="form.visitClass === visitConstants.CLASS_SINGLE_VISIT">
          <v-col cols="4">
            <validation-provider
              v-slot="{ errors }"
              rules="required"
              >
              <v-autocomplete
                v-if="form.visitSubclass !== visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV"
                v-model="form.timeReferenceUid"
                :label="$t('StudyVisitForm.time_reference')"
                data-cy="time-reference"
                :items="timeReferences"
                item-text="sponsorPreferredName"
                item-value="termUid"
                :error-messages="errors"
                clearable
                @change="getVisitPreview"
                />
              <v-autocomplete
                v-else
                v-model="form.visitSubLabelReference"
                :label="$t('StudyVisitForm.time_reference')"
                data-cy="time-reference"
                :items="anchorVisitsInSubgroup"
                item-text="visitName"
                item-value="uid"
                :error-messages="errors"
                clearable
                />
            </validation-provider>
          </v-col>
          <v-col cols="4">
            <validation-provider
              v-slot="{ errors }"
              rules="required"
              >
              <v-text-field
                v-model="form.timeValue"
                type="number"
                :label="$t('StudyVisitForm.time_dist')"
                data-cy="visit-timing"
                clearable
                :error-messages="errors"
                @change="getVisitPreview"
                :disabled="disableTimeValue"
                />
            </validation-provider>
          </v-col>
          <v-col cols="4">
            <validation-provider
              v-slot="{ errors }"
              rules="required"
              >
              <v-autocomplete
                v-model="form.timeUnitUid"
                :label="$t('StudyVisitForm.time_unit_name')"
                data-cy="time-unit"
                :items="timeUnits"
                item-text="name"
                item-value="uid"
                :error-messages="errors"
                clearable
                @change="getVisitPreview"
                />
            </validation-provider>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="3">
            <v-text-field
              v-model="form.visitName"
              :label="$t('StudyVisitForm.visit_name')"
              data-cy="visit-name"
              readonly
              filled
              :loading="previewLoading"
              />
          </v-col>
          <v-col cols="3">
            <v-text-field
              v-model="form.visitShortName"
              :label="$t('StudyVisitForm.visit_short_name')"
              data-cy="visit-short-name"
              readonly
              filled
              :loading="previewLoading"
              />
          </v-col>
          <v-col cols="3" v-if="form.visitClass === visitConstants.CLASS_SINGLE_VISIT">
            <v-text-field
              v-model="form.studyDayLabel"
              :label="$t('StudyVisitForm.study_day_label')"
              data-cy="study-day-label"
              readonly
              filled
              :loading="previewLoading"
              />
          </v-col>
          <v-col cols="3" v-if="form.visitClass === visitConstants.CLASS_SINGLE_VISIT">
            <v-text-field
              v-model="form.studyWeekLabel"
              :label="$t('StudyVisitForm.study_week_label')"
              data-cy="study-week-label"
              readonly
              filled
              :loading="previewLoading"
              />
          </v-col>
        </v-row>
        <template v-if="form.visitClass === visitConstants.CLASS_SINGLE_VISIT">
          <div class="sub-title">{{ $t('StudyVisitForm.visit_window') }}</div>
          <div class="d-flex align-center">
            <div class="mr-2">
              <validation-provider
                v-slot="{ errors }"
                rules="max_value:0"
                >
                <v-row>
                  <v-col>
                    <v-text-field
                      v-model="form.minVisitWindowValue"
                      :label="$t('StudyVisitForm.visit_win_min')"
                      data-cy="visit-win-min"
                      clearable
                      :error-messages="errors"
                      type="number"
                      />
                  </v-col>
                </v-row>
              </validation-provider>
            </div>
            <div class="mr-2 secondary--text text-h4">/</div>
            <div class="mr-2">
              <validation-provider
                v-slot="{ errors }"
                rules="min_value:0"
                >
                <v-row>
                  <v-col>
                    <v-text-field
                      v-model="form.maxVisitWindowValue"
                      :label="$t('StudyVisitForm.visit_win_max')"
                      data-cy="visit-win-max"
                      clearable
                      :error-messages="errors"
                      type="number"
                      />
                  </v-col>
                </v-row>
              </validation-provider>
            </div>
            <div>
              <validation-provider
                v-slot="{ errors }"
                rules="required"
                >
                <v-row>
                  <v-col>
                    <v-autocomplete
                      v-model="form.visitWindowUnitUid"
                      :label="$t('StudyVisitForm.visit_win_unit')"
                      data-cy="visit-win-unit"
                      :items="timeUnits"
                      item-text="name"
                      item-value="uid"
                      :error-messages="errors"
                      clearable
                      @change="getVisitPreview"
                      />
                  </v-col>
                </v-row>
              </validation-provider>
            </div>
          </div>
        </template>
        <div class="sub-title mt-8">{{ $t('StudyVisitForm.visit_details') }}</div>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.description"
              :label="$t('StudyVisitForm.visit_description')"
              data-cy="visit-description"
              clearable
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-autocomplete
              v-model="form.epochAllocationUid"
              :label="$t('StudyVisitForm.epoch_allocation')"
              data-cy="epoch-allocation-rule"
              :items="epochAllocations"
              item-text="sponsorPreferredName"
              item-value="termUid"
              clearable
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <validation-provider
              v-slot="{ errors }"
              rules=""
              >
              <v-textarea
                v-model="form.startRule"
                :label="$t('StudyVisitForm.visit_start_rule')"
                data-cy="visit-start-rule"
                clearable
                rows="1"
                :error-messages="errors"
                auto-grow
                />
            </validation-provider>
          </v-col>
          <v-col cols="6">
            <v-textarea
              v-model="form.endRule"
              :label="$t('StudyVisitForm.visit_stop_rule')"
              data-cy="visit-end-rule"
              clearable
              rows="1"
              auto-grow
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.note"
              :label="$t('StudyVisitForm.visit_notes')"
              data-cy="visit-notes"
              clearable
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6" class="d-flex align-center">
            <div class="mr-2">
              <v-combobox
                v-model="form.consecutiveVisitGroup"
                :label="$t('StudyVisitForm.consecutive_visit')"
                :items="visitGroups"
                item-text="name"
                ref="consecutiveGroupCombobox"
                clearable
                />
            </div>
            <v-checkbox
              v-model="form.showVisit"
              default="true"
              :label="$t('StudyVisitForm.show_visit')"
              />
          </v-col>
        </v-row>
      </validation-observer>
    </template>
  </stepper-form>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</div>
</template>

<script>
import StepperForm from '@/components/tools/StepperForm'
import epochs from '@/api/studyEpochs'
import units from '@/api/units'
import codelists from '@/api/controlledTerminology/terms'
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import visitConstants from '@/constants/visits'

export default {
  components: {
    ConfirmDialog,
    StepperForm
  },
  props: {
    studyVisit: Object,
    firstVisit: Boolean,
    opened: Boolean
  },
  computed: {
    displayAnchorVisitFlag () {
      return this.globalAnchorVisit === null || (this.studyVisit && this.studyVisit.uid === this.globalAnchorVisit.uid)
    },
    title () {
      return (this.studyVisit) ? this.$t('StudyVisitForm.edit_title') : this.$t('StudyVisitForm.add_title')
    },
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      groups: 'studyEpochs/allowedConfigs'
    }),
    filteredPeriods () {
      if (this.form.visitClass === visitConstants.CLASS_SINGLE_VISIT) {
        return this.periods
      }
      if (this.periods) {
        return this.periods.filter(item => item.epochName === visitConstants.EPOCH_BASIC)
      }
      return []
    }
  },
  data () {
    return {
      anchorVisitsInSubgroup: [],
      batchCreateVisits: false,
      currentAnchorVisit: null,
      disableTimeValue: false,
      form: this.getInitialFormContent(this.studyVisit),
      helpItems: [
        'StudyVisitForm.vtype_step_label',
        'StudyVisitForm.period',
        'StudyVisitForm.batch_create_visits',
        'StudyVisitForm.single_visit',
        'StudyVisitForm.anchor_visit_in_group',
        'StudyVisitForm.visit_type',
        'StudyVisitForm.contact_mode',
        'StudyVisitForm.anchor_visit',
        'StudyVisitForm.current_anchor_visit',
        'StudyVisitForm.time_reference',
        'StudyVisitForm.time_value',
        'StudyVisitForm.time_unit',
        'StudyVisitForm.visit_name',
        'StudyVisitForm.visit_short_name',
        'StudyVisitForm.study_day_label',
        'StudyVisitForm.study_week_label',
        'StudyVisitForm.visit_win_min',
        'StudyVisitForm.visit_win_max',
        'StudyVisitForm.visit_win_unit',
        'StudyVisitForm.visit_description',
        'StudyVisitForm.epoch_allocation',
        'StudyVisitForm.visit_start_rule',
        'StudyVisitForm.visit_stop_rule',
        'StudyVisitForm.visit_notes',
        'StudyVisitForm.consecutive_visit',
        'StudyVisitForm.duplicate_visit'
      ],
      globalAnchorVisit: null,
      periods: [],
      steps: [
        { name: 'visitType', title: this.$t('StudyVisitForm.vtype_step_label') },
        { name: 'epoch', title: this.$t('StudyVisitForm.epoch_step_label') },
        { name: 'details', title: this.$t('StudyVisitForm.details_step_label') }
      ],
      timeReferences: [],
      timeUnits: [],
      visitGroups: [],
      visitTypes: [],
      loading: false,
      previewLoading: false,
      contactModes: [],
      epochAllocations: [],
      studyEpoch: '',
      visitCount: 1,
      visitClasses: [
        { label: this.$t('StudyVisitForm.scheduled_visit'), value: visitConstants.CLASS_SINGLE_VISIT },
        { label: this.$t('StudyVisitForm.unscheduled_visit'), value: visitConstants.CLASS_UNSCHEDULED_VISIT },
        { label: this.$t('StudyVisitForm.non_visit'), value: visitConstants.CLASS_NON_VISIT }
      ],
      visitSubClasses: [
        { label: this.$t('StudyVisitForm.single_visit'), value: visitConstants.SUBCLASS_SINGLE_VISIT },
        { label: this.$t('StudyVisitForm.anchor_visit_in_group'), value: visitConstants.SUBCLASS_ANCHOR_VISIT_IN_GROUP_OF_SUBV },
        {
          label: this.$t('StudyVisitForm.additional_sub_visit'),
          value: visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV
        }
      ]
    }
  },
  methods: {
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    close () {
      this.$emit('close')
      this.form = this.getInitialFormContent()
      this.$refs.stepper.reset()
    },
    getInitialFormContent (item) {
      if (item) {
        return item
      }
      this.studyEpoch = ''
      return {
        isGlobalAnchorVisit: false,
        visitClass: visitConstants.CLASS_SINGLE_VISIT,
        showVisit: true,
        minVisitWindowValue: 0,
        maxVisitWindowValue: 0,
        visitSubclass: visitConstants.CLASS_SINGLE_VISIT
      }
    },
    async submit () {
      this.$refs.consecutiveGroupCombobox.blur()
      const valid1 = await this.$refs.observer_1.validate()
      if (!valid1) {
        return
      }
      const valid2 = await this.$refs.observer_2.validate()
      if (!valid2) {
        return
      }
      try {
        if (!this.studyVisit) {
          await this.addObject()
        } else {
          await this.updateObject()
        }
        this.close()
      } finally {
        this.$refs.stepper.reset()
        this.$refs.stepper.loading = false
      }
    },
    async addObject () {
      const data = JSON.parse(JSON.stringify(this.form))
      if (data.visitSubclass === visitConstants.SUBCLASS_ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV) {
        data.timeReferenceUid = this.timeReferences.find(item => item.sponsorPreferredName === visitConstants.TIMEREF_GLOBAL_ANCHOR_VISIT).termUid
      } else if (data.visitClass !== visitConstants.CLASS_SINGLE_VISIT) {
        delete data.timeValue
        delete data.timeReferenceUid
        delete data.minVisitWindowValue
        delete data.maxVisitWindowValue
        delete data.timeUnitUid
      }
      await this.$store.dispatch('studyEpochs/addStudyVisit', { studyUid: this.selectedStudy.uid, input: data })
      this.$store.dispatch('studyEpochs/fetchStudyVisits', this.selectedStudy.uid)
      bus.$emit('notification', { msg: this.$t('StudyVisitForm.add_success') })
    },
    updateObject () {
      const data = JSON.parse(JSON.stringify(this.form))
      return this.$store.dispatch('studyEpochs/updateStudyVisit', { studyUid: this.selectedStudy.uid, studyVisitUid: this.studyVisit.uid, input: data }).then(resp => {
        this.$store.dispatch('studyEpochs/fetchStudyVisits', this.selectedStudy.uid)
        bus.$emit('notification', { msg: this.$t('StudyVisitForm.update_success') })
      })
    },
    getVisitPreview () {
      if (this.studyVisit) {
        return
      }
      const mandatoryFields = ['visitTypeUid', 'visitContactModeUid']
      if (this.form.visitClass === visitConstants.CLASS_SINGLE_VISIT) {
        mandatoryFields.push('timeReferenceUid', 'timeValue')
      }
      for (const field of mandatoryFields) {
        if (this.form[field] === undefined || this.form[field] === null) {
          return
        }
      }
      const payload = { ...this.form }
      if (payload.visitClass !== visitConstants.CLASS_SINGLE_VISIT) {
        payload.timeReferenceUid = this.timeReferences.find(item => item.sponsorPreferredName === visitConstants.TIMEREF_GLOBAL_ANCHOR_VISIT).termUid
        payload.timeValue = 0
      }
      payload.isGlobalAnchorVisit = false
      this.previewLoading = true
      epochs.getStudyVisitPreview(this.selectedStudy.uid, payload).then(resp => {
        for (const field of ['visitName', 'visitShortName', 'studyDayLabel', 'studyWeekLabel']) {
          this.$set(this.form, field, resp.data[field])
        }
      }).finally(() => {
        this.previewLoading = false
      })
    },
    callbacks () {
      this.$store.dispatch('studyEpochs/fetchAllowedConfigs')
      epochs.getGlobalAnchorVisit(this.selectedStudy.uid).then(resp => {
        this.globalAnchorVisit = resp.data
        if (this.globalAnchorVisit) {
          this.currentAnchorVisit = this.globalAnchorVisit.visitTypeName
        }
      })
      epochs.getAnchorVisitsInGroupOfSubvisits(this.selectedStudy.uid).then(resp => {
        this.anchorVisitsInSubgroup = resp.data
      })
      codelists.getByCodelist('epochs').then(resp => {
        this.loading = true
        this.epochsData = resp.data.items
        epochs.getStudyEpochs(this.selectedStudy.uid).then(resp => {
          this.periods = resp.data.items
          this.periods.forEach(item => {
            this.epochsData.forEach(epochDef => {
              if (epochDef.termUid === item.epoch) {
                item.epochName = epochDef.sponsorPreferredName
              }
            })
          })
          if (this.studyVisit) {
            this.studyEpoch = this.studyVisit.studyEpochUid
          }
          this.loading = false
        })
      })
      codelists.getByCodelist('contactModes').then(resp => {
        this.contactModes = resp.data.items
      })
      units.getBySubset('Study Time').then(resp => {
        this.timeUnits = resp.data.items
        if (!this.studyVisit) {
          const defaultUnit = this.timeUnits.find(unit => unit.name === 'days')
          this.form.timeUnitUid = defaultUnit.uid
          this.form.visitWindowUnitUid = defaultUnit.uid
        }
      })
      epochs.getGroups(this.selectedStudy.uid).then(resp => {
        this.visitGroups = resp.data
      })
      codelists.getByCodelist('epochAllocations').then(resp => {
        this.epochAllocations = resp.data.items
      })
    },
    onTabChange (number) {
      if (number === 3 && this.globalAnchorVisit === null) {
        bus.$emit('notification', { msg: this.$t('StudyVisitForm.no_anchor_visit'), type: 'warning' })
      }
    },
    setVisitType (value) {
      if (this.visitTypes.length) {
        this.$set(this.form, 'visitTypeUid', this.visitTypes.find(item => item.visit_type_name === value).visit_type_uid)
        this.getVisitPreview()
      }
    },
    setEpochAllocationRule (value) {
      if (this.epochAllocations.length) {
        this.$set(this.form, 'epochAllocationUid', this.epochAllocations.find(item => item.sponsorPreferredName === value).termUid)
      }
    },
    setStudyEpochToBasic () {
      if (this.loading) {
        return
      }
      if (this.periods.length) {
        this.studyEpoch = this.periods.find(item => item.epochName === visitConstants.EPOCH_BASIC)
        if (this.studyEpoch) {
          this.studyEpoch = this.studyEpoch.uid
        }
      }
      if (!this.studyEpoch) {
        const subType = this.groups.find(item => item.subtype_name === visitConstants.EPOCH_BASIC)
        const payload = { epochSubType: subType.subtype, studyUid: this.selectedStudy.uid }
        epochs.getPreviewEpoch(this.selectedStudy.uid, payload).then(resp => {
          const data = {
            studyUid: this.selectedStudy.uid,
            epoch: resp.epoch,
            epochType: subType.type,
            epochSubType: subType.subtype,
            colorHash: '#FFFFFF'
          }
          epochs.addStudyEpoch(this.selectedStudy.uid, data).then(resp => {
            epochs.getStudyEpochs(this.selectedStudy.uid).then(resp => {
              this.periods = resp.data.items
              this.studyEpoch = this.periods.find(item => item.epochName === visitConstants.EPOCH_BASIC).uid
            })
          })
        })
      }
    }
  },
  created () {
    this.visitConstants = visitConstants
  },
  mounted () {
    this.callbacks()
  },
  watch: {
    studyVisit (value) {
      if (value) {
        this.form = value
      }
    },
    opened () {
      this.callbacks()
    },
    studyEpoch (value) {
      if (!value) {
        return
      }
      this.$set(this.form, 'studyEpochUid', value)
      const data = {
        study_uid: this.selectedStudy.uid,
        epoch_type_uid: this.periods.find(el => el.uid === value).epochType
      }
      epochs.getAllowedVisitTypes(data).then(resp => {
        this.visitTypes = resp.data
        codelists.getByCodelist('timepointReferences').then(resp => {
          this.timeReferences = resp.data.items
          if (this.form.visitClass === visitConstants.CLASS_UNSCHEDULED_VISIT && this.visitTypes.length) {
            this.setVisitType(visitConstants.VISIT_TYPE_UNSCHEDULED)
          }
          if (this.form.visitClass === visitConstants.CLASS_NON_VISIT && this.visitTypes.length) {
            this.setVisitType(visitConstants.VISIT_TYPE_NON_VISIT)
          }
        })
      })
      if (this.form.visitClass === visitConstants.CLASS_NON_VISIT || this.form.visitClass === visitConstants.CLASS_UNSCHEDULED_VISIT) {
        this.setEpochAllocationRule(visitConstants.DATE_CURRENT_VISIT)
      } else {
        const studyEpoch = this.periods.find(item => item.uid === value)
        if (studyEpoch.epochName === visitConstants.EPOCH_TREATMENT || studyEpoch.epochName === visitConstants.EPOCH_TREATMENT_1) {
          epochs.getAmountOfVisitsInStudyEpoch(this.selectedStudy.uid, studyEpoch.uid).then(resp => {
            const amountOfVisitsInTreatment = resp.data
            if (amountOfVisitsInTreatment === 0) {
              this.setEpochAllocationRule(visitConstants.PREVIOUS_VISIT)
            } else {
              this.setEpochAllocationRule(visitConstants.CURRENT_VISIT)
            }
          })
        } else {
          this.setEpochAllocationRule(visitConstants.CURRENT_VISIT)
        }
      }
    },
    batchCreateVisits (value) {
      if (value) {
        const timeRef = this.timeReferences.find(timeRef => timeRef.sponsorPreferredName === visitConstants.TIMEREF_PREVIOUS_VISIT)
        if (timeRef) {
          this.$set(this.form, 'timeReferenceUid', timeRef.termUid)
        }
      }
    },
    'form.isGlobalAnchorVisit' (value) {
      if (value) {
        this.$set(this.form, 'timeValue', 0)
        this.disableTimeValue = true
      } else {
        this.$set(this.form, 'timeValue', null)
        this.disableTimeValue = false
      }
    },
    'form.visitClass' (value) {
      if (value !== visitConstants.CLASS_SINGLE_VISIT) {
        this.setStudyEpochToBasic()
        const contactMode = this.contactModes.find(item => item.sponsorPreferredName === visitConstants.CONTACT_MODE_VIRTUAL_VISIT)
        if (contactMode) {
          this.$set(this.form, 'visitContactModeUid', contactMode.termUid)
        }
      }
      if (value === visitConstants.CLASS_UNSCHEDULED_VISIT && this.visitTypes.length) {
        this.setVisitType(visitConstants.VISIT_TYPE_UNSCHEDULED)
      }
      if (value === visitConstants.CLASS_NON_VISIT && this.visitTypes.length) {
        this.setVisitType(visitConstants.VISIT_TYPE_NON_VISIT)
      }
    },
    periods (value) {
      if (value && value.length && this.form.visitClass !== visitConstants.CLASS_SINGLE_VISIT) {
        this.setStudyEpochToBasic()
      }
    }
  }
}
</script>

<style scoped lang="scss">
.sub-title {
  color: var(--v-secondary-base);
  font-weight: 600;
  margin: 10px 0;
  font-size: 1.1em;
}
</style>
