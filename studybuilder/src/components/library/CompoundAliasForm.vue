<template>
<horizontal-stepper-form
  ref="stepper"
  :title="title"
  :steps="steps"
  @close="close"
  @save="submit"
  :form-observer-getter="getObserver"
  :editable="compoundAlias !== undefined && compoundAlias !== null"
  :helpItems="helpItems"
  :edit-data="form"
  >
  <template v-slot:step.compound="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-row>
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-autocomplete
              v-model="form.compoundSimple"
              :label="$t('CompoundAliasTable.compound_name')"
              :items="compounds"
              :search-input.sync="compoundSearch"
              item-text="name"
              return-object
              dense
              clearable
              hide-no-data
              cache-items
              :loading="loadingCompounds"
              :error-messages="errors"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <template v-if="form.compound">
        <v-row>
          <v-col cols="12">
            <yes-no-field
              v-model="form.compound.isSponsorCompound"
              :label="$t('CompoundForm.sponsor_compound')"
              row
              disabled
              hide-details
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="4">
            <v-text-field
              v-model="form.compound.analyteNumber"
              :label="$t('CompoundForm.analyte_number')"
              dense
              disabled
              filled
              hide-details
              />
          </v-col>
          <v-col cols="4">
            <v-text-field
              v-model="form.compound.nncLongNumber"
              :label="$t('CompoundForm.long_number')"
              dense
              disabled
              filled
              hide-details
              />
          </v-col>
          <v-col cols="4">
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
          <v-col cols="12">
            <v-text-field
              v-model="form.compound.name"
              :label="$t('CompoundForm.name')"
              dense
              disabled
              filled
              hide-details
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-textarea
              :label="$t('_global.definition')"
              v-model="form.compound.definition"
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
              :value="brandNames"
              :label="$t('CompoundForm.brand_name')"
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
  <template v-slot:step.alias="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-row>
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-text-field
              v-model="form.name"
              :label="$t('CompoundAliasForm.name')"
              dense
              clearable
              :error-messages="errors"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-text-field
              v-model="form.nameSentenceCase"
              :label="$t('CompoundAliasForm.sentence_case_name')"
              dense
              clearable
              :error-messages="errors"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <yes-no-field
              v-model="form.isPreferredSynonym"
              :label="$t('CompoundAliasForm.is_preferred_synonym')"
              :error-messages="errors"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <v-textarea
            :label="$t('_global.definition')"
            v-model="form.definition"
            dense
            clearable
            auto-grow
            rows="1"
            />
        </v-col>
      </v-row>
    </validation-observer>
  </template>
</horizontal-stepper-form>
</template>

<script>
import _isEqual from 'lodash/isEqual'
import { bus } from '@/main'
import compoundAliases from '@/api/concepts/compoundAliases'
import compounds from '@/api/concepts/compounds'
import compoundsSimple from '@/api/concepts/compoundsSimple'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import libConstants from '@/constants/libraries'
import YesNoField from '@/components/tools/YesNoField'

export default {
  components: {
    HorizontalStepperForm,
    YesNoField
  },
  props: {
    compoundAliasUid: String,
    formShown: Boolean
  },
  data () {
    return {
      compounds: [],
      compoundAlias: null,
      compoundSearch: null,
      form: this.getInitialForm(),
      helpItems: [
        'CompoundAliasForm.step1_title',
        'CompoundAliasForm.name',
        'CompoundAliasForm.sentence_case_name',
        'CompoundAliasForm.is_preferred_synonym'
      ],
      loadingCompounds: false,
      steps: [
        { name: 'compound', title: this.$t('CompoundAliasForm.step1_title') },
        { name: 'alias', title: this.$t('CompoundAliasForm.step2_title') }

      ]
    }
  },
  computed: {
    title () {
      return (this.compoundAlias) ? this.$t('CompoundAliasForm.edit_title') : this.$t('CompoundAliasForm.add_title')
    },
    brandNames () {
      if (this.form.compound && this.form.compound.brands && this.form.compound.brands.length) {
        return this.form.compound.brands.map(item => item.name).join(', ')
      }
      return ''
    },
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
    }
  },
  methods: {
    close () {
      this.$emit('close')
      this.compounds = []
      this.form = this.getInitialForm()
      this.$refs.stepper.reset()
    },
    getInitialForm () {
      return {
        compoundSimple: {},
        compound: {},
        isPreferredSynonym: false
      }
    },
    loadFormData () {
      this.fetchCompounds('')
      if (this.compoundAliasUid !== null) {
        compoundAliases.getObject(this.compoundAliasUid).then(resp => {
          this.compoundAlias = resp.data
          compounds.getObject(this.compoundAlias.compound.uid).then(resp => {
            this.$set(this.form, 'compoundSimple', resp.data)
          })
        })
      }
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    async add (data) {
      data.libraryName = libConstants.LIBRARY_SPONSOR
      await compoundAliases.create(data)
      this.$emit('created')
      bus.$emit('notification', { msg: this.$t('CompoundAliasForm.add_success'), type: 'success' })
    },
    async update (data) {
      data.changeDescription = this.$t('_global.work_in_progress')
      await compoundAliases.update(this.compoundAlias.uid, data)
      this.$emit('updated')
      bus.$emit('notification', { msg: this.$t('CompoundAliasForm.update_success'), type: 'success' })
    },
    async submit () {
      if (this.$store.getters['form/form'] === '' || _isEqual(this.$store.getters['form/form'], JSON.stringify(this.form))) {
        this.close()
        bus.$emit('notification', { type: 'info', msg: this.$t('_global.no_changes') })
        return
      }
      const data = { ...this.form }
      data.compoundUid = data.compound.uid
      delete data.compound
      try {
        if (!this.compoundAliasUid) {
          await this.add(data)
        } else {
          await this.update(data)
        }
        this.close()
      } catch (error) {
        this.$refs.stepper.loading = false
      }
    },
    fetchCompounds (search) {
      const params = {
        filters: {
          name: { v: [search], op: 'co' }
        },
        sortBy: {
          name: true
        }
      }
      this.loadingCompounds = true
      compoundsSimple.getFiltered(params).then(resp => {
        this.compounds = resp.data.items
        this.loadingCompounds = false
      })
    }
  },
  watch: {
    formShown (value) {
      if (value) {
        this.loadFormData()
      } else {
        this.compoundAlias = null
        this.compound = null
      }
    },
    compoundAlias: {
      handler: function (value) {
        if (value) {
          this.form = { ...value }
        }
      },
      immediate: true
    },
    'form.compoundSimple' (value) {
      if (value && value.uid) {
        compounds.getObject(value.uid).then(resp => {
          this.$set(this.form, 'compound', resp.data)
        })
      }
    },
    'form.name' (value) {
      if (value) {
        this.$set(this.form, 'nameSentenceCase', value.toLowerCase())
      }
    },
    compoundSearch (value) {
      value && value !== this.form.compoundSimple && this.fetchCompounds(value)
    }
  },
  mounted () {
    this.loadFormData()
  }
}
</script>
