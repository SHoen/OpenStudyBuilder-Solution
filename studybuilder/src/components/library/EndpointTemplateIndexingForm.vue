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
            data-cy="template-endpoint-category"
            :items="endpointCategories"
            item-text="sponsor_preferred_name"
            item-value="term_uid"
            :disabled="notApplicable"
            :errors="errors"
            />
        </validation-provider>
      </template>
    </not-applicable-field>
    <not-applicable-field
      :checked="template && !template.sub_categories"
      :clean-function="value => $set(form, 'sub_categories', null)"
      >
      <template v-slot:mainField="{ notApplicable }">
        <validation-provider
          v-slot="{ errors }"
          name="subCategories"
          :rules="`requiredIfNotNA:${notApplicable}`"
          >
          <multiple-select
            v-model="form.sub_categories"
            :label="$t('EndpointTemplateForm.endpoint_sub_category')"
            data-cy="template-endpoint-sub-category"
            :items="endpointSubCategories"
            item-text="sponsor_preferred_name"
            item-value="term_uid"
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
        category_uids: [],
        sub_category_uids: []
      }
      if (form.categories) {
        for (const category of form.categories) {
          if (typeof category === 'string') {
            result.category_uids.push(category)
          } else {
            result.category_uids.push(category.term_uid)
          }
        }
      }
      if (form.sub_categories) {
        for (const subcategory of form.sub_categories) {
          if (typeof subcategory === 'string') {
            result.sub_category_uids.push(subcategory)
          } else {
            result.sub_category_uids.push(subcategory.term_uid)
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
