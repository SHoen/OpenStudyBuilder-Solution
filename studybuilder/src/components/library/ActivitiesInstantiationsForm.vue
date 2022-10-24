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
    <template v-slot:step.type>
      <validation-provider
        v-slot="{ errors }"
        rules="required"
        >
        <v-row>
          <v-col>
            <v-select
              v-model="type"
              :items="types"
              :label="$t('ActivityForms.type')"
              item-text="name"
              item-value="value"
              dense
              clearable
              :error-messages="errors"
            />
          </v-col>
        </v-row>
      </validation-provider>
    </template>
    <template v-slot:step.basicData>
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
              class="mb-4"
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
            <v-autocomplete
              v-model="form.activities"
              :items="activities"
              :label="$t('ActivityForms.activities')"
              item-text="name"
              item-value="uid"
              dense
              clearable
              multiple
              :error-messages="errors"
              class="pt-3"
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
              class="mb-4"
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
            <v-text-field
              v-model="form.topicCode"
              :label="$t('ActivityForms.topicCode')"
              hide-details
              class="mb-4"
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
              v-model="form.adamParamCode"
              :label="$t('ActivityForms.adamCode')"
              hide-details
              class="mb-4"
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
              v-model="form.legacyDescription"
              :label="$t('ActivityForms.legacyDesc')"
              hide-details
              class="mb-4"
              :error-messages="errors"
            />
          </v-col>
        </v-row>
      </validation-provider>
    </template>
    <template v-slot:step.additionalData1="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.name"
              label="additionalData1"
              hide-details
              class="mb-4"
              :error-messages="errors"
            />
          </v-col>
        </v-row>
        </validation-provider>
      </validation-observer>
    </template>
    <template v-slot:step.additionalData2="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.name"
              label="additionalData2"
              hide-details
              class="mb-4"
              :error-messages="errors"
            />
          </v-col>
        </v-row>
        </validation-provider>
      </validation-observer>
    </template>
    <template v-slot:step.additionalData3="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          rules="required"
          >
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.name"
              label="additionalData3"
              hide-details
              class="mb-4"
              :error-messages="errors"
            />
          </v-col>
        </v-row>
        </validation-provider>
      </validation-observer>
    </template>
  </stepper-form>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</v-card>
</template>

<script>
import { bus } from '@/main'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import _isEqual from 'lodash/isEqual'
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
        ? this.$t('ActivityForms.editInstance')
        : this.$t('ActivityForms.addInstance')
    }
  },
  data () {
    return {
      form: {},
      working: false,
      type: '',
      activities: [],
      types: [
        { name: 'Reminders', value: 'reminders' },
        { name: 'Special Purposes', value: 'special-purposes' },
        { name: 'Events', value: 'events' },
        { name: 'Compound Dosings', value: 'compound-dosings' },
        { name: 'Categoric Findings', value: 'categoric-findings' },
        { name: 'Numeric Findings', value: 'numeric-findings' },
        { name: 'Textual Findings', value: 'textual-findings' },
        { name: 'Rating Scales', value: 'rating-scales' },
        { name: 'Laboratory Activities', value: 'laboratory-activities' }
      ],
      advancedSteps1: [
        { name: 'type', title: this.$t('ActivityForms.select_type') },
        { name: 'basicData', title: this.$t('ActivityForms.addBasicData') },
        { name: 'additionalData1', title: this.$t('ActivityForms.addAdditionalData') }
      ],
      advancedSteps2: [
        { name: 'type', title: this.$t('ActivityForms.select_type') },
        { name: 'basicData', title: this.$t('ActivityForms.addBasicData') },
        { name: 'additionalData2', title: this.$t('ActivityForms.addAdditionalData') }
      ],
      advancedSteps3: [
        { name: 'type', title: this.$t('ActivityForms.select_type') },
        { name: 'basicData', title: this.$t('ActivityForms.addBasicData') },
        { name: 'additionalData3', title: this.$t('ActivityForms.addAdditionalData') }
      ],
      steps: this.getInitialSteps(),
      helpItems: [
        'ActivityFormsInstantiations.select_type',
        'ActivityFormsInstantiations.name',
        'ActivityFormsInstantiations.definition',
        'ActivityFormsInstantiations.activities',
        'ActivityFormsInstantiations.topicCode',
        'ActivityFormsInstantiations.adamCode',
        'ActivityFormsInstantiations.legacyDesc'
      ]
    }
  },
  methods: {
    initForm (value) {
      this.form = {
        name: value.name,
        nameSentenceCase: value.nameSentenceCase,
        definition: value.definition,
        changeDescription: value.changeDescription,
        activitySubGroups: value.activitySubGroups
      }
      this.$store.commit('form/SET_FORM', this.form)
    },
    getInitialSteps () {
      return [
        { name: 'type', title: this.$t('ActivityForms.select_type') },
        { name: 'basicData', title: this.$t('ActivityForms.addBasicData') }
      ]
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
      this.$store.commit('form/CLEAR_FORM')
      this.$refs.observer.reset()
    },
    async submit () {
      this.form.libraryName = 'Sponsor' // Hardcoded for now at the Sinna and Mikkel request
      this.form.nameSentenceCase = this.form.name.charAt(0).toUpperCase() + this.form.name.slice(1)
      this.working = true
      if (!this.editedActivity) {
        activities.create(this.form, this.type).then(resp => {
          bus.$emit('notification', { msg: this.$t('ActivityForms.activity_created') })
          this.close()
        })
      } else {
        activities.update(this.editedActivity.uid, this.form, this.type).then(resp => {
          bus.$emit('notification', { msg: this.$t('ActivityForms.activity_updated') })
          this.close()
        })
      }
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    getActivities () {
      activities.get({}, 'activities').then(resp => {
        this.activities = resp.data.items
      })
    }
  },
  mounted () {
    if (this.editedActivity) {
      this.initForm(this.editedActivity)
    }
    this.getActivities()
  },
  watch: {
    editedActivity: {
      handler (value) {
        if (value) {
          this.initForm(value)
        }
      },
      immediate: true
    },
    type (value) {
      switch (value) {
        case 'events' || 'special-purposes' || 'reminders':
          this.steps = this.getInitialSteps()
          return
        case 'laboratory-activities' || 'rating-scales' || 'categoric-findings':
          this.steps = this.advancedSteps1
          return
        case 'compund-dosigns' || 'compounds':
          this.steps = this.advancedSteps2
          return
        case 'textual-findings' || 'numeric-findings':
          this.steps = this.advancedSteps3
      }
    }
  }
}
</script>
