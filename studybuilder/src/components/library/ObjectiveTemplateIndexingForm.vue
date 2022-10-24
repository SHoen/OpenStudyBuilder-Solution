<template>
<template-indexing-form
  :form="form"
  :template="template"
  >
  <template v-slot:templateIndexFields>
    <not-applicable-field
      :checked="template && !template.categories"
      :clean-function="(value) => cleanObjectiveCategories(form, value)"
      >
      <template v-slot:mainField="{ notApplicable }">
        <validation-provider
          v-slot="{ errors }"
          name="categories"
          :rules="`requiredIfNotNA:${notApplicable}`"
          >
          <multiple-select
            v-model="form.categories"
            :label="$t('ObjectiveTemplateForm.objective_category')"
            :items="objectiveCategories"
            item-text="sponsorPreferredName"
            item-value="termUid"
            :disabled="notApplicable"
            :errors="errors"
            />
        </validation-provider>
      </template>
    </not-applicable-field>
    <not-applicable-field
      :checked="template && (template.confirmatoryTesting === null || template.confirmatoryTesting === undefined)"
      :clean-function="(value) => cleanConfirmatoryTesting(form, value)"
      >
      <template v-slot:mainField="{ notApplicable }">
        <validation-provider
          v-slot="{ errors }"
          name="confirmatoryTesting"
          :rules="`requiredIfNotNA:${notApplicable}`"
          >
          <yes-no-field
            v-model="form.confirmatoryTesting"
            :label="$t('ObjectiveTemplateForm.confirmatory_testing')"
            :disabled="notApplicable"
            :error-messages="errors"
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
import YesNoField from '@/components/tools/YesNoField'

export default {
  components: {
    MultipleSelect,
    NotApplicableField,
    TemplateIndexingForm,
    YesNoField
  },
  props: {
    form: Object,
    template: Object
  },
  data () {
    return {
      objectiveCategories: []
    }
  },
  methods: {
    cleanObjectiveCategories (form, value) {
      if (value) {
        this.$set(form, 'categories', [])
      }
    },
    cleanConfirmatoryTesting (form, value) {
      if (value) {
        this.$set(form, 'confirmatoryTesting', null)
      }
    },
    preparePayload (form) {
      const result = {
        confirmatoryTesting: form.confirmatoryTesting,
        categoryUids: []
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
      return result
    }
  },
  mounted () {
    terms.getByCodelist('objectiveCategories').then(resp => {
      this.objectiveCategories = resp.data.items
    })
  }
}
</script>
