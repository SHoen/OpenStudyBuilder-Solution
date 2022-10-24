<template>
<base-template-form
  object-type="objective"
  :template="template"
  :load-form-function="loadForm"
  :prepare-payload-function="preparePayload"
  :help-items="helpItems"
  v-bind="$attrs"
  v-on="$listeners"
  >
  <template v-slot:indexingTab="{ form }">
    <objective-template-indexing-form
      ref="indexingForm"
      :form="form"
      :template="template"
      />
  </template>
</base-template-form>
</template>

<script>
import BaseTemplateForm from './BaseTemplateForm'
import ObjectiveTemplateIndexingForm from './ObjectiveTemplateIndexingForm'

export default {
  components: {
    BaseTemplateForm,
    ObjectiveTemplateIndexingForm
  },
  props: {
    template: Object
  },
  data () {
    return {
      helpItems: [
        'ObjectiveTemplateForm.objective_category',
        'ObjectiveTemplateForm.confirmatory_testing'
      ]
    }
  },
  methods: {
    loadForm (form) {
      form.confirmatoryTesting = this.template ? this.template.confirmatoryTesting : null
      if (this.template.categories && this.template.categories.length) {
        this.$set(form, 'categories', this.template.categories)
      }
    },
    preparePayload (payload) {
      Object.assign(payload, this.$refs.indexingForm.preparePayload(payload))
    }
  }
}
</script>
