<template>
<horizontal-stepper-form
  ref="stepper"
  :title="title"
  :steps="steps"
  @close="close"
  @save="submit"
  :form-observer-getter="getObserver"
  :editable="studyCompoundDosing !== undefined && studyCompoundDosing !== null"
  :helpItems="helpItems"
  :edit-data="form"
  >
  <template v-slot:step.element="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-row>
        <v-col cols="12">
          <validation-provider
            rules="required"
            v-slot="{ errors }"
            >
            <v-autocomplete
              v-model="form.studyElement"
              :label="$t('StudyCompoundDosingForm.element')"
              :items="studyElements"
              item-text="name"
              return-object
              :error-messages="errors"
              dense
              clearable
              />
          </validation-provider>
        </v-col>
      </v-row>
      <template v-if="form.studyElement">
        <v-row>
          <v-col cols="6">
            <v-text-field
              v-model="form.studyElement.order"
              :label="$t('StudyCompoundDosingForm.element_order')"
              row
              disabled
              hide-details
              />
          </v-col>
          <v-col cols="6">
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-text-field
              v-model="elementType"
              :label="$t('StudyCompoundDosingForm.element_type')"
              row
              disabled
              hide-details
              />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="form.studyElement.elementSubType.sponsorPreferredName"
              :label="$t('StudyCompoundDosingForm.element_subtype')"
              row
              disabled
              hide-details
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-text-field
              v-model="form.studyElement.name"
              :label="$t('StudyCompoundDosingForm.element_name')"
              row
              disabled
              hide-details
              />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="form.studyElement.shortName"
              :label="$t('StudyCompoundDosingForm.element_short_name')"
              row
              disabled
              hide-details
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.studyElement.description"
              :label="$t('StudyCompoundDosingForm.element_description')"
              row
              disabled
              hide-details
              />
          </v-col>
        </v-row>
      </template>
    </validation-observer>
  </template>
  <template v-slot:step.compound="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-row>
        <v-col cols="12">
          <validation-provider
            rules="required"
            v-slot="{ errors }"
            >
            <v-autocomplete
              v-model="form.studyCompound"
              :label="$t('StudyCompoundDosingForm.compound')"
              :items="studyCompounds"
              item-text="compoundAlias.name"
              return-object
              :error-messages="errors"
              dense
              clearable
              />
          </validation-provider>
        </v-col>
      </v-row>
    </validation-observer>
    <template v-if="form.studyCompound">
      <v-row>
        <v-col cols="6">
          <v-text-field
            v-model="form.studyCompound.order"
            :label="$t('StudyCompoundDosingForm.compound_order')"
            row
            disabled
            hide-details
            />
        </v-col>
        <v-col cols="6">
          <v-text-field
            v-model="form.studyCompound.typeOfTreatment.name"
            :label="$t('StudyCompoundDosingForm.type_of_treatment')"
            row
            disabled
            hide-details
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <v-text-field
              v-model="form.studyCompound.compound.name"
              :label="$t('StudyCompoundDosingForm.compound_name')"
              row
              disabled
              hide-details
              />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="form.studyCompound.compoundAlias.name"
              :label="$t('StudyCompoundDosingForm.compound_alias_name')"
              row
              disabled
              hide-details
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="6">
            <yes-no-field
              v-model="form.studyCompound.compoundAlias.isPreferredSynonym"
              :label="$t('StudyCompoundForm.is_preferred_synonym')"
              row
              disabled
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
  </template>
  <template v-slot:step.compound_dosing="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-row>
        <v-col>
          <v-autocomplete
            v-if="form.studyCompound"
            v-model="form.doseValueUid"
            :label="$t('StudyCompoundDosingForm.dose_value')"
            :items="form.studyCompound.compound.doseValues"
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
            v-if="form.studyCompound"
            :data-cy="$t('StudyCompoundDosingForm.dose_frequency')"
            v-model="form.doseFrequencyUid"
            :label="$t('StudyCompoundDosingForm.dose_frequency')"
            :items="form.studyCompound.compound.doseFrequencies"
            item-text="name"
            item-value="termUid"
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
import arms from '@/api/arms'
import terms from '@/api/controlledTerminology/terms'
import { bus } from '@/main'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import { mapGetters } from 'vuex'
import YesNoField from '@/components/tools/YesNoField'

