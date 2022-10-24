<template>
<v-card color="dfltBackground">
  <v-card-title>
    <span class="dialog-title">{{ $t('CodelistAttributesForm.title') }}</span>
    <help-button-with-panels :title="$t('_global.help')" :items="helpItems" />
  </v-card-title>
  <v-card-text>
    <div class="white px-2">
      <validation-observer ref="observer">
        <v-row class="mt-4">
          <v-col>
            <validation-provider
              v-slot="{ errors }"
              rules="required"
              >
              <v-text-field
                v-model="form.name"
                :label="$t('CodelistAttributesForm.name')"
                :error-messages="errors"
                dense
                clearable
                />
            </validation-provider>
          </v-col>
        </v-row>
        <v-row class="mt-4">
          <v-col>
            <validation-provider
              v-slot="{ errors }"
              rules="required"
              >
              <v-text-field
                v-model="form.submissionValue"
                :label="$t('CodelistAttributesForm.subm_value')"
                :error-messages="errors"
                dense
                clearable
                />
            </validation-provider>
          </v-col>
        </v-row>
        <v-row class="mt-4">
          <v-col>
            <validation-provider
              v-slot="{ errors }"
              rules="required"
              >
              <v-text-field
                v-model="form.nciPreferredName"
                :label="$t('CodelistAttributesForm.nci_pref_name')"
                :error-messages="errors"
                dense
                clearable
                />
            </validation-provider>
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-switch
              v-model="form.extensible"
              :label="$t('CodelistAttributesForm.extensible')"
              />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <validation-provider
              v-slot="{ errors }"
              rules="required"
              >
              <v-textarea
                v-model="form.definition"
                :label="$t('CodelistAttributesForm.definition')"
                :error-messages="errors"
                rows="1"
                clearable
                auto-grow
                />
            </validation-provider>
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <validation-provider
              v-slot="{ errors }"
              rules="required"
              >
              <v-textarea
                v-model="form.changeDescription"
                :label="$t('HistoryTable.change_description')"
                :error-messages="errors"
                :rows="1"
                clearable
                auto-grow
                />
            </validation-provider>
          </v-col>
        </v-row>
      </validation-observer>
    </div>
  </v-card-text>
  <v-card-actions class="pb-6 px-6">
    <v-spacer></v-spacer>
    <v-btn
      class="secondary-btn"
      color="white"
      @click="cancel"
      >
      {{ $t('_global.cancel') }}
    </v-btn>
    <v-btn
      color="secondary"
      :loading="working"
      @click="submit"
      >
      {{ $t('_global.save') }}
    </v-btn>
  </v-card-actions>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</v-card>
</template>

<script>
import { bus } from '@/main'
import controlledTerminology from '@/api/controlledTerminology'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels'
import _isEqual from 'lodash/isEqual'
import ConfirmDialog from '@/components/tools/ConfirmDialog'

export default {
  components: {
    ConfirmDialog,
    HelpButtonWithPanels
  },
  props: ['value'],
  data () {
    return {
      form: {},
      helpItems: [
        'CodelistAttributesForm.name',
        'CodelistAttributesForm.subm_value',
        'CodelistAttributesForm.nci_pref_name',
        'CodelistAttributesForm.extensible',
        'CodelistAttributesForm.definition'
      ],
      working: false
    }
  },
  methods: {
    async cancel () {
      if (this.$store.getters['form/form'] === '' || _isEqual(this.$store.getters['form/form'], JSON.stringify(this.form))) {
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
      this.$store.commit('form/CLEAR_FORM')
      this.$emit('close')
      this.form = {}
    },
    async submit () {
      const isValid = await this.$refs.observer.validate()
      if (!isValid) return
      this.working = true
      try {
        const resp = await controlledTerminology.updateCodelistAttributes(this.value.codelistUid, this.form)
        this.$emit('input', resp.data)
        bus.$emit('notification', { msg: this.$t('CodelistAttributesForm.update_success') })
        this.close()
      } finally {
        this.working = false
      }
    }
  },
  watch: {
    value: {
      handler (val) {
        if (val) {
          this.form = {
            name: val.name,
            submissionValue: val.submissionValue,
            nciPreferredName: val.nciPreferredName,
            extensible: val.extensible,
            definition: val.definition
          }
          this.$store.commit('form/SET_FORM', this.form)
        }
      },
      immediate: true
    }
  }
}
</script>
