<template>
<v-card>
  <stepper-form
    ref="stepper"
    :title="title"
    :steps="steps"
    @close="cancel"
    @save="submit"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    >
    <template v-slot:step.select>
      <v-row>
        <v-col>
          <v-radio-group
            v-model="subgroup"
            :disabled="editing"
          >
            <v-radio :label="$t('ActivityForms.group')" :value="false" />
            <v-radio :label="$t('ActivityForms.subgroup')" :value="true" />
          </v-radio-group>
        </v-col>
      </v-row>
    </template>
    <template v-slot:step.details>
      <validation-provider
        v-slot="{ errors }"
        rules="required"
        v-if="subgroup"
        >
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.activityGroups"
              :items="groups"
              :label="$t('ActivityForms.groups')"
              item-text="name"
              item-value="uid"
              dense
              clearable
              multiple
              :error-messages="errors"
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
              v-model="form.name"
              :label="$t('ActivityForms.name')"
              hide-details
              :error-messages="errors"
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
              v-model="form.definition"
              :label="$t('ActivityForms.definition')"
              hide-details
              :error-messages="errors"
              auto-grow
              rows="1"
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
              v-if="editing"
              v-model="form.changeDescription"
              :label="$t('ActivityForms.change_description')"
              hide-details
              :error-messages="errors"
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
      </validation-provider>
    </template>
  </stepper-form>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</v-card>
</template>

<script>
import { bus } from '@/main'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import _isEqual from 'lodash/isEqual'
import _isEmpty from 'lodash/isEmpty'
import StepperForm from '@/components/tools/StepperForm'
import activities from '@/api/activities'

export default {
  components: {
    ConfirmDialog,
    StepperForm
  },
  props: {
    editedActivity: Object
  },
  computed: {
    title () {
      return (this.editedActivity)
        ? this.$t('ActivityForms.edit_group')
        : this.$t('ActivityForms.add_group')
    }
  },
  data () {
    return {
      form: {},
      subgroup: false,
      steps: [
        { name: 'select', title: this.$t('ActivityForms.select_type') },
        { name: 'details', title: this.$t('ActivityForms.add_additional_data') }
      ],
      groups: [],
      loading: false,
      editing: false,
      libraries: [],
      helpItems: [
        'ActivityFormsGrouping.select_type',
        'ActivityFormsGrouping.name',
        'ActivityFormsGrouping.definition'
      ]
    }
  },
  methods: {
    initForm (value) {
      this.editing = true
      if (value.uid.includes('SubGroup')) {
        this.subgroup = true
      } else {
        this.subgroup = false
      }
      this.form = {
        name: value.name,
        nameSentenceCase: '',
        definition: value.definition,
        changeDescription: value.changeDescription,
        activityGroups: []
      }
      if (!_isEmpty(value)) {
        this.form.nameSentenceCase = value.name.charAt(0).toUpperCase() + value.name.slice(1)
        if (!_isEmpty(value.activityGroups)) {
          value.activityGroups.forEach(element => {
            this.form.activityGroups.push(element.uid)
          })
        }
      }
      this.$store.commit('form/SET_FORM', this.form)
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
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
        if (await this.$refs.confirm.open(this.$t('_global.cancel_changes'), options)) {
          this.close()
        }
      }
    },
    close () {
      this.$emit('close')
      this.form = {}
      this.editing = false
      this.$store.commit('form/CLEAR_FORM')
      this.$refs.stepper.reset()
    },
    async submit () {
      this.form.libraryName = 'Sponsor' // Hardcoded for now at the Sinna and Mikkel request
      this.form.nameSentenceCase = this.form.name.charAt(0).toUpperCase() + this.form.name.slice(1)
      if (!this.editedActivity) {
        if (!this.subgroup) {
          activities.create(this.form, 'activity-groups').then(resp => {
            bus.$emit('notification', { msg: this.$t('ActivityForms.group_created') })
            this.close()
          })
        } else {
          activities.create(this.form, 'activity-sub-groups').then(resp => {
            bus.$emit('notification', { msg: this.$t('ActivityForms.subgroup_created') })
            this.close()
          })
        }
      } else {
        if (!this.subgroup) {
          activities.update(this.editedActivity.uid, this.form, 'activity-groups').then(resp => {
            bus.$emit('notification', { msg: this.$t('ActivityForms.group_updated') })
            this.close()
          })
        } else {
          activities.update(this.editedActivity.uid, this.form, 'activity-sub-groups').then(resp => {
            bus.$emit('notification', { msg: this.$t('ActivityForms.subgroup_updated') })
            this.close()
          })
        }
      }
      this.$refs.stepper.loading = false
    },
    checkIfEqual () {
      if (_isEqual(this.form.changeDescription, this.editedActivity.changeDescription) &&
          _isEqual(this.form.definition, this.editedActivity.definition) &&
          _isEqual(this.form.name, this.editedActivity.name)) {
        return true
      } else {
        return false
      }
    },
    getGroups () {
      activities.get({}, 'activity-groups').then(resp => {
        this.groups = resp.data.items
      })
    }
  },
  mounted () {
    if (this.editedActivity) {
      this.initForm(this.editedActivity)
    }
    this.getGroups()
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
