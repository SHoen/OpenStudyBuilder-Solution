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
      <v-row>
        <v-col>
          <validation-provider
            v-slot="{ errors }"
            rules="required"
            >
            <v-text-field
              :label="$t('CrfAliases.context')"
              v-model="form.context"
              dense
              clearable
              :error-messages="errors"
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
            <v-text-field
              :label="$t('_global.name')"
              v-model="form.name"
              dense
              clearable
              :error-messages="errors"
            />
          </validation-provider>
        </v-col>
      </v-row>
    </validation-observer>
  </template>
</simple-form-dialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import crfs from '@/api/crfs'
import _isEqual from 'lodash/isEqual'
import { bus } from '@/main'

export default {
  components: {
    SimpleFormDialog
  },
  props: {
    editedItem: Object,
    open: Boolean
  },
  computed: {
    title () {
      return (Object.keys(this.editedItem).length !== 0)
        ? this.$t('CrfAliases.edit_alias')
        : this.$t('CrfAliases.add_alias')
    }
  },
  data () {
    return {
      form: {},
      helpItems: []
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
        if (await this.$refs.form.confirm(this.$t('_global.cancel_changes'), options)) {
          this.close()
        }
      }
    },
    close () {
      this.$emit('close')
      this.form = {}
      this.$store.commit('form/CLEAR_FORM')
      this.$refs.observer.reset()
    },
    async submit () {
      const valid = await this.$refs.observer.validate()
      if (!valid) {
        return
      }
      this.form.libraryName = 'Sponsor'
      if (Object.keys(this.editedItem).length !== 0) {
        crfs.editAlias(this.editedItem.uid, this.form).then(resp => {
          bus.$emit('notification', { msg: this.$t('CrfAliases.alias_edited') })
          this.close()
        })
      } else {
        crfs.addAlias(this.form).then(resp => {
          bus.$emit('notification', { msg: this.$t('CrfAliases.alias_created') })
          this.close()
        })
      }
    }
  },
  mounted () {
    if (Object.keys(this.editedItem).length !== 0) {
      this.form = this.editedItem
      this.$store.commit('form/SET_FORM', this.form)
    }
  },
  watch: {
    editedItem (value) {
      if (Object.keys(value).length !== 0) {
        this.form = value
        this.$store.commit('form/SET_FORM', this.form)
      }
    }
  }
}
</script>
