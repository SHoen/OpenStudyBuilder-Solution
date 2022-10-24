<template>
<stepper-form
  data-cy="form-body"
  ref="stepper"
  :title="$t('CodelistTermCreationForm.title')"
  :steps="steps"
  @close="close"
  @save="submit"
  :form-observer-getter="getObserver"
  :help-items="helpItems"
  :editData="form"
  >
  <template v-slot:step.creation_mode>
    <v-row>
      <v-col>
        <v-radio-group
          v-model="createNewTerm"
          >
          <v-radio data-cy="select-exitsing-term" :label="$t('CodelistTermCreationForm.select_mode')" :value="false" />
          <v-radio data-cy="create-new-term" :label="$t('CodelistTermCreationForm.create_mode')" :value="true" />
        </v-radio-group>
      </v-col>
    </v-row>
  </template>
  <template v-slot:step.select>
    <v-row>
      <v-col>
        <n-n-table
          v-model="selection"
          :headers="termHeaders"
          :items="terms"
          :server-items-length="total"
          :options.sync="options"
          item-key="termUid"
          class="mt-4"
          has-api
          hide-export-button
          @filter="scheduleFilterTerms"
          column-data-resource="ct/terms"
          :loading="loading"
          >
          </n-n-table>
      </v-col>
    </v-row>
  </template>
  <template v-slot:step.names="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <validation-provider
        v-slot="{ errors }"
        rules="required"
        >
        <v-row>
          <v-col>
            <v-text-field
              data-cy="term-sponsor-preferred-name"
              v-model="form.sponsorPreferredName"
              :label="$t('CodelistTermCreationForm.sponsor_pref_name')"
              :error-messages="errors"
              @blur="setSentenceCase"
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
          <v-col>
            <v-text-field
              data-cy="term-sentence-case-name"
              v-model="form.sponsorPreferredNameSentenceCase"
              :label="$t('CodelistTermCreationForm.sponsor_sentence_case_name')"
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
          <v-col>
            <v-text-field
              data-cy="term-order"
              v-model="form.order"
              :label="$t('CodelistTermCreationForm.order')"
              :error-messages="errors"
              dense
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
    </validation-observer>
  </template>
  <template v-slot:step.attributes="{ step }">
    <validation-observer :ref="`observer_${step}`">
      <validation-provider
        v-slot="{ errors }"
        rules="required"
        >
        <v-row>
          <v-col>
            <v-text-field
              data-cy="term-name"
              v-model="form.nameSubmissionValue"
              :label="$t('CodelistTermCreationForm.term_name')"
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
          <v-col>
            <v-text-field
              data-cy="term-submission-value"
              v-model="form.codeSubmissionValue"
              :label="$t('CodelistTermCreationForm.submission_value')"
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
          <v-col>
            <v-text-field
              data-cy="term-nci-preffered-name"
              v-model="form.nciPreferredName"
              :label="$t('CodelistTermCreationForm.nci_pref_name')"
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
          <v-col>
            <v-textarea
              data-cy="term-definition"
              v-model="form.definition"
              :label="$t('CodelistTermCreationForm.definition')"
              :error-messages="errors"
              dense
              clearable
              auto-grow
              rows="1"
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
              data-cy="term-synonyms"
              v-model="form.synonyms"
              :label="$t('CodelistTermCreationForm.synonyms')"
              :error-messages="errors"
              dense
              clearable
              />
          </v-col>
        </v-row>
      </validation-provider>
    </validation-observer>
  </template>
</stepper-form>
</template>

<script>
import { bus } from '@/main'
import controlledTerminology from '@/api/controlledTerminology'
import terms from '@/api/controlledTerminology/terms'
import StepperForm from '@/components/tools/StepperForm'
import NNTable from '@/components/tools/NNTable'