export default {
  components: {
    HorizontalStepperForm,
    YesNoField
  },
  props: {
    studyCompoundDosing: Object
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy',
      studyCompounds: 'studyCompounds/studyCompounds',
      studyCompoundDosings: 'studyCompounds/studyCompoundDosings'
    }),
    title () {
      if (this.studyCompoundDosing !== undefined && this.studyCompoundDosing !== null) {
        return this.$t('StudyCompoundDosingForm.edit_title')
      }
      return this.$t('StudyCompoundDosingForm.add_title')
    },
    substances () {
      if (!this.form.studyCompound) {
        return ''
      }
      const compound = this.form.studyCompound.compound
      if (compound && compound.substances && compound.substances.length) {
        return compound.substances.map(item => `${item.substanceName} (${item.substanceUnii})`).join(', ')
      }
      return ''
    },
    pharmacologicalClass () {
      if (!this.form.studyCompound) {
        return ''
      }
      const compound = this.form.studyCompound.compound
      if (compound && compound.substances && compound.substances.length) {
        return compound.substances.map(item => item.pclassName).filter(pclass => pclass !== undefined && pclass !== null).join(', ')
      }
      return ''
    },
    elementType () {
      if (!this.form.studyElement) {
        return ''
      }
      return this.getElementType(this.form.studyElement)
    }
  },
  data () {
    return {
      helpItems: [
        'StudyCompoundDosingForm.element',
        'StudyCompoundDosingForm.compound',
        'StudyCompoundDosingForm.dose_value',
        'StudyCompoundDosingForm.dose_frequency'
      ],
      form: {
      },
      steps: this.getInitialSteps(),
      studyElements: [],
      studyElementTypes: []
    }
  },
  methods: {
    close () {
      this.$emit('close')
      this.form = {}
      this.$refs.stepper.reset()
    },
    getInitialSteps () {
      return [
        { name: 'element', title: this.$t('StudyCompoundDosingForm.step1_title') },
        { name: 'compound', title: this.$t('StudyCompoundDosingForm.step2_title') },
        { name: 'compound_dosing', title: this.$t('StudyCompoundDosingForm.step3_title') }
      ]
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    getElementType (item) {
      const type = this.studyElementTypes.filter(el => el.termUid === item.code)[0]
      if (item.code && type) {
        return type.sponsorPreferredName
      }
    },
    async submit () {
      const data = { ...this.form }
      data.studyElementUid = data.studyElement.elementUid
      delete data.studyElement
      data.studyCompoundUid = data.studyCompound.studyCompoundUid

      let action = null
      let notification = null
      let args = null
      if (!this.studyCompoundDosing) {
        action = 'addStudyCompoundDosing'
        notification = 'add_success'
        args = { studyUid: this.selectedStudy.uid, data }
      } else {
        action = 'updateStudyCompoundDosing'
        notification = 'update_success'
        args = {
          studyUid: this.selectedStudy.uid,
          studyCompoundDosingUid: this.studyCompoundDosing.studyCompoundDosingUid,
          data
        }
      }
      try {
        await this.$store.dispatch(`studyCompounds/${action}`, args)
        bus.$emit('notification', { msg: this.$t(`StudyCompoundDosingForm.${notification}`) })
        this.close()
      } finally {
        this.$refs.stepper.loading = false
      }
    }
  },
  mounted () {
    this.$store.dispatch('studyCompounds/fetchStudyCompounds', { studyUid: this.selectedStudy.uid })
    arms.getStudyElements(this.selectedStudy.uid).then(resp => {
      this.studyElements = resp.data.items
    })
    terms.getByCodelist('elementTypes').then(resp => {
      this.studyElementTypes = resp.data.items
    })
  },
  watch: {
    studyCompoundDosing: {
      handler: function (value) {
        if (value) {
          this.form = { ...value }
          if (value.doseValue) {
            this.$set(this.form, 'doseValueUid', value.doseValue.uid)
          }
          if (value.doseFrequency) {
            this.$set(this.form, 'doseFrequencyUid', value.doseFrequency.termUid)
          }
        }
      },
      immediate: true
    }
  }
}
</script>
