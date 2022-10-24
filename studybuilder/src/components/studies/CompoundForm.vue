<template>
<horizontal-stepper-form
  ref="stepper"
  :title="title"
  :steps="steps"
  @close="close"
  @save="submit"
  :form-observer-getter="getObserver"
  :editable="studyCompound !== undefined && studyCompound !== null"
  :helpItems="helpItems"
  :edit-data="form"
  >
  <template v-slot:step.type_of_treatment="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <not-applicable-field
        ref="naField"
        :clean-function="cleanTypeOfTreatment"
        :disabled="typeOfTreatmentUidNADisabled"
        :checked="studyCompound && !studyCompound.compound"
        >
        <template v-slot:mainField="{ notApplicable }">
          <validation-provider
            v-slot="{ errors }"
            name="activity"
            :rules="`requiredIfNotNA:${notApplicable}`"
            >
            <v-autocomplete
              v-model="form.typeOfTreatment"
              :data-cy="$t('StudyCompoundForm.type_of_treatment')"
              :label="$t('StudyCompoundForm.type_of_treatment')"
              :items="typeOfTreatments"
              item-text="sponsorPreferredName"
              item-value="termUid"
              return-object
              :error-messages="errors"
              dense
              clearable
              />
          </validation-provider>
        </template>
      </not-applicable-field>
    </validation-observer>
  </template>
  <template v-slot:step.compoundAlias="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-row>
        <v-col cols="6">
          <validation-provider
            rules="required"
            v-slot="{ errors }"
            >
            <v-autocomplete
              v-model.lazy="form.compoundSimple"
              :label="$t('StudyCompoundForm.compound')"
              :items="compounds"
              item-text="name"
              item-value="uid"
              return-object
              :error-messages="errors"
              dense
              clearable
              />
          </validation-provider>
        </v-col>
        <v-col cols="6">
          <validation-provider
            rules="required"
            v-slot="{ errors }"
            >
            <v-autocomplete
              v-model="form.compoundAlias"
              :label="$t('StudyCompoundForm.compound_alias')"
              :items="compoundAliases"
              item-text="name"
              item-value="uid"
              return-object
              :error-messages="errors"
              dense
              clearable
              />
          </validation-provider>
        </v-col>
      </v-row>
      <template v-if="form.compound">
        <v-row>
          <v-col cols="6">
            <yes-no-field
              v-model="form.compound.isSponsorCompound"
              :label="$t('StudyCompoundForm.sponsor_compound')"
              row
              disabled
              hide-details
              />
          </v-col>
          <v-col cols="6" v-if="form.compoundAlias">
            <yes-no-field
              v-model="form.compoundAlias.isPreferredSynonym"
              :label="$t('StudyCompoundForm.is_preferred_synonym')"
              row
              disabled
              hide-details
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-text-field
              v-model="form.compound.nncLongNumber"
              :label="$t('CompoundForm.long_number')"
              dense
              disabled
              filled
              hide-details
              />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="form.compound.nncShortNumber"
              :label="$t('CompoundForm.short_number')"
              dense
              disabled
              filled
              hide-details
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-textarea
              :label="$t('StudyCompoundForm.compound_definition')"
              v-model="form.compound.definition"
              dense
              auto-grow
              rows="1"
              disabled
              filled
              hide-details
              />
          </v-col>
          <v-col cols="6" v-if="form.compoundAlias">
            <v-textarea
              :label="$t('StudyCompoundForm.alias_definition')"
              v-model="form.compoundAlias.definition"
              dense
              auto-grow
              rows="1"
              disabled
              filled
              hide-details
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              :value="substances"
              :label="$t('CompoundAliasForm.substance')"
              dense
              disabled
              filled
              hide-details
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              :value="pharmacologicalClass"
              :label="$t('CompoundAliasForm.pharmacological_class')"
              dense
              disabled
              filled
              hide-details
              />
          </v-col>
        </v-row>
      </template>
    </validation-observer>
  </template>
  <template v-slot:step.compound="{ step }">
    <validation-observer v-if="form.compound" :ref="`observer_${step}`">
      <v-row>
        <v-col>
          <v-autocomplete
            v-model="form.dosageFormUid"
            :label="$t('StudyCompoundForm.dosage_form')"
            :items="form.compound.dosageForms"
            item-text="name"
            item-value="termUid"
            dense
            clearable
            />
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <v-autocomplete
            v-model="form.strengthValueUid"
            :label="$t('StudyCompoundForm.compound_strength_value')"
            :items="form.compound.strengthValues"
            :item-text="(item) => `${item.value} ${item.unitLabel}`"
            item-value="uid"
            dense
            clearable
            />
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <v-autocomplete
            :data-cy="$t('StudyCompoundForm.route_of_admin')"
            v-model="form.routeOfAdministrationUid"
            :label="$t('StudyCompoundForm.route_of_admin')"
            :items="form.compound.routesOfAdministration"
            item-text="name"
            item-value="termUid"
            dense
            clearable
            />
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <v-autocomplete
            :data-cy="$t('StudyCompoundForm.dispensed_in')"
            v-model="form.dispensedInUid"
            :label="$t('StudyCompoundForm.dispensed_in')"
            :items="form.compound.dispensers"
            item-text="name"
            item-value="termUid"
            dense
            clearable
            />
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <v-autocomplete
            :data-cy="$t('StudyCompoundForm.device')"
            v-model="form.deviceUid"
            :label="$t('StudyCompoundForm.device')"
            :items="form.compound.deliveryDevices"
            item-text="name"
            item-value="termUid"
            dense
            clearable
            />
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <v-textarea
            :data-cy="$t('StudyCompoundForm.other')"
            v-model="form.otherInfo"
            :label="$t('StudyCompoundForm.other')"
            auto-grow
            rows="1"
            dense
            clearable
            />
        </v-col>
      </v-row>
    </validation-observer>
  </template>
