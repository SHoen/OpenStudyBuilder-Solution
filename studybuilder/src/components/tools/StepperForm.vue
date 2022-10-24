<template>
<v-card class="pl-6 pr-6 pb-4" color="dfltBackground">
  <v-card-title class="pl-0">
    <span class="dialog-title">{{ title }}</span>
    <help-button-with-panels :title="$t('_global.help')" :items="helpItems" />
  </v-card-title>
  <v-card-text class="mt-4 white">
    <v-stepper
      v-model="currentStep"
      vertical
      >
      <template v-for="(step, index) in steps">
        <v-stepper-step
          :key="`stepper-${index}`"
          :complete="currentStep > index + 1 || editable"
          :step="index + 1"
          color="secondary"
          :editable="editable"
          :edit-icon="editable ? '$complete' : '$edit'"
          >
          <span class="text-h6" :class="{ 'step-title': currentStep >= index + 1 }">{{ step.title }}</span>
        </v-stepper-step>
        <v-stepper-content
          :key="`content-${index}`"
          :step="index + 1"
          >
          <v-sheet v-if="!step.noStyle" elevation="4" class="ma-2 pa-4" :rounded="false">
            <slot :name="`step.${step.name}`" v-bind:step="index + 1" />
          </v-sheet>
          <template v-else>
            <slot :name="`step.${step.name}`" v-bind:step="index + 1" />
          </template>
          <div class="mx-2 mt-6 mb-1">
            <v-btn
              color="white"
              class="secondary-btn"
              @click="cancel"
              >
              {{ $t('_global.cancel') }}
            </v-btn>
            <v-btn
              v-if="currentStep > 1"
              color="white"
              class="secondary-btn ml-2"
              @click="currentStep = index"
              >
              {{ $t('_global.previous') }}
            </v-btn>
            <v-btn
              v-if="currentStep < steps.length"
              :data-cy="step.name + '-continue-button'"
              color="secondary"
              class="ml-2"
              @click="goToStep(index + 1, index + 2)"
              >
              {{ $t('_global.continue') }}
            </v-btn>
            <v-btn
              :data-cy="step.name + '-save-button'"
              v-if="currentStep >= steps.length || editable"
              color="secondary"
              class="ml-2"
              @click="submit"
              :loading="loading"
              >
              {{ $t('_global.save') }}
            </v-btn>
          </div>
        </v-stepper-content>
      </template>
    </v-stepper>
  </v-card-text>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</v-card>
</template>

<script>
import HelpButtonWithPanels from './HelpButtonWithPanels'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import _isEqual from 'lodash/isEqual'

export default {
  components: {
    HelpButtonWithPanels,
    ConfirmDialog
  },
  props: {
    title: String,
    steps: Array,
    formObserverGetter: Function,
    editable: {
      type: Boolean,
      default: false
    },
    extraStepValidation: {
      type: Function,
      required: false
    },
    helpItems: Array,
    editData: Object
  },
  data () {
    return {
      currentStep: 1,
      loading: false
    }
  },
  mounted () {
    this.$store.commit('form/SET_FORM', this.editData)
  },
  methods: {
    async cancel () {
      if (this.$store.getters['form/form'] === '' || _isEqual(this.$store.getters['form/form'], JSON.stringify(this.editData))) {
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
      this.reset()
    },
    reset () {
      this.currentStep = 1
      this.steps.forEach((item, index) => {
        const observer = this.formObserverGetter(index + 1)
        if (observer !== undefined) {
          observer.reset()
        }
      })
      this.loading = false
    },
    async validateStepObserver (step) {
      const observer = this.formObserverGetter(step)
      if (observer !== undefined) {
        return await observer.validate()
      }
      return true
    },
    async goToStep (currentStep, nextStep) {
      if (!await this.validateStepObserver(currentStep)) {
        return
      }
      if (this.extraStepValidation) {
        if (!await this.extraStepValidation(currentStep)) {
          return
        }
      }
      this.currentStep = nextStep
    },
    setCurrentStep (value) {
      this.currentStep = value
    },
    async submit () {
      if (!await this.validateStepObserver(this.currentStep)) {
        return
      }
      this.loading = true
      this.$emit('save')
    }
  },
  watch: {
    currentStep (value) {
      this.$emit('change', value)
    }
  }
}
</script>

<style scoped lang="scss">
.v-stepper {
  box-shadow: none;
  background-color: var(--v-dltBackground-base);
}

.step-title {
  color: var(--v-secondary-base) !important;
  font-size: 16px;
}
</style>
