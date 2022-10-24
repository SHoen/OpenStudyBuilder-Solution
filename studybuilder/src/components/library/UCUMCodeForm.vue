<template>
<simple-form-dialog
  ref="form"
  :title="$t('UCUMCodeForm.title')"
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
            <ucum-unit-field
              v-model="form.name"
              :label="$t('UCUM.code')"
              :error-messages="errors"
              return-object
              @input="setValues"
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
              :label="$t('UCUM.description')"
              :error-messages="errors"
              dense
              clearable
              auto-grow
              rows="1"
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
import UcumUnitField from '@/components/tools/UCUMUnitField'

export default {
  components: {
    SimpleFormDialog,
    UcumUnitField
  },
  props: {
    codelistUid: String,
    open: Boolean
  },
  data () {
    return {
      helpItems: [
        'UCUM.code',
        'UCUM.description'
      ],
      form: {}
    }
  },
  methods: {
    close () {
      this.$refs.form.working = false
      this.form = {}
      this.$emit('close')
    },
    setValues (code) {
      this.$set(this.form, 'definition', code.guidance)
    },
    submit () {
      const valid = this.$refs.observer.validate()
      if (!valid) {
        return
      }
      this.$refs.form.working = true
      const data = { ...this.form }
      data.libraryName = 'UCUM'
      data.name = data.name.code
      data.dictionaryId = data.nameSentenceCase = data.name
      dictionaries.create(data).then(resp => {
        bus.$emit('notification', { msg: this.$t('DictionaryTermForm.create_success') })
        this.$emit('save')
        this.close()
      })
    }
  },
  mounted () {
    this.form.codelistUid = this.codelistUid
  }
}
</script>
