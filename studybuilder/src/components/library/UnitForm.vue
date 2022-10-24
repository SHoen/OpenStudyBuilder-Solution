<template>
<simple-form-dialog
  ref="form"
  :title="title"
  :help-items="helpItems"
  :help-text="$t('HelpMessages.units')"
  @close="cancel"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <validation-observer ref="observer">
      <validation-provider
        v-if="!unit"
        v-slot="{ errors }"
        name="Library"
        rules="required"
        >
        <v-row>
          <v-col>
            <v-select
              v-model="form.libraryName"
              :label="$t('_global.library')"
              :items="libraries"
              item-text="name"
              item-value="name"
              :error-messages="errors"
              dense
              clearable
              ></v-select>
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        rules="required"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('_global.name')"
              :error-messages="errors"
              dense
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        rules="required"
        >
        <v-row>
          <v-col cols="12">
            <v-select
              v-model="form.ctUnits"
              :label="$t('UnitForm.ct_term')"
              :items="unitTerms"
              :item-text="cTermText"
              item-value="termUid"
              single-line
              multiple
              :error-messages="errors"
              dense
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        rules=""
        >
        <v-row>
          <v-col>
            <v-select
              v-model="form.unitSubsets"
              label="Unit Subset"
              :items="unitSubsets"
              item-text="sponsorPreferredName"
              item-value="termUid"
              single-line
              multiple
              :error-messages="errors"
              dense
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <v-row>
        <v-col cols="6">
          <v-switch
            v-model="form.convertibleUnit"
            :label="$t('UnitForm.convertible_unit')"
            />
          <v-switch
            v-model="form.displayUnit"
            :label="$t('UnitForm.display_unit')"
            />
          <v-switch
            v-model="form.masterUnit"
            :label="$t('UnitForm.master_unit')"
            />
          <v-switch
            v-model="form.siUnit"
            :label="$t('UnitForm.si_unit')"
            />
          <v-switch
            v-model="form.usConventionalUnit"
            :label="$t('UnitForm.us_unit')"
            />
        </v-col>
        <v-col>
          <validation-provider
            v-slot="{ errors }"
            rules=""
            >
            <ucum-unit-field v-model="form.ucum" :error-messages="errors" />
          </validation-provider>
        </v-col>
      </v-row>
      <validation-provider
        v-slot="{ errors }"
        rules=""
        >
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.unitDimension"
              :label="$t('UnitForm.dimension')"
              :items="unitDimensions"
              item-text="sponsorPreferredName"
              item-value="termUid"
              :error-messages="errors"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        rules=""
        >
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.legacyCode"
              :label="$t('UnitForm.legacy_code')"
              :error-messages="errors"
              dense
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        rules=""
        >
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.molecularWeightConvExpon"
              :label="$t('UnitForm.molecular_weight')"
              :error-messages="errors"
              dense
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        rules=""
        >
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.conversionFactorToMaster"
              :label="$t('UnitForm.conversion_factor')"
              :error-messages="errors"
              dense
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
    </validation-observer>
  </template>
</simple-form-dialog>
</template>

<script>
import { bus } from '@/main'
import terms from '@/api/controlledTerminology/terms'
import libraries from '@/api/libraries'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import StudybuilderUCUMField from '@/components/tools/StudybuilderUCUMField'

export default {
  components: {
    SimpleFormDialog,
    'ucum-unit-field': StudybuilderUCUMField
  },
  props: {
    unit: Object,
    open: Boolean
  },
  computed: {
    title () {
      return (this.objective)
        ? this.$t('UnitForm.edit_title')
        : this.$t('UnitForm.add_title')
    }
  },
  data () {
    return {
      form: this.getInitialForm(),
      helpItems: [
        'UnitForm.ct_term',
        'UnitForm.convertible_unit',
        'UnitForm.display_unit',
        'UnitForm.master_unit',
        'UnitForm.si_unit',
        'UnitForm.us_unit',
        'UnitForm.dimension',
        'UnitForm.legacy_code',
        'UnitForm.add_success',
        'UnitForm.molecular_weight',
        'UnitForm.conversion_factor'
      ],
      libraries: [],
      unitTerms: [],
      ucumUnits: [],
      unitDimensions: [],
      unitSubsets: []
    }
  },
  methods: {
    getInitialForm () {
      return {
        convertibleUnit: false,
        displayUnit: false,
        masterUnit: false,
        siUnit: false,
        usConventionalUnit: false
      }
    },
    cTermText (unit) {
      return `[${unit.termUid}] ${unit.sponsorPreferredName}`
    },
    async cancel () {
      if (this.form.libraryName === undefined) {
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
    close () {
      this.$emit('close')
      this.form = this.getInitialForm()
      this.$refs.observer.reset()
    },
    async submit () {
      const isValid = await this.$refs.observer.validate()
      if (!isValid) return
      this.$refs.form.working = true
      if (this.form.ucum.termUid) {
        this.$set(this.form, 'ucum', this.form.ucum.termUid)
      }
      if (Object.keys(this.unit).length !== 0) {
        try {
          const args = {
            uid: this.unit.uid,
            data: this.form
          }
          await this.$store.dispatch('units/updateUnit', args)
          bus.$emit('notification', { msg: 'update success' })
          this.close()
        } finally {
          this.$refs.form.working = false
        }
      } else {
        try {
          await this.$store.dispatch('units/addUnit', this.form)
          bus.$emit('notification', { msg: this.$t('UnitForm.add_success') })
          this.close()
        } finally {
          this.$refs.form.working = false
        }
      }
    }
  },
  mounted () {
    terms.getByCodelist('units').then(resp => {
      this.unitTerms = resp.data.items
    })
    terms.getByCodelist('unitDimensions').then(resp => {
      this.unitDimensions = resp.data.items
    })
    terms.getByCodelist('unitSubsets').then(resp => {
      this.unitSubsets = resp.data.items
    })
    libraries.get(1).then(resp => {
      this.libraries = resp.data
    })
    if (Object.keys(this.unit).length !== 0) {
      this.form = JSON.parse(JSON.stringify(this.unit))
      this.$set(this.form, 'ctUnits', this.unit.ctUnits.map(el => el.termUid))
      this.$set(this.form, 'unitSubsets', this.unit.unitSubsets.map(el => el.termUid))
      this.$set(this.form, 'ucum', this.unit.ucum.termUid)
      this.$set(this.form, 'unitDimension', this.unit.unitDimension.termUid)
    }
  },
  watch: {
    unit (value) {
      if (Object.keys(value).length !== 0) {
        this.form = JSON.parse(JSON.stringify(value))
        this.$set(this.form, 'ctUnits', this.unit.ctUnits.map(el => el.termUid))
        this.$set(this.form, 'unitSubsets', this.unit.unitSubsets.map(el => el.termUid))
        this.$set(this.form, 'ucum', this.unit.ucum.termUid)
        this.$set(this.form, 'unitDimension', this.unit.unitDimension.termUid)
      }
    }
  }
}
</script>
