<template>
<v-card data-cy="form-body" color="dfltBackground fullscreen-dialog">
  <v-card-title>
    <span class="dialog-title ml-6">{{ title }}</span>
    <help-button v-if="helpText" :help-text="helpText" />
    <help-button-with-panels v-if="helpItems" :title="$t('_global.help')" :items="helpItems" />
  </v-card-title>
  <v-card-text class="mt-4 dfltBackground">
    <v-stepper
      v-model="currentStep"
      >
      <v-stepper-header class="white mx-8">
        <template v-for="(step, index) in steps">
          <v-stepper-step
            :key="`stepper-${index}`"
            :complete="currentStep > index + 1 || editable"
            :step="index + 1"
            color="secondary"
            :editable="editable"
            :edit-icon="editable ? '$complete' : '$edit'"
            >
            <span class="bigger" :class="{ 'step-title': currentStep >= index + 1, 'step-title-inactive': currentStep < index + 1 }">{{ step.title }}</span>
          </v-stepper-step>
          <v-divider :key="`divider-${index}`" v-if="index < steps.length - 1"></v-divider>
        </template>
      </v-stepper-header>
      <v-stepper-items>
        <v-stepper-content
          v-for="(step, index) in steps"
          :key="`content-${index}`"
          :step="index + 1"
          >
          <v-sheet elevation="4" class="ma-2 pa-4">
            <v-row>
              <v-col v-if="step.belowDisplay" cols="12" class="d-flex align-start justify-end py-4">
                <div class="mx-2">
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
                  <slot :name="`step.${step.name}.actions.middle`" v-bind:step="index + 1" />
                  <v-btn
                   :data-cy="step.name + '-continue-button'"
                    v-if="currentStep < steps.length"
                    color="secondary"
                    class="ml-2"
                    @click="goToStep(index + 1, index + 2)"
                    >
                    {{ $t('_global.continue') }}
                  </v-btn>
                  <v-btn
                    :data-cy="step.name + '-save-button'"
                    v-if="currentStep >= steps.length"
                    color="secondary"
                    class="ml-2"
                    @click="submit"
                    :loading="loading"
                    >
                    {{ $t('_global.save') }}
                  </v-btn>
                  <slot :name="`step.${step.name}.afterActions`" v-bind:step="index + 1" />
                </div>
              </v-col>
              <v-col :cols="step.belowDisplay ? 12 : 8" class="pr-0">
                <slot :name="`step.${step.name}`" v-bind:step="index + 1" />
              </v-col>
              <v-col v-if="!step.belowDisplay" cols="4" class="d-flex align-start justify-end py-4">
                <div class="mx-2">
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
                  <slot :name="`step.${step.name}.actions.middle`" v-bind:step="index + 1" />
                  <v-btn
                   :data-cy="step.name + '-continue-button'"
                    v-if="currentStep < steps.length"
                    color="secondary"
                    class="ml-2"
                    @click="goToStep(index + 1, index + 2)"
                    >
                    {{ $t('_global.continue') }}
                  </v-btn>
                  <v-btn
                    :data-cy="step.name + '-save-button'"
                    v-if="currentStep >= steps.length"
                    color="secondary"
                    class="ml-2"
                    @click="submit"
                    :loading="loading"
                    >
                    {{ $t('_global.save') }}
                  </v-btn>
                  <slot :name="`step.${step.name}.afterActions`" v-bind:step="index + 1" />
                </div>
              </v-col>
              <slot :name="`step.${step.name}.after`" v-bind:step="index + 1" />
            </v-row>
          </v-sheet>
        </v-stepper-content>
      </v-stepper-items>
    </v-stepper>
  </v-card-text>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
  <template v-if="debug">
    <div class="debug">{{ editData }}</div>
  </template>
</v-card>
</template>

<script>
import HelpButton from '@/components/tools/HelpButton'
import HelpButtonWithPanels from '@/components/tools/HelpButtonWithPanels'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import _isEqual from 'lodash/isEqual'

export default {
  components: {
    HelpButton,
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
    helpText: {
      type: String,
      required: false
    },
    helpItems: {
      type: Array,
      required: false
    },
    editData: Object,
    debug: Boolean
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
      this.$nextTick(() => {
        this.$emit('stepLoaded', nextStep)
      })
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
    editData (value) {
      if (this.$store.getters['form/form'] === '') {
        this.$store.commit('form/SET_FORM', value)
      }
    }
  }
}
</script>

<style scoped lang="scss">
.v-stepper {
  background-color: var(--v-dltBackground-base) !important;
}
.bigger {
  font-size: large;
}
.step-title {
  color: var(--v-secondary-base);
}
.step-title-inactive {
  color: rgba(0, 0, 0, 0.6);
}

.debug {
    padding: 1% 10%;
    background: lightgray;
    white-space: pre-wrap;
}

</style>
