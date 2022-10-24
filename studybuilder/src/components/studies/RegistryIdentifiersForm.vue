<template>
<simple-form-dialog
  ref="form"
  :title="$t('RegistryIdentifiersForm.title')"
  :help-items="helpItems"
  @close="cancel"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <validation-observer ref="observer">
      <v-container>
        <not-applicable-field
          :clean-function="clearCtGovId"
          :checked="form.ctGovIdNullValueCode ? true : false">
          <template v-slot:mainField="{ notApplicable }">
            <validation-provider
              v-slot="{ errors }"
              name="CTGovID"
              >
              <v-text-field
                id="ctGovId"
                :data-cy="$t('RegistryIdentifiersForm.ctgovid')"
                :label="$t('RegistryIdentifiersForm.ctgovid')"
                v-model="form.ctGovId"
                :error-messages="errors"
                dense
                clearable
                :disabled="notApplicable"
                autocomplete="off"
                ></v-text-field>
            </validation-provider>
          </template>
        </not-applicable-field>
        <not-applicable-field
          :clean-function="clearEudractId"
          :checked="form.eudractIdNullValueCode ? true : false">
          <template v-slot:mainField="{ notApplicable }">
            <validation-provider
              v-slot="{ errors }"
              name="EUDRACTID"
              >
              <v-text-field
                id="eudractId"
                :data-cy="$t('RegistryIdentifiersForm.eudractid')"
                :label="$t('RegistryIdentifiersForm.eudractid')"
                v-model="form.eudractId"
                :error-messages="errors"
                dense
                clearable
                :disabled="notApplicable"
                autocomplete="off"
                ></v-text-field>
            </validation-provider>
          </template>
        </not-applicable-field>
        <not-applicable-field
          :clean-function="clearUniversalTrialNumberUTN"
          :checked="form.universalTrialNumberUTNNullValueCode ? true : false">
          <template v-slot:mainField="{ notApplicable }">
            <validation-provider
              v-slot="{ errors }"
              name="UTN"
              >
              <v-text-field
                id="utn"
                :data-cy="$t('RegistryIdentifiersForm.utn')"
                :label="$t('RegistryIdentifiersForm.utn')"
                v-model="form.universalTrialNumberUTN"
                :error-messages="errors"
                dense
                clearable
                :disabled="notApplicable"
                autocomplete="off"
                ></v-text-field>
            </validation-provider>
          </template>
        </not-applicable-field>
        <not-applicable-field
          :clean-function="clearJapaneseTrialRegistryIdJAPIC"
          :checked="form.japaneseTrialRegistryIdJAPICNullValueCode ? true : false">
          <template v-slot:mainField="{ notApplicable }">
            <validation-provider
              v-slot="{ errors }"
              name="Japic"
              >
              <v-text-field
                id="japic"
                :data-cy="$t('RegistryIdentifiersForm.japic')"
                :label="$t('RegistryIdentifiersForm.japic')"
                v-model="form.japaneseTrialRegistryIdJAPIC"
                :error-messages="errors"
                dense
                clearable
                :disabled="notApplicable"
                autocomplete="off"
                ></v-text-field>
            </validation-provider>
          </template>
        </not-applicable-field>
        <not-applicable-field
          :clean-function="clearInvestigationalNewDrugApplicationNumberIND"
          :checked="form.investigationalNewDrugApplicationNumberINDNullValueCode ? true : false">
          <template v-slot:mainField="{ notApplicable }">
            <validation-provider
              v-slot="{ errors }"
              name="IND"
              >
              <v-text-field
                id="ind"
                :data-cy="$t('RegistryIdentifiersForm.ind')"
                :label="$t('RegistryIdentifiersForm.ind')"
                v-model="form.investigationalNewDrugApplicationNumberIND"
                :error-messages="errors"
                dense
                clearable
                :disabled="notApplicable"
                autocomplete="off"
                ></v-text-field>
            </validation-provider>
          </template>
        </not-applicable-field>
      </v-container>
    </validation-observer>
  </template>
</simple-form-dialog>
</template>

<script>
import _isEqual from 'lodash/isEqual'
import { mapGetters } from 'vuex'
import { bus } from '@/main'
import NotApplicableField from '@/components/tools/NotApplicableField'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'

