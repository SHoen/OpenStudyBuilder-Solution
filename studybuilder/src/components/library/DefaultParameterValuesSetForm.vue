<template>
<simple-form-dialog
  ref="form"
  :title="title"
  @close="close"
  @submit="submit"
  :open="open"
  maxWidth="1200px"
  >
  <template v-slot:body>
    <parameter-value-selector
      v-if="template"
      v-model="parameters"
      :template="template.name"
      load-parameter-values-from-template
      :with-pin-button="false"
      preview-text=" "
      :edit-mode="setNumber !== undefined"
      />
  </template>
</simple-form-dialog>
</template>

<script>
import { bus } from '@/main'
import instances from '@/utils/instances'
import { objectManagerMixin } from '@/mixins/objectManager'
import ParameterValueSelector from '@/components/tools/ParameterValueSelector'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog'
import templatesApi from '@/api/templates'

export default {
  mixins: [objectManagerMixin], // FIXME: We include this mixin because of default parameter values. Should we split it?
  components: {
    ParameterValueSelector,
    SimpleFormDialog
  },
  props: {
    template: Object,
    objectType: String,
    setNumber: {
      type: String,
      required: false
    },
    valuesSet: {
      type: Array,
      required: false
    },
    open: Boolean
  },
  computed: {
    title () {
      if (this.setNumber) {
        return this.$t('DefaultParameterValuesSetForm.edit_title')
      }
      return this.$t('DefaultParameterValuesSetForm.add_title')
    }
  },
  data () {
    return {
      parameters: []
    }
  },
  methods: {
    close () {
      this.parameters = []
      this.$emit('close')
    },
    async submit () {
      const defaultDefaultParameterValues = await instances.formatParameterValues(this.parameters, true)
      if (this.setNumber) {
        await this.apiTemplateEndpoint.editDefaultParameterValuesSet(this.template.uid, this.setNumber, defaultDefaultParameterValues)
        bus.$emit('notification', { msg: this.$t('DefaultParameterValuesSetForm.edit_success'), type: 'success' })
      } else {
        await this.apiTemplateEndpoint.addDefaultParameterValuesSet(this.template.uid, defaultDefaultParameterValues)
        bus.$emit('notification', { msg: this.$t('DefaultParameterValuesSetForm.add_success'), type: 'success' })
      }
      this.close()
    },
    loadParameters (template) {
      const templateCopy = { ...template }
      templateCopy.defaultParameterValues = this.valuesSet
      this.showParametersFromTemplate(templateCopy, true)
    }
  },
  created () {
    this.apiTemplateEndpoint = templatesApi(`/${this.objectType}-templates`)
  },
  mounted () {
    this.loadParameters(this.template)
  },
  watch: {
    template (value) {
      if (value) {
        this.loadParameters(value)
      }
    }
  }
}
</script>
