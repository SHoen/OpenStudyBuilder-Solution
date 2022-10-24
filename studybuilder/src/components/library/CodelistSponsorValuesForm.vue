<template>
<v-card data-cy="form-body" color="dfltBackground">
  <v-card-title>
    <span class="dialog-title">{{ $t('CodelistSponsorValuesForm.title') }}</span>
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
              data-cy="sponsor-preffered-name"
              v-model="form.name"
              :label="$t('CodelistSponsorValuesForm.pref_name')"
              :error-messages="errors"
              dense
              clearable
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="6">
          <v-switch
            v-model="form.templateParameter"
            :label="$t('CodelistSponsorValuesForm.tpl_parameter')"
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
              data-cy="change-description"
              v-model="form.changeDescription"
              :label="$t('HistoryTable.change_description')"
              :error-messages="errors"
              rows="1"
              auto-grow
              clearable
              class="white pa-2"
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
      data-cy="save-button"
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
    HelpButtonWithPanels,
    ConfirmDialog
  },
  props: ['value'],
  data () {
    return {
      form: {},
      helpItems: [
        'CodelistSponsorValuesForm.pref_name',
        'CodelistSponsorValuesForm.tpl_parameter'
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
      this.$emit('close')
      this.$store.commit('form/CLEAR_FORM')
    },
    async submit () {
      const isValid = await this.$refs.observer.validate()
      if (!isValid) return
      this.working = true
      try {
        const resp = await controlledTerminology.updateCodelistNames(this.value.codelistUid, this.form)
        this.$emit('input', resp.data)
        bus.$emit('notification', { msg: this.$t('CodelistSponsorValuesForm.update_success') })
        delete this.form.changeDescription
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
            templateParameter: val.templateParameter
          }
          this.$store.commit('form/SET_FORM', this.form)
        }
      },
      immediate: true
    }
  }
}
</script>
