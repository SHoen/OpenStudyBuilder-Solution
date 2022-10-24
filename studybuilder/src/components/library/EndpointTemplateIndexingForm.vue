<template>
<template-indexing-form
  :form="form"
  :template="template"
  >
  <template v-slot:templateIndexFields>
    <not-applicable-field
      :checked="template && !template.categories"
      :clean-function="value => $set(form, 'categories', null)"
      >
      <template v-slot:mainField="{ notApplicable }">
        <validation-provider
          v-slot="{ errors }"
          name="categories"
          :rules="`requiredIfNotNA:${notApplicable}`"
          >
          <multiple-select
            v-model="form.categories"
            :label="$t('EndpointTemplateForm.endpoint_category')"
            :items="endpointCategories"
            item-text="sponsorPreferredName"
            item-value="termUid"
            :disabled="notApplicable"
            :errors="errors"
            />
        </validation-provider>
      </template>
    </not-applicable-field>
    <not-applicable-field
      :checked="template && !template.subCategories"
      :clean-function="value => $set(form, 'subCategories', null)"
      >
      <template v-slot:mainField="{ notApplicable }">
        <validation-provider
          v-slot="{ errors }"
          name="subCategories"
          :rules="`requiredIfNotNA:${notApplicable}`"
          >
          <multiple-select
            v-model="form.subCategories"
            :label="$t('EndpointTemplateForm.endpoint_sub_category')"
            :items="endpointSubCategories"
            item-text="sponsorPreferredName"
            item-value="termUid"
            :disabled="notApplicable"
            :errors="errors"
            />
        </validation-provider>
      </template>
    </not-applicable-field>
  </template>
</template-indexing-form>
</template>

<script>
import MultipleSelect from '@/components/tools/MultipleSelect'
import NotApplicableField from '@/components/tools/NotApplicableField'
import TemplateIndexingForm from './TemplateIndexingForm'
import terms from '@/api/controlledTerminology/terms'

export default {
  components: {
    MultipleSelect,
    NotApplicableField,
    TemplateIndexingForm
  },
  props: {
    form: Object,
    template: Object
  },
  data () {
    return {
      endpointCategories: [],
      endpointSubCategories: []
    }
  },
  methods: {
    preparePayload (form) {
      const result = {
        categoryUids: [],
        subCategoryUids: []
      }
      if (form.categories) {
        for (const category of form.categories) {
          if (typeof category === 'string') {
            result.categoryUids.push(category)
          } else {
            result.categoryUids.push(category.termUid)
          }
        }
      }
      if (form.subCategories) {
        for (const subcategory of form.subCategories) {
          if (typeof subcategory === 'string') {
            result.subCategoryUids.push(subcategory)
          } else {
            result.subCategoryUids.push(subcategory.termUid)
          }
        }
      }
      return result
    }
  },
  mounted () {
    terms.getByCodelist('endpointCategories').then(resp => {
      this.endpointCategories = resp.data.items
    })
    terms.getByCodelist('endpointSubCategories').then(resp => {
      this.endpointSubCategories = resp.data.items
    })
  }
}
</script>
