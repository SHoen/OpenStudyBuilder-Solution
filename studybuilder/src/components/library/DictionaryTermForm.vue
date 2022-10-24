<template>
<simple-form-dialog
  ref="form"
  :title="$t('DictionaryTermForm.title', { dictionaryName })"
  :help-items="helpItems"
  @close="close"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <validation-observer ref="observer">
      <v-row>
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-text-field
              v-model="form.dictionaryId"
              :label="`${dictionaryName} ID`"
              :error-messages="errors"
              dense
              clearable
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
              v-model="form.name"
              :label="$t('_global.name')"
              :error-messages="errors"
              dense
              clearable
              @blur="setLowerCase"
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
              :label="$t('DictionaryTermForm.lower_case_name')"
              :error-messages="errors"
              dense
              clearable
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            rules=""
            >
            <v-text-field
              v-model="form.abbreviation"
              :label="$t('DictionaryTermForm.abbreviation')"
              :error-messages="errors"
              dense
              clearable
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            rules=""
            >
            <v-textarea
              v-model="form.definition"
              :label="$t('DictionaryTermForm.definition')"
              :error-messages="errors"
              dense
              clearable
              rows="1"
              auto-grow
              />
          </validation-provider>
        </v-col>
      </v-row>
      <v-row v-if="editedTerm">
        <v-col cols="12">
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-textarea
              v-model="form.changeDescription"
              :label="$t('_global.change_description')"
              :error-messages="errors"
              dense
              clearable
              rows="1"
              auto-grow
              />
          </validation-provider>
        </v-col>
      </v-row>
    </validation-observer>
  </template>
</simple-form-dialog>
</template>

<script>
import { bus } from '@/main'
import dictionaries from '@/api/dictionaries'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import _isEqual from 'lodash/isEqual'

export default {
  components: {
    SimpleFormDialog
  },
  props: {
    editedTerm: Object,
    editedTermCategory: String,
    dictionaryName: String,
    open: Boolean
  },
  data () {
    return {
      helpItems: [
        'DictionaryTermForm.dictionary_id',
        'DictionaryTermForm.name',
        'DictionaryTermForm.lower_case_name',
        'DictionaryTermForm.abbreviation',
        'DictionaryTermForm.definition'
      ],
      form: {}
    }
  },
  methods: {
    isUpdate () {
      return Boolean(this.editedTerm)
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
    close () {
      this.form = {}
      this.$store.commit('form/CLEAR_FORM')
      this.$emit('close')
    },
    submit () {
      if (this.editedTerm) {
        this.edit()
      } else {
        this.create()
      }
    },
    edit () {
      if (this.form.defComplete) {
        this.form.defComplete = 'Y'
      } else {
        this.form.defComplete = 'N'
      }
      const data = JSON.parse(JSON.stringify(this.form))
      dictionaries.edit(this.editedTerm.termUid, data).then(resp => {
        bus.$emit('notification', { msg: this.$t('DictionaryTermForm.update_success') })
        this.$emit('save')
        this.close()
      })
    },
    async create () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      this.form.libraryName = this.dictionaryName
      this.form.codelistUid = this.editedTermCategory
      const data = JSON.parse(JSON.stringify(this.form))
      dictionaries.create(data).then(resp => {
        bus.$emit('notification', { msg: this.$t('DictionaryTermForm.create_success') })
        this.$emit('save')
        this.close()
      })
    },
    initForm (form) {
      this.form = form
    },
    setLowerCase () {
      if (this.form.name) {
        this.$set(
          this.form, 'nameSentenceCase', this.form.name.toLowerCase()
        )
      }
    }
  },
  mounted () {
    if (this.editedTerm) {
      if (this.editedTerm.defComplete === 'Y') {
        this.editedTerm.defComplete = true
      } else {
        this.editedTerm.defComplete = false
      }
      this.initForm(this.editedTerm)
      this.form.changeDescription = this.$t('DictionaryTermForm.default_change_descr')
    }
    this.form.codelistUid = this.editedTermCategory
    this.$store.commit('form/SET_FORM', this.form)
  },
  watch: {
    editedTerm: {
      handler (value) {
        if (value) {
          if (this.editedTerm.defComplete === 'Y') {
            this.editedTerm.defComplete = true
          } else {
            this.editedTerm.defComplete = false
          }
          this.initForm(value)
          this.form.codelistUid = this.editedTermCategory
          this.$store.commit('form/SET_FORM', this.form)
        }
      },
      immediate: true
    }
  }
}
</script>