export default {
  components: {
    NotApplicableField,
    SimpleFormDialog
  },
  props: {
    identifiers: Object,
    open: Boolean
  },
  computed: {
    ...mapGetters({
      selectedStudy: 'studiesGeneral/selectedStudy'
    })
  },
  data () {
    return {
      form: JSON.parse(JSON.stringify(this.identifiers)),
      helpItems: [
        'NullFlavorSelect.label',
        'RegistryIdentifiersForm.ctgovid',
        'RegistryIdentifiersForm.eudractid',
        'RegistryIdentifiersForm.utn',
        'RegistryIdentifiersForm.japic'
      ]
    }
  },
  watch: {
    identifiers (value) {
      this.form = JSON.parse(JSON.stringify(value))
    }
  },
  methods: {
    clearCtGovId () {
      this.$set(this.form, 'ctGovId', '')
      if (this.form.ctGovIdNullValueCode) {
        this.$set(this.form, 'ctGovIdNullValueCode', null)
      } else {
        this.$set(this.form, 'ctGovIdNullValueCode', { termUid: this.$t('_global.na_uid'), name: this.$t('_global.not_applicable_full_name') })
      }
    },
    clearEudractId () {
      this.$set(this.form, 'eudractId', '')
      if (this.form.eudractIdNullValueCode) {
        this.$set(this.form, 'eudractIdNullValueCode', null)
      } else {
        this.$set(this.form, 'eudractIdNullValueCode', { termUid: this.$t('_global.na_uid'), name: this.$t('_global.not_applicable_full_name') })
      }
    },
    clearUniversalTrialNumberUTN () {
      this.$set(this.form, 'universalTrialNumberUTN', '')
      if (this.form.universalTrialNumberUTNNullValueCode) {
        this.$set(this.form, 'universalTrialNumberUTNNullValueCode', null)
      } else {
        this.$set(this.form, 'universalTrialNumberUTNNullValueCode', { termUid: this.$t('_global.na_uid'), name: this.$t('_global.not_applicable_full_name') })
      }
    },
    clearJapaneseTrialRegistryIdJAPIC () {
      this.$set(this.form, 'japaneseTrialRegistryIdJAPIC', '')
      if (this.form.japaneseTrialRegistryIdJAPICNullValueCode) {
        this.$set(this.form, 'japaneseTrialRegistryIdJAPICNullValueCode', null)
      } else {
        this.$set(this.form, 'japaneseTrialRegistryIdJAPICNullValueCode', { termUid: this.$t('_global.na_uid'), name: this.$t('_global.not_applicable_full_name') })
      }
    },
    clearInvestigationalNewDrugApplicationNumberIND () {
      this.$set(this.form, 'investigationalNewDrugApplicationNumberIND', '')
      if (this.form.investigationalNewDrugApplicationNumberINDNullValueCode) {
        this.$set(this.form, 'investigationalNewDrugApplicationNumberINDNullValueCode', null)
      } else {
        this.$set(this.form, 'investigationalNewDrugApplicationNumberINDNullValueCode', { termUid: this.$t('_global.na_uid'), name: this.$t('_global.not_applicable_full_name') })
      }
    },
    close () {
      this.$emit('close')
      this.$refs.observer.reset()
    },
    async cancel () {
      if (_isEqual(this.identifiers, this.form)) {
        this.close()
        return
      }
      const options = {
        type: 'warning',
        cancelLabel: this.$t('_global.cancel'),
        agreeLabel: this.$t('_global.continue')
      }
      if (await this.$refs.form.confirm(this.$t('_global.cancel_changes'), options)) {
        this.close()
      }
    },
    unsetValues () {
      this.$set(this.form, 'ctGovId', null)
      this.$set(this.form, 'eudractId', null)
      this.$set(this.form, 'universalTrialNumberUTN', null)
      this.$set(this.form, 'japaneseTrialRegistryIdJAPIC', null)
      this.$set(this.form, 'investigationalNewDrugApplicationNumberIND', null)
    },
    async submit () {
      if (_isEqual(this.identifiers, this.form)) {
        bus.$emit('notification', { msg: this.$t('_global.no_changes'), type: 'info' })
        this.close()
        return
      }
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      const data = {
        registryIdentifiers: this.form
      }
      this.$refs.form.working = true
      try {
        await this.$store.dispatch('manageStudies/editStudyIdentification', [this.selectedStudy.uid, data])
        this.$emit('updated', this.form)
        bus.$emit('notification', { msg: this.$t('RegistryIdentifiersForm.update_success') })
        this.close()
      } finally {
        this.$refs.form.working = false
      }
    }
  }
}
</script>
