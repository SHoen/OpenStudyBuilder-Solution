<template>
<div class="fullscreen-dialog">
  <horizontal-stepper-form
    ref="stepper"
    :title="title"
    :steps="steps"
    @close="cancel"
    @save="submit"
    :form-observer-getter="getObserver"
    :editable="template !== undefined && template !== null"
    :helpItems="helpItems"
    :extra-step-validation="extraValidation"
    >
    <template v-slot:step.template="{ step }">
      <v-row>
        <v-col cols="11">
          <validation-observer :ref="`observer_${step}`">
            <validation-provider
              v-slot="{ errors }"
              name="Name"
              vid="name"
              rules="required"
              >
              <n-n-template-input-field
                v-model="form.name"
                :items="parameterTypes"
                :error-messages="errors"
                :show-drop-down-early="true"
                :label="$t(`${translationKey}TemplateForm.name`)"
                ></n-n-template-input-field>
            </validation-provider>
          </validation-observer>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="11">
         <p class="grey--text text-subtitle-1 font-weight-bold">{{ $t('_global.plain_text_version') }}</p>
          <div class="pa-4 parameterBackground">
            {{ namePlainPreview }}
          </div>
        </v-col>
      </v-row>
      <slot name="extraFields" :form="form"></slot>
    </template>
    <template v-slot:step.template.actions.middle>
      <v-btn
        class="secondary-btn ml-2"
        color="white"
        @click="verifySyntax"
        >
        {{ $t('_global.verify_syntax') }}
      </v-btn>
    </template>
    <template v-slot:step.testTemplate>
      <parameter-value-selector
        v-model="parameters"
        :template="form.name"
        load-parameter-values-from-template
        preview-text=" "
        :edit-mode="template !== undefined && template !== null"
        />
    </template>
    <template v-slot:step.properties="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <slot name="indexingTab" v-bind:form="form"></slot>
      </validation-observer>
    </template>
    <template v-slot:step.change="{ step }">
      <validation-observer :ref="`observer_${step}`">
        <validation-provider
          v-slot="{ errors }"
          name="ChangeDescription"
          rules="required"
          >
          <v-textarea
            v-model="form.changeDescription"
            :label="$t('HistoryTable.change_description')"
            :error-messages="errors"
            :rows="1"
            dense
            clearable
            auto-grow
            class="white pa-5"
            ></v-textarea>
        </validation-provider>
      </validation-observer>
    </template>
  </horizontal-stepper-form>
  <confirm-dialog ref="confirm" :text-cols="6" :action-cols="5" />
</div>
</template>

<script>
import _isEqual from 'lodash/isEqual'
import { bus } from '@/main'
import ConfirmDialog from '@/components/tools/ConfirmDialog'
import HorizontalStepperForm from '@/components/tools/HorizontalStepperForm'
import instances from '@/utils/instances'
import NNTemplateInputField from '@/components/tools/NNTemplateInputField'
import { objectManagerMixin } from '@/mixins/objectManager'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector'
import statuses from '@/constants/statuses'
import templateParameterTypes from '@/api/templateParameterTypes'
import templatesApi from '@/api/templates'

