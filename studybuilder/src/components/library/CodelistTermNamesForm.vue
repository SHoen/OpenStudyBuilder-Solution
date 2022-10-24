<template>
<v-card data-cy="form-body" color="dfltBackground">
  <v-card-title>
    <span class="dialog-title">{{ $t('CodelistTermNamesForm.title') }}</span>
    <help-button-with-panels :title="$t('_global.help')" :items="helpItems" />
  </v-card-title>
  <v-card-text class="mt-4">
    <div class="white pa-4">
      <validation-observer ref="observer">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <v-text-field
            data-cy="term-sponsor-preffered-name"
            v-model="form.sponsorPreferredName"
            :label="$t('CodelistTermCreationForm.sponsor_pref_name')"
            :error-messages="errors"
            @blur="setSentenceCase"
            clearable
            />
        </validation-provider>
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <v-text-field
            data-cy="term-sponsor-sentence-case-name"
            v-model="form.sponsorPreferredNameSentenceCase"
            :label="$t('CodelistTermCreationForm.sponsor_sentence_case_name')"
            :error-messages="errors"
            clearable
            />
        </validation-provider>
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <v-text-field
            data-cy="term-order"
            v-model="form.order"
            :label="$t('CodelistTermCreationForm.order')"
            :error-messages="errors"
            clearable
            />
        </validation-provider>
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
          <v-textarea
            data-cy="change-description"
            v-model="form.changeDescription"
            :label="$t('HistoryTable.change_description')"
            class="white py-2"
            :error-messages="errors"
            :rows="1"
            auto-grow
            />
        </validation-provider>
      </validation-observer>
    </div>
  </v-card-text>
  <v-card-actions>
    <v-spacer></v-spacer>
    <v-btn
      class="secondary-btn"
      color="white"
      @click="close"
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
</v-card>
</template>

<script>
import { bus } from '@/main'
import controlledTerminology from '@/api/controlledTerminology'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels'

export default {
  props: ['value'],
  components: {
    HelpButtonWithPanels
  },
  data () {
    return {
      form: {},
      helpItems: [
        'CodelistTermCreationForm.sponsor_pref_name',
        'CodelistTermCreationForm.sponsor_sentence_case_name',
        'CodelistTermCreationForm.order'
      ],
      working: false
    }
  },
  methods: {
    close () {
      this.$emit('close')
      this.form.changeDescription = ''
    },
    setSentenceCase () {
      if (this.form.sponsorPreferredName) {
        this.$set(this.form, 'sponsorPreferredNameSentenceCase', this.form.sponsorPreferredName.toLowerCase())
      }
    },
    async submit () {
      const isValid = await this.$refs.observer.validate()
      if (!isValid) return
      this.working = true
      try {
        const resp = await controlledTerminology.updateCodelistTermNames(this.value.termUid, this.form)
        this.$emit('input', resp.data)
        bus.$emit('notification', { msg: this.$t('CodelistTermNamesForm.update_success') })
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
            sponsorPreferredName: val.sponsorPreferredName,
            sponsorPreferredNameSentenceCase: val.sponsorPreferredNameSentenceCase,
            order: val.order
          }
        }
      },
      immediate: true
    }
  }
}
</script>
