<template>
<simple-form-dialog
  ref="form"
  :title="title"
  :help-items="helpItems"
  @close="close"
  @submit="submit"
  :open="open"
  >
  <template v-slot:body>
    <validation-observer ref="observer">
      <validation-provider
        v-slot="{ errors }"
        rules="required"
        >
        <v-row>
          <v-col>
            <v-autocomplete
              :label="$t('ActivityForms.activity_subgroup')"
              :items="subGroups"
              v-model="form.activitySubGroup"
              item-text="name"
              item-value="uid"
              :error-messages="errors"
              dense
              clearable
              ></v-autocomplete>
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
              :label="$t('ActivityForms.name')"
              v-model="form.name"
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
              :label="$t('ActivityForms.definition')"
              v-model="form.definition"
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
        v-if="editedActivity"
        v-slot="{ errors }"
        >
        <v-row>
          <v-col>
            <label class="v-label">{{ $t('ActivityForms.reason_for_change') }}</label>
            <v-textarea
              v-model="form.changeDescription"
              :error-messages="errors"
              dense
              clearable
              auto-grow
              rows="1"
              />
          </v-col>
        </v-row>
      </validation-provider>
    </validation-observer>
  </template>
</simple-form-dialog>
</template>

<script>
import { bus } from '@/main'
import _isEqual from 'lodash/isEqual'
import _isEmpty from 'lodash/isEmpty'
import activities from '@/api/activities'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'

export default {
  components: {
    SimpleFormDialog
  },
  props: {
    editedActivity: Object,
    open: Boolean
  },
  computed: {
    title () {
      return (this.editedActivity)
        ? this.$t('ActivityForms.edit_activity')
        : this.$t('ActivityForms.add_activity')
    }
  },
  data () {
    return {
      form: {},
      subGroups: [],
      libraries: [],
      helpItems: [
        'ActivityForms.activity_subgroup',
        'ActivityForms.name',
        'ActivityForms.definition'
      ]
    }
  },
  methods: {
    initForm (value) {
      this.form = {
        name: value.name,
        nameSentenceCase: '',
        definition: value.definition,
        changeDescription: value.changeDescription,
        libraryName: value.libraryName
      }
      if (!_isEmpty(value)) {
        this.form.nameSentenceCase = value.name.charAt(0).toUpperCase() + value.name.slice(1)
        this.form.activitySubGroup = value.activitySubGroup
      }
      this.$store.commit('form/SET_FORM', this.form)
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
      this.$emit('close')
      this.form = {}
      this.$store.commit('form/CLEAR_FORM')
      this.$refs.observer.reset()
    },
    async submit () {
      this.form.libraryName = 'Sponsor' // Hardcoded for now at the Sinna and Mikkel request
      this.form.nameSentenceCase = this.form.name.charAt(0).toUpperCase() + this.form.name.slice(1)
      if (!this.editedActivity) {
        activities.create(this.form, 'activities').then(resp => {
          bus.$emit('notification', { msg: this.$t('ActivityForms.activity_created') })
          this.close()
        })
      } else {
        activities.update(this.editedActivity.uid, this.form, 'activities').then(resp => {
          bus.$emit('notification', { msg: this.$t('ActivityForms.activity_updated') })
          this.close()
        })
      }
    },
    getSubGroups () {
      activities.get({}, 'activity-sub-groups').then(resp => {
        this.subGroups = resp.data.items
      })
    }
  },
  mounted () {
    if (this.editedActivity) {
      this.initForm(this.editedActivity)
    }
    this.getSubGroups()
  },
  watch: {
    editedActivity: {
      handler (value) {
        if (value) {
          this.initForm(value)
        }
      },
      immediate: true
    }
  }
}
</script>
