<template>
<simple-form-dialog
  ref="form"
  :title="title"
  :help-items="helpItems"
  @close="cancel"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <validation-observer ref="observer">
      <validation-provider
        v-slot="{ errors }"
        >
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.armUids"
              :label="$t('StudyCohorts.study_arm')"
              data-cy="study-arm"
              :items="arms"
              item-text="name"
              item-value="armUid"
              :error-messages="errors"
              clearable
              multiple
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        >
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.branchArmUids"
              :label="$t('StudyCohorts.study_branch_arm')"
              data-cy="branch-arm"
              :items="branches"
              item-text="name"
              item-value="branchArmUid"
              :error-messages="errors"
              clearable
              multiple
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        rules="required|max:200"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('StudyCohorts.cohort_name')"
              data-cy="study-cohort-name"
              :error-messages="errors"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        rules="required|max:20"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.shortName"
              :label="$t('StudyCohorts.cohort_short_name')"
              data-cy="study-cohort-short-name"
              :error-messages="errors"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.code"
              :label="$t('StudyCohorts.cohort_code')"
              data-cy="study-cohort-code"
              :error-messages="errors"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        :rules="`min_value:1|max_value:${findMaxNuberOfSubjects()}`"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              :disabled="!form.armUids"
              :value="form.numberOfSubjects"
              @input="form.numberOfSubjects = $event !== '' ? $event : null"
              :label="$t('StudyCohorts.nuber_of_subjects')"
              data-cy="study-cohort-planned-number-of-subjects"
              :error-messages="(errors[0] && errors[0].includes($t('StudyCohorts.value_less_then'))) ? $t('StudyCohorts.number_of_subjects_exceeds') : errors"
              type="number"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <validation-provider
        v-slot="{ errors }"
        >
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.description"
              :label="$t('_global.description')"
              data-cy="study-cohort-description"
              :error-messages="errors"
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
      <div class="mt-4">
        <label class="v-label">{{ $t('StudyCohorts.colour') }}</label>
        <v-color-picker
          v-model="colorHash"
          clearable
          show-swatches
          hide-canvas
          hide-sliders
          swatches-max-height="300px"
          />
      </div>
    </validation-observer>
  </template>
</simple-form-dialog>
</template>

<script>

import { mapGetters } from 'vuex'
import arms from '@/api/arms'
import { bus } from '@/main'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import _isEqual from 'lodash/isEqual'

export default {
  components: {
    SimpleFormDialog
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    }),
    title () {
      return (Object.keys(this.editedCohort).length !== 0)
        ? this.$t('StudyCohorts.edit_cohort')
        : this.$t('StudyCohorts.add_cohort')
    }
  },
  props: {
    editedCohort: Object,
    arms: Array,
    branches: Array,
    open: Boolean
  },
  data () {
    return {
      form: {},
      helpItems: [],
      colorHash: null
    }
  },
  methods: {
    async submit () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      if (Object.keys(this.editedCohort).length !== 0) {
        this.edit()
      } else {
        this.create()
      }
    },
    async create () {
      if (this.colorHash) {
        this.form.colourCode = this.colorHash.hexa
      }
      arms.createCohort(this.selectedStudy.uid, this.form).then(resp => {
        bus.$emit('notification', { msg: this.$t('StudyCohorts.cohort_created') })
        this.close()
      })
    },
    edit () {
      if (this.colorHash) {
        this.form.colourCode = this.colorHash.hexa !== undefined ? this.colorHash.hexa : this.colorHash
      }
      arms.editCohort(this.selectedStudy.uid, this.editedCohort.cohortUid, this.form).then(resp => {
        bus.$emit('notification', { msg: this.$t('StudyCohorts.cohort_updated') })
        this.close()
      })
    },
    close () {
      this.form = {}
      this.$store.commit('form/CLEAR_FORM')
      this.colorHash = null
      this.$refs.observer.reset()
      this.$emit('close')
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
    findMaxNuberOfSubjects () {
      let subjectsSum = 0
      if (this.form.armUids) {
        this.form.armUids.forEach(el => {
          subjectsSum += this.arms.find(e => e.armUid === el).numberOfSubjects
        })
      }
      return subjectsSum
    }
  },
  mounted () {
    if (Object.keys(this.editedCohort).length !== 0) {
      this.form = JSON.parse(JSON.stringify(this.editedCohort))
      this.$set(this.form, 'armUids', this.editedCohort.armRoots ? this.editedCohort.armRoots.map(el => el.armUid) : null)
      this.$set(this.form, 'branchArmUids', this.editedCohort.branchArmRoots ? this.editedCohort.branchArmRoots.map(el => el.branchArmUid) : null)
      if (this.editedCohort.colourCode) {
        this.colorHash = this.editedCohort.colourCode
      }
      this.$store.commit('form/SET_FORM', this.form)
    }
  },
  watch: {
    editedCohort (value) {
      if (Object.keys(value).length !== 0) {
        this.form = JSON.parse(JSON.stringify(value))
        this.$set(this.form, 'armUids', value.armRoots ? value.armRoots.map(el => el.armUid) : null)
        this.$set(this.form, 'branchArmUids', value.branchArmRoots ? value.branchArmRoots.map(el => el.branchArmUid) : null)
        if (value.colourCode) {
          this.colorHash = value.colourCode
        }
        this.$store.commit('form/SET_FORM', this.form)
      }
    }
  }
}
</script>
