<template>
<base-template-form
  object-type="criteria"
  :template="template"
  :load-form-function="loadForm"
  :prepare-payload-function="preparePayload"
  :help-items="helpItems"
  :title-context="{ type }"
  v-bind="$attrs"
  v-on="$listeners"
  >
  <template v-slot:extraFields="{ form }">
    <validation-observer ref="observer">
      <v-row>
        <v-col cols="11">
          <vue-editor
            ref="editor"
            id="editor"
            v-model="form.guidanceText"
            :editor-toolbar="customToolbar"
            :placeholder="$t('CriteriaTemplateForm.guidance_text')"
            class="pt-4"
            />
        </v-col>
      </v-row>
    </validation-observer>
  </template>
  <template v-slot:indexingTab="{ form }">
    <criteria-template-indexing-form
      ref="indexingForm"
      :form="form"
      :template="template"
      />
  </template>
</base-template-form>
</template>

<script>
import BaseTemplateForm from './BaseTemplateForm'
import CriteriaTemplateIndexingForm from './CriteriaTemplateIndexingForm'
import terms from '@/api/controlledTerminology/terms'
import { VueEditor } from 'vue2-editor'

export default {
  components: {
    BaseTemplateForm,
    CriteriaTemplateIndexingForm,
    VueEditor
  },
  props: {
    template: Object,
    type: String
  },
  data () {
    return {
      customToolbar: [
        ['bold', 'italic', 'underline'],
        [{ script: 'sub' }, { script: 'super' }],
        [{ list: 'ordered' }, { list: 'bullet' }]
      ],
      helpItems: [
        'CriteriaTemplateForm.guidance_text',
        'CriteriaTemplateForm.indication',
        'CriteriaTemplateForm.criterion_cat',
        'CriteriaTemplateForm.criterion_sub_cat'
      ],
      types: [],
      typeUid: ''
    }
  },
  methods: {
    loadForm (form) {
      form.guidanceText = this.template.guidanceText
      if (this.template.categories && this.template.categories.length) {
        this.$set(form, 'categories', this.template.categories)
      }
      if (this.template.subCategories && this.template.subCategories.length) {
        this.$set(form, 'subCategories', this.template.subCategories)
      }
      this.$store.commit('form/SET_FORM', form)
    },
    preparePayload (payload) {
      payload.typeUid = this.typeUid
      Object.assign(payload, this.$refs.indexingForm.preparePayload(payload))
    }
  },
  mounted () {
    terms.getByCodelist('criteriaTypes').then(resp => {
      this.types = resp.data.items
      this.typeUid = this.types.find(item => item.sponsorPreferredName.toLowerCase().startsWith(this.type)).termUid
    })
  }
}
</script>