</horizontal-stepper-form>
</template>

<script>
import { bus } from '@/main'
import compoundAliases from '@/api/concepts/compoundAliases'
import compounds from '@/api/concepts/compounds'
import compoundsSimple from '@/api/concepts/compoundsSimple'
import constants from '@/constants/studyCompounds'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import { mapGetters } from 'vuex'
import NotApplicableField from '@/components/tools/NotApplicableField'
import statuses from '@/constants/statuses'
import studyConstants from '@/constants/study'
import terms from '@/api/controlledTerminology/terms'
import YesNoField from '@/components/tools/YesNoField'

export default {
  components: {
    HorizontalStepperForm,
    NotApplicableField,
    YesNoField
  },
  props: ['studyCompound'],
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyCompounds: 'studyCompounds/studyCompounds',
      getStudyCompoundsByTypeOfTreatment: 'studyCompounds/getStudyCompoundsByTypeOfTreatment',
      getNAStudyCompoundsByTypeOfTreatment: 'studyCompounds/getNAStudyCompoundsByTypeOfTreatment'
    }),
    substances () {
      if (this.form.compound && this.form.compound.substances && this.form.compound.substances.length) {
        return this.form.compound.substances.map(item => `${item.substanceName} (${item.substanceUnii})`).join(', ')
      }
      return ''
    },
    pharmacologicalClass () {
      if (this.form.compound && this.form.compound.substances && this.form.compound.substances.length) {
        return this.form.compound.substances.map(item => item.pclassName).filter(pclass => pclass !== undefined && pclass !== null).join(', ')
      }
      return ''
    },
    title () {
      if (this.studyCompound !== undefined) {
        return this.$t('StudyCompoundForm.edit_title')
      }
      return this.$t('StudyCompoundForm.add_title')
    },
    typeOfTreatmentUidNADisabled () {
      if ((this.$refs.naField && this.$refs.naField.notApplicable) || (this.studyCompound && !this.studyCompound.compound)) {
        return false
      }
      if (!this.form.typeOfTreatment) {
        return true
      }
      const types = [
        constants.TYPE_OF_TREATMENT_INVESTIGATIONAL_PRODUCT,
        constants.TYPE_OF_TREATMENT_CURRENT_TREATMENT,
        constants.TYPE_OF_TREATMENT_COMPARATIVE_TREATMENT
      ]
      if (!types.find(item => item === this.form.typeOfTreatment.sponsorPreferredName)) {
        return true
      }
      const studyCompounds = this.getStudyCompoundsByTypeOfTreatment(this.form.typeOfTreatment.termUid)
      if (studyCompounds.length) {
        return true
      }
      const NAstudyCompounds = this.getNAStudyCompoundsByTypeOfTreatment(this.form.typeOfTreatment.termUid)
      if (NAstudyCompounds.length) {
        return true
      }
      return false
    }
  },
  data () {
    return {
      compoundAliases: [],
      compounds: [],
      helpItems: [
        'StudyCompoundForm.type_of_treatment',
        'StudyCompoundForm.compound',
        'StudyCompoundForm.compound_alias',
        'StudyCompoundForm.pharma_class',
        'StudyCompoundForm.substance',
        'StudyCompoundForm.unii',
        'StudyCompoundForm.route_of_admin',
        'StudyCompoundForm.dosage_form',
        'StudyCompoundForm.dispensed_in',
        'StudyCompoundForm.device',
        'StudyCompoundForm.formulation',
        'StudyCompoundForm.other'
      ],
      form: this.getInitialForm(),
      typeOfTreatments: [],
      steps: this.getInitialSteps()
    }
  },
  methods: {
    close () {
      this.$emit('close')
      this.form = this.getInitialForm()
      this.$refs.stepper.reset()
      this.$refs.naField.reset()
    },
    getInitialForm () {
      return {
        compound: {},
        compoundSimple: {},
        compoundAlias: {},
        typeOfTreatment: {},
        dosageFormUid: null,
        strengthValueUid: null,
        routeOfAdministrationUid: null,
        dispensedInUid: null,
        deviceUid: null,
        otherInfo: null
      }
    },
    getInitialSteps () {
      return [
        { name: 'type_of_treatment', title: this.$t('StudyCompoundForm.step1_title') },
        { name: 'compoundAlias', title: this.$t('StudyCompoundForm.step2_title') },
        { name: 'compound', title: this.$t('StudyCompoundForm.step3_title') }
      ]
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    cleanTypeOfTreatment (value) {
      if (value) {
        this.steps = [
          { name: 'type_of_treatment', title: this.$t('StudyCompoundForm.step1_title') }
        ]
      } else {
        this.steps = this.getInitialSteps()
      }
    },
    async submit () {
      const data = JSON.parse(JSON.stringify(this.form))
      data.typeOfTreatmentUid = data.typeOfTreatment.termUid
      delete data.typeOfTreatment
      delete data.compound
      if (data.compoundAlias) {
        data.compoundAliasUid = data.compoundAlias.uid || null
      } else {
        data.reasonForMissingNullValueUid = studyConstants.TERM_NOT_APPLICABLE
      }

      let action = null
      let notification = null
      let args = null
      if (!this.studyCompound) {
        action = 'addStudyCompound'
        notification = 'add_success'
        args = { studyUid: this.selectedStudy.uid, data }
      } else {
        action = 'updateStudyCompound'
        notification = 'update_success'
        args = {
          studyUid: this.selectedStudy.uid,
          studyCompoundUid: this.studyCompound.studyCompoundUid,
          data
        }
      }
      try {
        await this.$store.dispatch(`studyCompounds/${action}`, args)
        bus.$emit('notification', { msg: this.$t(`StudyCompoundForm.${notification}`) })
        this.close()
      } finally {
        this.$refs.stepper.loading = false
      }
    }
  },
  mounted () {
    const filters = {
      status: { v: [statuses.FINAL] }
    }
    compoundsSimple.getFiltered({ filters }).then(resp => {
      this.compounds = resp.data.items
    })
    terms.getByCodelist('typeOfTreatment').then(resp => {
      this.typeOfTreatments = resp.data.items
    })
  },
  watch: {
    studyCompound: {
      handler: function (val) {
        if (val) {
          this.form.typeOfTreatment = val.typeOfTreatment
          this.form.otherInfo = val.otherInfo
          if (val.compound) {
            this.form.compound = val.compound
            this.form.compoundSimple = {
              uid: val.compound.uid,
              name: val.compound.name
            }
            const filters = {
              compoundUid: { v: [val.compound.uid] },
              status: { v: [statuses.FINAL] }
            }
            compoundAliases.getFiltered({ filters }).then(resp => {
              this.compoundAliases = resp.data.items
            })
          } else {
            this.steps = [
              { name: 'type_of_treatment', title: this.$t('StudyCompoundForm.step1_title') }
            ]
          }
          if (val.compoundAlias) {
            this.form.compoundAlias = val.compoundAlias
          }
          if (val.dosageForm) {
            this.form.dosageFormUid = val.dosageForm.termUid
          }
          if (val.routeOfAdministration) {
            this.form.routeOfAdministrationUid = val.routeOfAdministration.termUid
          }
          if (val.dispensedIn) {
            this.form.dispensedInUid = val.dispensedIn.termUid
          }
          if (val.device) {
            this.form.deviceUid = val.device.termUid
          }
          if (val.strengthValue) {
            this.form.strengthValueUid = val.strengthValue.uid
          }
        }
      },
      immediate: true
    },
    'form.compoundSimple' (newValue, oldValue) {
      if (newValue) {
        if (!this.studyCompound || this.studyCompound.compound.uid !== newValue.uid) {
          this.$set(this.form, 'compoundAlias', null)
        }
        const filters = {
          compoundUid: { v: [newValue.uid] },
          status: { v: [statuses.FINAL] }
        }
        compoundAliases.getFiltered({ filters }).then(resp => {
          this.compoundAliases = resp.data.items
        })
        if (newValue.uid) {
          compounds.getObject(newValue.uid).then(resp => {
            this.$set(this.form, 'compound', resp.data)
          })
        }
      }
    }
  }
}
</script>
