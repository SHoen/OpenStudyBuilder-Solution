<template>
<horizontal-stepper-form
  ref="stepper"
  :title="title"
  :steps="steps"
  @close="close"
  @save="submit"
  :form-observer-getter="getObserver"
  :editable="compound !== undefined && compound !== null"
  :helpItems="helpItems"
  :edit-data="form"
  >
  <template v-slot:step.identifiers="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-row>
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <yes-no-field
              v-model="form.isSponsorCompound"
              :label="$t('CompoundForm.sponsor_compound')"
              row
              :error-messages="errors"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="4">
          <validation-provider
            v-slot="{ errors }"
            rules=""
            >
            <v-text-field
              v-model="form.analyteNumber"
              :label="$t('CompoundForm.analyte_number')"
              dense
              :error-messages="errors"
              />
          </validation-provider>
         </v-col>
        <v-col cols="4">
          <validation-provider
            v-slot="{ errors }"
            rules=""
            >
            <v-text-field
              v-model="form.nncLongNumber"
              :label="$t('CompoundForm.long_number')"
              dense
              :error-messages="errors"
              />
          </validation-provider>
        </v-col>
        <v-col cols="4">
          <validation-provider
            v-slot="{ errors }"
            rules=""
            >
            <v-text-field
              v-model="form.nncShortNumber"
              :label="$t('CompoundForm.short_number')"
              dense
              :error-messages="errors"
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="6">
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-text-field
              v-model="form.name"
              :label="$t('CompoundForm.name')"
              dense
              :error-messages="errors"
              />
          </validation-provider>
        </v-col>
        <v-col cols="6">
           <yes-no-field
             v-model="form.isNameInn"
             :label="$t('CompoundForm.is_inn')"
             row
             />
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
      <v-row>
        <v-col cols="12">
          <multiple-select
            v-model="form.brands"
            :label="$t('CompoundForm.brand_name')"
            :items="brands"
            return-object
            item-text="name"
            />
        </v-col>
      </v-row>
      <v-card style="position: relative">
        <v-card-title style="position: relative">
          {{$t('CompoundForm.substances')}}
        </v-card-title>
        <v-btn
            color="primary"
            absolute
            top
            right
            fab
            x-small
            @click="addSubstance"
            >
            <v-icon>mdi-plus</v-icon>
        </v-btn>
        <v-card-text>
          <v-card v-for="(substance, index) in form.substances" :key="index" class="sub-v-card">
            <v-card-text style="position: relative">
              <substance-field v-model="form.substances[index]" />
            </v-card-text>
            <v-btn
              color="error"
              absolute
              top
              right
              fab
              x-small
              @click="removeSubstance(index)"
              >
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </v-card>
        </v-card-text>
      </v-card>
    </validation-observer>
  </template>
  <template v-slot:step.dosingDetails="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-row>
        <v-col cols="6">
          <v-card style="position: relative">
            <v-card-title style="position: relative">
              {{$t('CompoundForm.doses')}}
            </v-card-title>
            <v-btn
                color="primary"
                absolute
                top
                right
                fab
                x-small
                @click="addDoseValue"
                >
                <v-icon>mdi-plus</v-icon>
            </v-btn>
            <v-card-text>
              <v-card v-for="(doseValue, index) in form.doseValues" :key="index" class="sub-v-card">
                <v-card-text style="position: relative">
                  <numeric-value-with-unit-field
                    v-model="form.doseValues[index]"
                    :label="$t('CompoundForm.dose')"
                    subset="Dose Unit"
                    :initial-value="form.doseValues[index]"
                    />
                </v-card-text>
                <v-btn
                  color="error"
                  absolute
                  top
                  right
                  fab
                  x-small
                  @click="removeDoseValue(index)"
                  >
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </v-card>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="6">
          <v-card style="position: relative">
            <v-card-title style="position: relative">
              {{$t('CompoundForm.strengths')}}
            </v-card-title>
            <v-btn
                color="primary"
                absolute
                top
                right
                fab
                x-small
                @click="addStrengthValue"
                >
                <v-icon>mdi-plus</v-icon>
            </v-btn>
            <v-card-text>
              <v-card v-for="(strengthValue, index) in form.strengthValues" :key="index" class="sub-v-card">
                <v-card-text style="position: relative">
                  <numeric-value-with-unit-field
                    v-model="form.strengthValues[index]"
                    :label="$t('CompoundForm.strength')"
                    subset="Strength Unit"
                    :initial-value="form.strengthValues[index]"
                    />
                </v-card-text>
                <v-btn
                  color="error"
                  absolute
                  top
                  right
                  fab
                  x-small
                  @click="removeStrengthValue(index)"
                  >
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </v-card>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <multiple-select
            v-model="form.doseFrequencyUids"
            :label="$t('CompoundForm.dosing_frequency')"
            :items="frequencies"
            item-text="sponsorPreferredName"
            item-value="termUid"
            />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <multiple-select
            v-model="form.routeOfAdministrationUids"
            :label="$t('CompoundForm.route_of_administration')"
            :items="routesOfAdmin"
            item-text="sponsorPreferredName"
            item-value="termUid"
            />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <multiple-select
            v-model="form.dosageFormUids"
            :label="$t('CompoundForm.dosage_form')"
            :items="dosageForms"
            item-text="sponsorPreferredName"
            item-value="termUid"
            />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <multiple-select
            v-model="form.dispensersUids"
            :label="$t('CompoundForm.dispensed_in')"
            :items="dispensers"
            item-text="sponsorPreferredName"
            item-value="termUid"
            />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <multiple-select
            v-model="form.deliveryDevicesUids"
            :label="$t('CompoundForm.device')"
            :items="devices"
            item-text="sponsorPreferredName"
            item-value="termUid"
            />
        </v-col>
      </v-row>
    </validation-observer>
  </template>
  <template v-slot:step.halfLife="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <v-row>
        <v-col cols="12">
          <numeric-value-with-unit-field
            v-model="form.halfLife"
            :label="$t('CompoundForm.half_life')"
            subset="Time Unit"
            :initial-value="form.halfLife"
            />
        </v-col>
      </v-row>
      <v-card style="position: relative">
        <v-card-title style="position: relative">
          {{$t('CompoundForm.lag_times')}}
        </v-card-title>
        <v-btn
          color="primary"
          absolute
          top
          right
          fab
          x-small
          @click="addLagTime"
          >
          <v-icon>mdi-plus</v-icon>
        </v-btn>
        <v-card-text>
          <v-card v-for="(lagTime, index) in form.lagTimes" :key="index" class="sub-v-card">
            <v-card-text style="position: relative;">
              <v-row>
                <v-col cols="6">
                  <v-autocomplete
                    v-model="form.sdtmDomains[index].uid"
                    :label="$t('CompoundForm.sdtm_domain')"
                    :items="adverseEvents"
                    item-text="sponsorPreferredName"
                    item-value="termUid"
                    dense
                    clearable
                    />
                </v-col>
                <v-col cols="6">
                  <numeric-value-with-unit-field
                    v-model="form.lagTimes[index]"
                    :label="$t('CompoundForm.lag_time')"
                    subset="Time Unit"
                    :initial-value="form.lagTimes[index]"
                    />
                </v-col>
              </v-row>
            </v-card-text>
            <v-btn
              color="error"
              absolute
              top
              right
              fab
              x-small
              @click="removeLagTime(index)"
              >
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </v-card>
        </v-card-text>
      </v-card>
    </validation-observer>
  </template>
   <template v-slot:step.alias="{ step }">
    <template v-if="compoundUid == null">
      <validation-observer :ref="`observer_${step}`">
        <v-row>
          <v-col cols="12">
            <validation-provider
              v-slot="{ errors }"
              rules="required"
              >
              <v-text-field
                v-model="form.aliasName"
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
                v-model="form.aliasNameSentenceCase"
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
                v-model="form.aliasIsPreferredSynonym"
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
              v-model="form.aliasDefinition"
              dense
              clearable
              auto-grow
              rows="1"
              />
          </v-col>
        </v-row>
      </validation-observer>
    </template>
    <v-row v-else>
      <v-col cols="12">
        <v-simple-table>
          <template v-slot:default>
            <thead>
              <tr class="text-left">
                <th>{{ $t('CompoundOverview.compound_alias') }}</th>
                <th>{{ $t('_global.definition') }}</th>
                <th>{{ $t('CompoundOverview.preferred_alias') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="alias in compoundAliases" :key="alias.uid">
                <td>{{ alias.name }}</td>
                <td>{{ alias.definition }}</td>
                <td>{{ alias.isPreferredSynonym|yesno }}</td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </v-col>
    </v-row>
  </template>
</horizontal-stepper-form>
</template>

<script>
import _isEqual from 'lodash/isEqual'
import brands from '@/api/brands'
import { bus } from '@/main'
import compounds from '@/api/concepts/compounds'
import compoundAliases from '@/api/concepts/compoundAliases'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import lagTimes from '@/api/concepts/lagTimes'
import libConstants from '@/constants/libraries'
import { mapGetters } from 'vuex'
import MultipleSelect from '@/components/tools/MultipleSelect'
import NumericValueWithUnitField from '@/components/tools/NumericValueWithUnitField'
import numericValuesWithUnit from '@/api/concepts/numericValuesWithUnit'
import SubstanceField from './SubstanceField'
import terms from '@/api/controlledTerminology/terms'
import YesNoField from '@/components/tools/YesNoField'

export default {
  components: {
    HorizontalStepperForm,
    MultipleSelect,
    NumericValueWithUnitField,
    SubstanceField,
    YesNoField
  },
  props: {
    compoundUid: String,
    formShown: Boolean
  },
  data () {
    return {
      compound: null,
      adverseEvents: [],
      brands: [],
      devices: [],
      dispensers: [],
      dosageForms: [],
      form: this.getInitialForm(),
      frequencies: [],
      helpItems: [
        'CompoundForm.sponsor_compound',
        'CompoundForm.analyte_number',
        'CompoundForm.long_number',
        'CompoundForm.short_number',
        'CompoundForm.name',
        'CompoundForm.is_inn',
        'CompoundForm.definition',
        'CompoundForm.brand_name',
        'CompoundForm.substance_name',
        'CompoundForm.pharmacological_class',
        'CompoundForm.medrt',
        'CompoundForm.dose',
        'CompoundForm.strength',
        'CompoundForm.dosing_frequency',
        'CompoundForm.route_of_administration',
        'CompoundForm.dosage_form',
        'CompoundForm.dispensed_in',
        'CompoundForm.device',
        'CompoundForm.formulation',
        'CompoundForm.formulation_details',
        'CompoundForm.manufacturing_place',
        'CompoundForm.manufacturing_process',
        'CompoundForm.half_life',
        'CompoundForm.lag_time',
        'CompoundForm.sdtm_domain',
        'CompoundAliasForm.name',
        'CompoundAliasForm.sentence_case_name',
        'CompoundAliasForm.is_preferred_synonym'
      ],
      routesOfAdmin: [],
      compoundAliases: [],
      steps: [
        { name: 'identifiers', title: this.$t('CompoundForm.step1_title') },
        { name: 'dosingDetails', title: this.$t('CompoundForm.step2_title') },
        { name: 'halfLife', title: this.$t('CompoundForm.step4_title') },
        { name: 'alias', title: this.$t('CompoundForm.step5_title') }
      ]
    }
  },
  computed: {
    ...mapGetters({
      substances: 'compounds/substances'
    }),
    title () {
      return (this.compound) ? this.$t('CompoundForm.edit_title') : this.$t('CompoundForm.add_title')
    }
  },
  methods: {
    addDoseValue () {
      this.form.doseValues.push({})
    },
    removeDoseValue (index) {
      this.form.doseValues.splice(index, 1)
    },
    addLagTime () {
      this.form.lagTimes.push({})
      this.form.sdtmDomains.push({})
    },
    removeLagTime (index) {
      this.form.lagTimes.splice(index, 1)
      this.form.sdtmDomains.splice(index, 1)
    },
    addStrengthValue () {
      this.form.strengthValues.push({})
    },
    removeStrengthValue (index) {
      this.form.strengthValues.splice(index, 1)
    },
    addSubstance () {
      this.form.substances.push({})
    },
    removeSubstance (index) {
      this.form.substances.splice(index, 1)
    },
    close () {
      this.$emit('close')
      this.form = this.getInitialForm()
      this.$refs.stepper.reset()
      this.$store.commit('form/CLEAR_FORM')
    },
    getInitialForm () {
      return {
        isSponsorCompound: true,
        doseValues: [{}],
        halfLife: {},
        lagTimes: [{}],
        sdtmDomains: [{}],
        strengthValues: [{}],
        substances: [{}],
        alias: {}
      }
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    async addCompound (data) {
      data.libraryName = libConstants.LIBRARY_SPONSOR
      const createdCompound = await compounds.create(data)

      try {
        // Add alias
        data.alias.compoundUid = createdCompound.data.uid
        data.alias.name = data.aliasName
        data.alias.nameSentenceCase = data.aliasNameSentenceCase
        data.alias.isPreferredSynonym = data.aliasIsPreferredSynonym
        data.alias.libraryName = data.libraryName
        data.alias.abbreviation = null
        await compoundAliases.create(data.alias)
      } catch (error) {
        // If creation of alias fails, delete the newly created compound
        await compounds.deleteObject(createdCompound.data.uid)
        throw error
      }

      this.$emit('created')
      bus.$emit('notification', { msg: this.$t('CompoundForm.add_success'), type: 'success' })
    },
    async updateCompound (data) {
      data.changeDescription = this.$t('_global.work_in_progress')
      await compounds.update(this.compound.uid, data)
      this.$emit('updated')
      bus.$emit('notification', { msg: this.$t('CompoundForm.update_success'), type: 'success' })
    },
    async createNumericValue (item) {
      item.libraryName = libConstants.LIBRARY_SPONSOR
      const resp = await numericValuesWithUnit.create(item)
      return resp.data.uid
    },
    async createNumericValues (items) {
      const result = []
      for (const item of items) {
        if (item.value && item.unitDefinitionUid) {
          result.push(await this.createNumericValue(item))
        }
      }
      return result
    },
    async createLagTime (item) {
      item.libraryName = libConstants.LIBRARY_SPONSOR
      const resp = await lagTimes.create(item)
      return resp.data.uid
    },
    async submit () {
      if (this.$store.getters['form/form'] === '' || _isEqual(this.$store.getters['form/form'], JSON.stringify(this.form))) {
        this.close()
        bus.$emit('notification', { type: 'info', msg: this.$t('_global.no_changes') })
        return
      }
      const data = { ...this.form }
      data.nameSentenceCase = data.name.toLowerCase()
      data.substanceTermsUids = []
      for (const substance of data.substances) {
        if (substance && substance.termUid) {
          data.substanceTermsUids.push(substance.termUid)
        }
      }
      delete data.substances
      data.doseValuesUids = await this.createNumericValues(data.doseValues)
      delete data.doseValues
      data.strengthValuesUids = await this.createNumericValues(data.strengthValues)
      delete data.strengthValues
      if (data.halfLife) {
        if (data.halfLife.value && data.halfLife.unitDefinitionUid) {
          data.halfLifeUid = await this.createNumericValue(data.halfLife)
        }
        delete data.halfLife
      }
      data.lagTimesUids = []
      for (const [index, item] of data.lagTimes.entries()) {
        if (item.value && item.unitDefinitionUid && this.form.sdtmDomains[index].uid) {
          item.sdtmDomainUid = this.form.sdtmDomains[index].uid
          data.lagTimesUids.push(await this.createLagTime(item))
        }
      }
      delete data.lagTimes
      if (data.brands) {
        data.brandsUids = data.brands.map(item => item.uid)
        delete data.brands
      }
      try {
        if (!this.compoundUid) {
          await this.addCompound(data)
        } else {
          await this.updateCompound(data)
        }
        this.close()
      } catch (error) {
        this.$refs.stepper.loading = false
      }
    },
    transformSubstances () {
      this.$set(this.form, 'substances', this.form.substances.map(substance => {
        return this.substances.find(item => item.termUid === substance.substanceTermUid)
      }))
    }
  },
  mounted () {
    if (this.compoundUid !== null) {
      compounds.getObject(this.compoundUid).then(resp => {
        this.compound = resp.data
      })
    }
    this.$store.dispatch('compounds/fetchSubstances').then(resp => {
      this.transformSubstances()
    })
    terms.getByCodelist('frequency').then(resp => {
      this.frequencies = resp.data.items
    })
    terms.getByCodelist('routeOfAdministration').then(resp => {
      this.routesOfAdmin = resp.data.items
    })
    terms.getByCodelist('dosageForm').then(resp => {
      this.dosageForms = resp.data.items
    })
    terms.getByCodelist('dispensedIn').then(resp => {
      this.dispensers = resp.data.items
    })
    terms.getByCodelist('deliveryDevice').then(resp => {
      this.devices = resp.data.items
    })
    terms.getByCodelist('adverseEvents').then(resp => {
      this.adverseEvents = resp.data.items
    })
    brands.getAll().then(resp => {
      this.brands = resp.data
    })
  },
  watch: {
    formShown (value) {
      if (value && this.compoundUid !== null) {
        compounds.getObject(this.compoundUid).then(resp => {
          this.compound = resp.data
        })
      } else {
        this.compound = null
      }
    },
    compound: {
      handler: function (value) {
        if (value) {
          this.form = { ...value }
          this.form.dosageFormUids = this.form.dosageForms.map(item => item.termUid)
          this.form.doseFrequencyUids = this.form.doseFrequencies.map(item => item.termUid)
          this.form.routeOfAdministrationUids = this.form.routesOfAdministration.map(item => item.termUid)
          this.form.dispensersUids = this.form.dispensers.map(item => item.termUid)
          this.form.deliveryDevicesUids = this.form.deliveryDevices.map(item => item.termUid)
          for (const field of ['doseValues', 'strengthValues', 'lagTimes']) {
            if (!this.form[field].length) {
              this.form[field] = [{}]
            }
          }
          this.form.sdtmDomains = []
          if (this.form.lagTimes.length) {
            for (const lagTime of this.form.lagTimes) {
              this.form.sdtmDomains.push({ uid: lagTime.sdtmDomainUid })
            }
          } else {
            this.form.sdtmDomains.push({})
          }
          if (!this.form.substances || !this.form.substances.length) {
            this.$set(this.form, 'substances', [{}])
          }
          if (this.substances.length) {
            this.transformSubstances()
          }

          const params = {
            filters: {
              compoundUid: { v: [value.uid] }
            }
          }
          compoundAliases.getFiltered(params).then(resp => {
            this.compoundAliases = resp.data.items
          })
        }
      },
      immediate: true
    },
    'form.name' (value) {
      if (value && !this.compound) {
        this.$set(this.form, 'aliasName', value)
      }
    },
    'form.aliasName' (value) {
      if (value) {
        this.$set(this.form, 'aliasNameSentenceCase', value.toLowerCase())
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.v-btn {
  &--right {
    right: -16px;
  }
}

.sub-v-card {
  margin-bottom: 25px;
}
</style>
