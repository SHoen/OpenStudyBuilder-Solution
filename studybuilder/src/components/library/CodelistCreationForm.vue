<template>
<div>
  <stepper-form
    ref="stepper"
    :title="$t('CodelistCreationForm.title')"
    :steps="steps"
    @close="cancel"
    @save="submit"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    >
    <template v-slot:step.catalogue="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <v-row>
            <v-col>
              <v-select
                data-cy="catalogue-dropdown"
                v-model="form.catalogueName"
                :label="$t('CodelistCreationForm.catalogue')"
                :items="catalogues"
                item-text="name"
                item-value="name"
                clearable
                dense
                :error-messages="errors"
                persistent-hint
                />
            </v-col>
          </v-row>
        </validation-provider>
      </validation-observer>
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
                data-cy="sponsor-preffered-name"
                v-model="form.sponsorPreferredName"
                :label="$t('CodelistSponsorValuesForm.pref_name')"
                :error-messages="errors"
                clearable
                dense
                class="mt-2"
                />
            </v-col>
          </v-row>
        </validation-provider>
        <v-row>
          <v-col>
            <v-switch
              v-model="form.templateParameter"
              :label="$t('CodelistSponsorValuesForm.tpl_parameter')"
              />
          </v-col>
        </v-row>
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
                data-cy="codelist-name"
                v-model="form.name"
                :label="$t('CodelistAttributesForm.name')"
                :error-messages="errors"
                clearable
                dense
                class="mt-3"
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
                data-cy="submission-value"
                v-model="form.submissionValue"
                :label="$t('CodelistAttributesForm.subm_value')"
                :error-messages="errors"
                dense
                clearable
                class="mt-4"
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
                data-cy="nci-preffered-name"
                v-model="form.nciPreferredName"
                :label="$t('CodelistAttributesForm.nci_pref_name')"
                :error-messages="errors"
                dense
                clearable
                class="mt-4"
                />
            </v-col>
          </v-row>
        </validation-provider>
        <v-row>
          <v-col>
            <v-switch
              data-cy="extensible-toggle"
              v-model="form.extensible"
              :label="$t('CodelistAttributesForm.extensible')"
              class="mt-2"
              />
          </v-col>
        </v-row>
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <v-row>
            <v-col>
              <v-textarea
                data-cy="definition"
                v-model="form.definition"
                :label="$t('CodelistAttributesForm.definition')"
                :error-messages="errors"
                rows="1"
                clearable
                auto-grow
                />
            </v-col>
          </v-row>
        </validation-provider>
      </validation-observer>
    </template>
  </stepper-form>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</div>
</template>

<script>
import { mapGetters } from 'vuex'
import controlledTerminology from '@/api/controlledTerminology'
import StepperForm from '@/components/tools/StepperForm'
import ConfirmDialog from '@/components/tools/ConfirmDialog'

export default {
  components: {
    StepperForm,
    ConfirmDialog
  },
  props: ['catalogue'],
  computed: {
    ...mapGetters({
      catalogues: 'ctCatalogues/catalogues'
    })
  },
  data () {
    return {
      form: {
        extensible: false,
        libraryName: 'Sponsor',
        templateParameter: false
      },
      helpItems: [
        'CodelistCreationForm.catalogue',
        'CodelistSponsorValuesForm.pref_name',
        'CodelistSponsorValuesForm.tpl_parameter',
        'CodelistAttributesForm.name',
        'CodelistAttributesForm.subm_value',
        'CodelistAttributesForm.nci_pref_name',
        'CodelistAttributesForm.extensible',
        'CodelistAttributesForm.definition'
      ],
      steps: [
        { name: 'catalogue', title: this.$t('CodelistCreationForm.step1_title') },
        { name: 'names', title: this.$t('CodelistCreationForm.step2_title') },
        { name: 'attributes', title: this.$t('CodelistCreationForm.step3_title') }
      ]
    }
  },
  methods: {
    async cancel () {
      if (this.form.catalogueName === 'All') {
        this.close()
      } else {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue')
        }
        if (await this.$refs.confirm.open(this.$t('_global.cancel_changes'), options)) {
          this.close()
        }
      }
    },
    close () {
      this.$emit('close')
      this.form = {}
      this.$refs.stepper.reset()
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    async submit () {
      this.form.terms = []
      const data = JSON.parse(JSON.stringify(this.form))
      try {
        const resp = await controlledTerminology.createCodelist(data)
        this.$emit('created', resp.data)
        this.close()
      } finally {
        this.$refs.stepper.loading = false
      }
    }
  },
  mounted () {
    this.form.catalogueName = this.catalogue
  }
}
</script>