export default {
  mixins: [objectManagerMixin], // FIXME: We include this mixin because of default parameter values. Should we split it?
  components: {
    ConfirmDialog,
    HorizontalStepperForm,
    NNTemplateInputField,
    ParameterValueSelector
  },
  props: {
    objectType: String,
    template: Object,
    loadFormFunction: {
      type: Function,
      required: false
    },
    preparePayloadFunction: {
      type: Function,
      required: false
    },
    helpItems: {
      type: Array,
      required: false
    },
    titleContext: {
      type: Object,
      required: false
    }
  },
  computed: {
    translationKey () {
      const parts = this.objectType.split('-')
      return parts.map(part => part.charAt(0).toUpperCase() + part.slice(1)).join('')
    },
    title () {
      const context = this.titleContext ? this.titleContext : {}
      return this.template
        ? this.$t(`${this.translationKey}TemplateForm.edit_title`, context)
        : this.$t(`${this.translationKey}TemplateForm.add_title`, context)
    },
    namePlainPreview () {
      if (this.form.name) {
        const result = new DOMParser().parseFromString(this.form.name, 'text/html')
        return result.documentElement.textContent || ''
      }
      return ''
    }
  },
  data () {
    return {
      apiTemplateEndpoint: null,
      form: {},
      originalForm: {},
      parameters: [],
      parameterTypes: [],
      steps: [],
      createModeSteps: [
        { name: 'template', title: this.$t('GenericTemplateForm.step1_add_title') },
        { name: 'testTemplate', title: this.$t('GenericTemplateForm.step2_title') },
        { name: 'properties', title: this.$t('GenericTemplateForm.step3_title') }
      ],
      editModeSteps: [
        { name: 'template', title: this.$t('GenericTemplateForm.step1_edit_title') },
        { name: 'properties', title: this.$t('GenericTemplateForm.step3_title') },
        { name: 'change', title: this.$t('GenericTemplateForm.step4_title') }
      ]
    }
  },
  created () {
    this.apiTemplateEndpoint = templatesApi(`/${this.objectType}-templates`)
    this.steps = this.createModeSteps
    templateParameterTypes.getTypes().then(resp => {
      this.parameterTypes = resp.data
    })
  },
  methods: {
    close () {
      this.form = {}
      this.$refs.stepper.reset()
      this.steps = this.createModeSteps
      this.parameters = []
      this.$emit('close')
    },
    closeWithNoChange () {
      this.close()
      bus.$emit('notification', { type: 'info', msg: this.$t('_global.no_changes') })
    },
    async cancel () {
      if (!_isEqual(this.form, this.originalForm)) {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue')
        }
        if (await this.$refs.confirm.open(this.$t('_global.cancel_changes'), options)) {
          this.close()
        }
      } else {
        this.closeWithNoChange()
      }
    },
    getObserver (step) {
      return this.$refs[`observer_${step}`]
    },
    /**
     * Do a step by step loading of the form using the given template because we don't want to include every fields.
     */
    loadFormFromTemplate () {
      this.form = {
        name: this.template ? this.template.name : null,
        library: this.template ? this.template.library : { name: 'Sponsor' },
        indications: this.template ? this.template.indications : null
      }
      if (this.template.status === statuses.DRAFT) {
        this.$set(this.form, 'changeDescription', this.$t('_global.work_in_progress'))
      }
      if (this.loadFormFunction) {
        this.loadFormFunction(this.form)
      }
      this.originalForm = { ...this.form }
    },
    async preparePayload (data) {
      if (data.indications && data.indications.length > 0) {
        if (this.template !== null && _isEqual(data.indications, this.template.indications)) {
          data.indicationUids = data.indications.map(item => item.termUid)
        } else {
          data.indicationUids = data.indications.map(item => item.termUid)
        }
      }
      if (this.preparePayloadFunction) {
        this.preparePayloadFunction(data)
      }
      const defaultParameterValues = await instances.formatParameterValues(this.parameters, true)
      if (defaultParameterValues.length) {
        data.defaultParameterValues = defaultParameterValues
      } else {
        data.defaultParameterValues = []
      }
    },
    async addTemplate () {
      const data = { ...this.form }

      await this.preparePayload(data)
      try {
        return this.apiTemplateEndpoint.create(data).then(resp => {
          this.$emit('templateAdded')
          bus.$emit('notification', { msg: this.$t(`${this.translationKey}TemplateForm.add_success`) })
          this.close()
        })
      } finally {
        this.$refs.stepper.loading = false
      }
    },
    async updateTemplate () {
      const data = { ...this.form }

      try {
        let template
        if (this.template.name !== data.name) {
          const resp = await this.apiTemplateEndpoint.update(this.template.uid, data)
          template = resp.data
        }
        await this.preparePayload(data)
        const resp = await this.apiTemplateEndpoint.updateGroupings(this.template.uid, data)
        if (!template) {
          template = resp.data
        }
        this.$emit('templateUpdated', template)
        bus.$emit('notification', { msg: this.$t(`${this.translationKey}TemplateForm.update_success`) })
        this.close()
      } finally {
        this.$refs.stepper.loading = false
      }
    },
    verifySyntax () {
      if (!this.form.name) {
        return
      }
      const data = { name: this.form.name }
      this.apiTemplateEndpoint.preValidate(data).then(resp => {
        bus.$emit(
          'notification',
          { msg: this.$t('_global.valid_syntax') })
      })
    },
    async extraValidation (step) {
      if (step !== 1) {
        return true
      }
      try {
        await this.apiTemplateEndpoint.preValidate({ name: this.form.name })
      } catch {
        return false
      }
      return true
    },
    async submit () {
      if (_isEqual(this.form, this.originalForm)) {
        this.closeWithNoChange()
      }
      if (!this.template) {
        this.addTemplate()
      } else {
        this.updateTemplate()
      }
    }
  },
  mounted () {
    if (this.template) {
      this.loadFormFromTemplate()
      this.steps = this.editModeSteps
    }
  }
}
</script>