export default {
  components: {
    StepperForm,
    NNTable
  },
  props: {
    catalogueName: String,
    codelistUid: String
  },
  data () {
    return {
      createNewTerm: false,
      form: {},
      alternateSteps: [
        { name: 'creation_mode', title: this.$t('CodelistTermCreationForm.creation_mode_label') },
        { name: 'names', title: this.$t('CodelistTermCreationForm.create_sponsor_name') },
        { name: 'attributes', title: this.$t('CodelistTermCreationForm.create_term_attributes') }
      ],
      helpItems: [
        'CodelistTermCreationForm.sponsor_pref_name',
        'CodelistTermCreationForm.sponsor_sentence_case_name',
        'CodelistTermCreationForm.term_name',
        'CodelistTermCreationForm.submission_value',
        'CodelistTermCreationForm.nci_pref_name',
        'CodelistTermCreationForm.definition',
        'CodelistTermCreationForm.synonyms'
      ],
      selection: [],
      search: '',
      steps: this.getInitialSteps(),
      termHeaders: [
        { text: this.$t('CodelistTermCreationForm.concept_id'), value: 'termUid' },
        { text: this.$t('CodelistTermCreationForm.sponsor_name'), value: 'name.sponsorPreferredName' },
        { text: this.$t('CodelistTermCreationForm.nci_pref_name'), value: 'attributes.nciPreferredName' },
        { text: this.$t('_global.definition'), value: 'attributes.definition' }
      ],
      terms: [],
      timer: null,
      total: 0,
      options: {},
      loading: false
    }
  },
  methods: {
    close () {
      this.$emit('close')
      this.createNewTerm = true
      this.form = {}
      this.$refs.stepper.reset()
    },
    getInitialSteps () {
      return [
        { name: 'creation_mode', title: this.$t('CodelistTermCreationForm.creation_mode_label') },
        { name: 'select', title: this.$t('CodelistTermCreationForm.select_term_label') }
      ]
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    async submit () {
      if (this.createNewTerm) {
        const data = {
          ...this.form,
          catalogueName: this.catalogueName,
          codelistUid: this.codelistUid,
          libraryName: 'Sponsor'
        }
        try {
          const resp = await controlledTerminology.createCodelistTerm(data)
          bus.$emit('notification', { msg: this.$t('CodelistTermCreationForm.add_success') })
          this.$emit('created', resp.data)
          this.close()
        } finally {
          this.$refs.stepper.loading = false
        }
      } else {
        if (!this.selection.length) {
          bus.$emit('notification', { msg: this.$t('CodelistTermCreationForm.no_selection'), type: 'error' })
          return
        }
        const codelistUid = this.codelistUid
        for (const term of this.selection) {
          await controlledTerminology.addTermToCodelist(codelistUid, term.termUid)
        }
        bus.$emit('notification', { msg: this.$t('CodelistTermCreationForm.add_success') })
        this.close()
      }
    },
    setSentenceCase () {
      if (this.form.sponsorPreferredName) {
        this.$set(this.form, 'sponsorPreferredNameSentenceCase', this.form.sponsorPreferredName.toLowerCase())
      }
    },
    filterTerms (filters, sort, filtersUpdated) {
      this.filters = filters
      if (filtersUpdated) {
        this.options.page = 1
      }
      const params = {
        pageNumber: (this.options.page),
        pageSize: this.options.itemsPerPage,
        totalCount: true
      }
      if (this.filters !== undefined) {
        params.filters = this.filters
      }
      if (this.options.sortBy.length !== 0 && sort !== undefined) {
        params.sortBy = `{"${this.options.sortBy[0]}":${!sort}}`
      }
      terms.getAll(params).then(resp => {
        this.terms = resp.data.items
        this.total = resp.data.total
        this.loading = false
      })
    },
    /*
    ** Avoid sending too many request to the API
    */
    scheduleFilterTerms (filters, sort) {
      this.loading = true
      if (this.timer) {
        clearTimeout(this.timer)
        this.timer = null
      }
      this.timer = setTimeout(this.filterTerms(filters, sort), 300)
    }
  },
  mounted () {
    terms.getAll({ pageSize: 10, totalCount: true }).then(resp => {
      this.terms = resp.data.items
      this.total = resp.data.total
    })
  },
  watch: {
    createNewTerm (value) {
      this.steps = (value) ? this.alternateSteps : this.getInitialSteps()
    },
    options () {
      this.scheduleFilterTerms()
    }
  }
}
</script>
