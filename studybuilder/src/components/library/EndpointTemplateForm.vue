<template>
<base-template-form
  object-type="endpoint"
  :template="template"
  :load-form-function="loadForm"
  :prepare-payload-function="preparePayload"
  :help-items="helpItems"
  v-bind="$attrs"
  v-on="$listeners"
  >
  <template v-slot:indexingTab="{ form }">
    <endpoint-template-indexing-form
      ref="indexingForm"
      :form="form"
      :template="template"
      />
  </template>
</base-template-form>
</template>

<script>
import BaseTemplateForm from './BaseTemplateForm'
import EndpointTemplateIndexingForm from './EndpointTemplateIndexingForm'

export default {
  props: {
    template: Object
  },
  components: {
    BaseTemplateForm,
    EndpointTemplateIndexingForm
  },
  data () {
    return {
      helpItems: [
        'EndpointTemplateForm.endpoint_category',
        'EndpointTemplateForm.endpoint_sub_category'
      ]
    }
  },
  methods: {
    loadForm (form) {
      if (this.template.categories && this.template.categories.length) {
        form.categories = this.template.categories
      }
      if (this.template.subCategories && this.template.subCategories.length) {
        form.subCategories = this.template.subCategories
      }
      this.$store.commit('form/SET_FORM', form)
    },
    preparePayload (payload) {
      Object.assign(payload, this.$refs.indexingForm.preparePayload(payload))
    }
  }
}
</script>
